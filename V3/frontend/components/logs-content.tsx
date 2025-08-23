"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { LogConsole } from "@/components/log-console"
import { ApiStatus } from "@/components/api-status"
import { useHealth } from "@/lib/api"
import { FileText, Activity } from "lucide-react"

export function LogsContent() {
  const { data: health } = useHealth()
  const isOnline = health?.ok && !health.error

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <Card className="glass-panel">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="font-heading text-xl flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Log Monitor
            </CardTitle>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Activity className="h-4 w-4" />
                <span>Auto-refresh: 1s</span>
              </div>
              <ApiStatus />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">
            {isOnline
              ? "Connected to backend. Logs are streaming in real-time."
              : "Backend offline. Showing cached log data."}
          </div>
        </CardContent>
      </Card>

      {/* Log Console */}
      <Card className="glass-panel">
        <CardContent className="pt-6">
          <LogConsole />
        </CardContent>
      </Card>
    </div>
  )
}
