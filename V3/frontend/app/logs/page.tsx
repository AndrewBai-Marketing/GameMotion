import { GlobalHeader } from "@/components/global-header"
import { LogsContent } from "@/components/logs-content"

export default function LogsPage() {
  return (
    <div className="min-h-screen">
      <GlobalHeader />
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="font-heading text-3xl font-bold">System Logs</h1>
            <p className="text-muted-foreground">
              Monitor GameMotion system activity, errors, and debug information in real-time.
            </p>
          </div>
          <LogsContent />
        </div>
      </main>
    </div>
  )
}
