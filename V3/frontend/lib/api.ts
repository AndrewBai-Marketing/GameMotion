// frontend/lib/api.ts
import useSWR from "swr";

const API_BASE =
  process.env.NEXT_PUBLIC_API?.replace(/\/$/, "") || "http://127.0.0.1:8000";

async function jfetch<T = any>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()) as T;
}

export const fetcher = (path: string) => jfetch(path);

// ---- Hooks the UI expects ----
export const useHealth = () =>
  useSWR<{ ok: boolean; version: string }>("/health", fetcher, {
    refreshInterval: 3000,
  });

export const useRuntime = () =>
  useSWR<{ active_exe: string | null; active_profile: any | null }>(
    "/runtime",
    fetcher,
    { refreshInterval: 1000 }
  );

export const useSettings = () =>
  useSWR<Record<string, any>>("/settings", fetcher, {
    refreshInterval: 5000,
  });

export const useProfiles = () =>
  useSWR<string[]>("/profiles", fetcher, { refreshInterval: 5000 });

export const useLogs = (tail = 300) =>
  useSWR<{ lines: string[] }>(`/logs?tail=${tail}`, fetcher, {
    refreshInterval: 1000,
  });

// ---- Mutations the UI expects ----
export async function startDetection() {
  await jfetch("/detect/start", { method: "POST" });
}

export async function stopDetection() {
  await jfetch("/detect/stop", { method: "POST" });
}

export async function startTraining(params: {
  game: string;
  action: string;
  samples: number;
  preview?: boolean;
}) {
  await jfetch("/train/start", {
    method: "POST",
    body: JSON.stringify(params),
  });
}

export async function saveProfile(exe_name: string, profile: any) {
  await jfetch(`/profiles/${encodeURIComponent(exe_name)}`, {
    method: "POST",
    body: JSON.stringify(profile),
  });
}

export async function getProfile(exe_name: string) {
  return await jfetch<any>(`/profiles/${encodeURIComponent(exe_name)}`);
}

export { API_BASE };
