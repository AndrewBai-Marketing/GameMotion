"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { ChevronLeft, ChevronRight, Play, Settings, Users, BarChart3, FileText } from "lucide-react"

const tutorialSteps = [
  {
    title: "Welcome to GameMotion v2.1",
    content: "GameMotion converts your physical movements into keyboard and mouse actions for seamless gaming control.",
    icon: <Play className="h-8 w-8 text-primary" />,
  },
  {
    title: "Dashboard Overview",
    content: "Monitor your system status, view live camera feed, and control detection from the main dashboard.",
    icon: <BarChart3 className="h-8 w-8 text-primary" />,
  },
  {
    title: "Training Your Actions",
    content: "Use the Training page to teach GameMotion your movements. Capture samples and build your action library.",
    icon: <Settings className="h-8 w-8 text-primary" />,
  },
  {
    title: "Managing Profiles",
    content:
      "Create and edit profiles for different games. Map your trained actions to specific keyboard and mouse inputs.",
    icon: <Users className="h-8 w-8 text-primary" />,
  },
  {
    title: "Configuration & Logs",
    content: "Fine-tune detection settings and monitor system logs for optimal performance.",
    icon: <FileText className="h-8 w-8 text-primary" />,
  },
]

interface TutorialModalProps {
  forceOpen?: boolean
  onClose?: () => void
}

export function TutorialModal({ forceOpen = false, onClose }: TutorialModalProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    const hasSeenTutorial = localStorage.getItem("gamemotion-tutorial-seen")
    if (forceOpen || !hasSeenTutorial) {
      setIsOpen(true)
    }
  }, [forceOpen])

  const handleClose = () => {
    localStorage.setItem("gamemotion-tutorial-seen", "true")
    setIsOpen(false)
    setCurrentStep(0) // Reset to first step when closing
    onClose?.() // Call optional onClose callback
  }

  const nextStep = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    } else {
      handleClose()
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const currentTutorial = tutorialSteps[currentStep]

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-heading text-xl">Getting Started</DialogTitle>
        </DialogHeader>

        <Card className="glass-panel">
          <CardContent className="p-6 text-center space-y-4">
            <div className="flex justify-center">{currentTutorial.icon}</div>

            <h3 className="font-heading text-lg font-bold">{currentTutorial.title}</h3>

            <p className="text-muted-foreground">{currentTutorial.content}</p>

            <div className="flex justify-center space-x-2 pt-2">
              {tutorialSteps.map((_, index) => (
                <div
                  key={index}
                  className={`h-2 w-2 rounded-full transition-colors ${
                    index === currentStep ? "bg-primary" : "bg-muted"
                  }`}
                />
              ))}
            </div>
          </CardContent>
        </Card>

        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={prevStep}
            disabled={currentStep === 0}
            className="flex items-center space-x-2 bg-transparent"
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Previous</span>
          </Button>

          <Button onClick={handleClose} variant="ghost">
            Skip Tutorial
          </Button>

          <Button onClick={nextStep} className="gradient-primary flex items-center space-x-2">
            <span>{currentStep === tutorialSteps.length - 1 ? "Get Started" : "Next"}</span>
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
