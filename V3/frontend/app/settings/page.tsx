import { GlobalHeader } from "@/components/global-header"
import { SettingsContent } from "@/components/settings-content"

export default function SettingsPage() {
  return (
    <div className="min-h-screen">
      <GlobalHeader />
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="font-heading text-3xl font-bold">Settings</h1>
            <p className="text-muted-foreground">
              Configure detection and training parameters to optimize GameMotion performance.
            </p>
          </div>
          <SettingsContent />
        </div>
      </main>
    </div>
  )
}
