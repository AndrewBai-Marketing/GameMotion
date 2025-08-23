// frontend/components/camera-preview.tsx
"use client";

import { useEffect, useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { API_BASE } from "@/lib/api";

export function CameraPreview() {
  const [tick, setTick] = useState(0);
  const [online, setOnline] = useState(true);

  // cache-bust the jpeg every 500ms
  useEffect(() => {
    const id = setInterval(() => setTick((t) => (t + 1) % 100000), 500);
    return () => clearInterval(id);
  }, []);

  const src = `${API_BASE}/preview.jpg?ts=${Date.now()}&r=${tick}`;

  return (
    <Card className="bg-muted/10">
      <CardContent className="p-4">
        <div className="relative aspect-video w-full bg-black rounded-md overflow-hidden">
          <img
            alt="Camera preview"
            src={src}
            className="w-full h-full object-cover"
            onError={() => setOnline(false)}
            onLoad={() => setOnline(true)}
          />
          {!online && (
            <span className="absolute right-2 top-2 text-xs rounded bg-gray-700/80 px-2 py-1">
              Offline
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
