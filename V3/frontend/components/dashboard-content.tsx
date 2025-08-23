// frontend/components/dashboard-content.tsx
"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import {
  useHealth,
  useRuntime,
  startDetection,
  stopDetection,
} from "@/lib/api";
import { CameraPreview } from "@/components/camera-preview";
import { Button } from "@/components/ui/button";

export function DashboardContent() {
  const { data: runtime } = useRuntime();
  const { data: health } = useHealth();
  const [busy, setBusy] = useState(false);

  const onStart = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await startDetection();
    } finally {
      setBusy(false);
    }
  };
  const onStop = async () => {
    if (busy) return;
    setBusy(true);
    try {
      await stopDetection();
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <CardContent className="p-6 space-y-4">
          <div className="text-2xl font-semibold">
            {runtime?.active_exe || "—"}
          </div>
          <div className="text-sm text-muted-foreground">
            Profile: {runtime?.active_profile?.display_name || "None"}
          </div>

          <div className="flex gap-3 pt-2">
            <Button onClick={onStart} disabled={busy}>
              ▶ Start Detection
            </Button>
            <Button variant="secondary" onClick={onStop} disabled={busy}>
              ⏹ Stop Detection
            </Button>
          </div>

          <div className="text-xs text-muted-foreground pt-2">
            Backend: {health?.ok ? "online" : "offline"}
          </div>
        </CardContent>
      </Card>

      <CameraPreview />
    </div>
  );
}
