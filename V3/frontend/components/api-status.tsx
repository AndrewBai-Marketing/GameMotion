"use client"

import { useHealth } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { Circle } from "lucide-react"

export function ApiStatus() {
  const { data: health, error } = useHealth()

  const isOnline = health?.ok && !error

  return (
    <Badge
      variant={isOnline ? "default" : "secondary"}
      className={`flex items-center gap-2 ${isOnline ? "bg-primary text-primary-foreground neon-glow" : ""}`}
    >
      <Circle className={`h-2 w-2 fill-current ${isOnline ? "animate-pulse" : ""}`} />
      {isOnline ? "Online" : "Offline"}
    </Badge>
  )
}
