"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { HelpCircle, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import Image from "next/image"
import { useState } from "react"
import { TutorialModal } from "./tutorial-modal" // Fixed import to use named export instead of default export

const navigation = [
  { name: "Dashboard", href: "/" },
  { name: "Training", href: "/training" },
  { name: "Profiles", href: "/profiles" },
  { name: "Settings", href: "/settings" },
  { name: "Logs", href: "/logs" },
]

export function GlobalHeader() {
  const pathname = usePathname()
  const [showTutorial, setShowTutorial] = useState(false) // Added state to control tutorial modal visibility

  return (
    <>
      <header className="sticky top-0 z-50 w-full border-b border-border/40 glass-panel">
        <div className="container flex h-16 max-w-screen-2xl items-center justify-between px-6">
          <Link href="/" className="flex items-center space-x-3">
            <Image src="/gamemotion-logo.png" alt="GameMotion" width={32} height={32} className="rounded-lg" />
            <span className="font-semibold text-xl text-foreground">GameMotion</span>
            <span className="text-xs bg-muted text-muted-foreground px-2 py-1 rounded-full font-medium">v2.1</span>
          </Link>

          <nav className="flex items-center gap-6 text-sm">
            {navigation.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "transition-all duration-200 px-4 py-2 rounded-lg font-medium",
                  pathname === item.href
                    ? "text-primary font-semibold bg-primary/10 shadow-sm"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50 hover:shadow-sm",
                )}
              >
                {item.name}
              </Link>
            ))}
          </nav>

          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
              <FileText className="h-4 w-4 mr-2" />
              Docs
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-foreground"
              onClick={() => setShowTutorial(true)}
            >
              <HelpCircle className="h-4 w-4 mr-2" />
              Help
            </Button>
          </div>
        </div>
      </header>

      {showTutorial && <TutorialModal forceOpen={true} onClose={() => setShowTutorial(false)} />}
    </>
  )
}
