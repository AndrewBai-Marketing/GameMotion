import { GlobalHeader } from "@/components/global-header"
import { ProfilesContent } from "@/components/profiles-content"

export default function ProfilesPage() {
  return (
    <div className="min-h-screen">
      <GlobalHeader />
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="font-heading text-3xl font-bold">Profile Management</h1>
            <p className="text-muted-foreground">Configure action mappings for different games and applications.</p>
          </div>
          <ProfilesContent />
        </div>
      </main>
    </div>
  )
}
