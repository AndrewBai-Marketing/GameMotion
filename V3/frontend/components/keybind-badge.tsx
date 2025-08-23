import { Badge } from "@/components/ui/badge"

interface KeybindBadgeProps {
  keys: string[]
  className?: string
}

export function KeybindBadge({ keys, className = "" }: KeybindBadgeProps) {
  return (
    <div className={`flex flex-wrap gap-1 ${className}`}>
      {keys.map((key, index) => (
        <Badge key={index} variant="outline" className="font-mono text-xs">
          {key}
        </Badge>
      ))}
    </div>
  )
}
