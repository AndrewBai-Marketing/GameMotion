// frontend/components/training-content.tsx
"use client";

import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useProfiles, startTraining, useLogs } from "@/lib/api";

export function TrainingContent() {
  const { data: profiles } = useProfiles();
  const { data: logs } = useLogs(400);
  const [game, setGame] = useState("");
  const [action, setAction] = useState("");
  const [samples, setSamples] = useState(40);
  const [busy, setBusy] = useState(false);

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      <Card>
        <CardContent className="p-6 space-y-3">
          <div className="text-lg font-semibold">Collect Samples</div>

          <label className="block text-sm">Game EXE</label>
          <input
            className="w-full rounded border bg-background p-2"
            list="exe-names"
            value={game}
            onChange={(e) => setGame(e.target.value)}
            placeholder="e.g., Notepad.exe"
          />
          <datalist id="exe-names">
            {(profiles || []).map((p) => (
              <option key={p} value={p} />
            ))}
          </datalist>

          <label className="block text-sm">Action label</label>
          <input
            className="w-full rounded border bg-background p-2"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            placeholder="e.g., JUMP"
          />

          <label className="block text-sm">Samples</label>
          <input
            type="number"
            className="w-full rounded border bg-background p-2"
            value={samples}
            onChange={(e) => setSamples(Number(e.target.value || 0))}
          />

          <Button
            disabled={!game || !action || busy}
            onClick={async () => {
              setBusy(true);
              try {
                await startTraining({
                  game,
                  action,
                  samples: Math.max(10, samples),
                  preview: true,
                });
              } finally {
                setBusy(false);
              }
            }}
          >
            {busy ? "Starting…" : "Start Training"}
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4">
          <div className="text-sm font-mono whitespace-pre-wrap h-[360px] overflow-auto">
            {(logs?.lines || []).join("\n")}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
