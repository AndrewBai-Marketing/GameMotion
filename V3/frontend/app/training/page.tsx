import { GlobalHeader } from "@/components/global-header"
import { TrainingContent } from "@/components/training-content"

export default function TrainingPage() {
  return (
    <div className="min-h-screen">
      <GlobalHeader />
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          <div className="space-y-2">
            <h1 className="font-heading text-3xl font-bold">Motion Training</h1>
            <p className="text-muted-foreground">
              Train GameMotion to recognize your movements and map them to specific actions.
            </p>
          </div>
          <TrainingContent />
        </div>
      </main>
    </div>
  )
}
