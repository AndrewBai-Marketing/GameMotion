import { GlobalHeader } from "@/components/global-header"
import { DashboardContent } from "@/components/dashboard-content"
import { TutorialModal } from "@/components/tutorial-modal"

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <GlobalHeader />
      <main className="container mx-auto px-4 py-8">
        <DashboardContent />
      </main>
      <TutorialModal />
    </div>
  )
}
