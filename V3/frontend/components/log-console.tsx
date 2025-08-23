"use client"

import { useEffect, useRef, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Copy, Trash2, Search } from "lucide-react"
import { useLogs } from "@/lib/api"

type LogLevel = "INFO" | "WARN" | "ERROR" | "DEBUG"

export function LogConsole() {
  const { data: logs } = useLogs()
  const [filter, setFilter] = useState<LogLevel | "ALL">("ALL")
  const [search, setSearch] = useState("")
  const scrollRef = useRef<HTMLDivElement>(null)

  const filteredLines =
    logs?.lines?.filter((line) => {
      const matchesFilter = filter === "ALL" || line.includes(`[${filter}]`)
      const matchesSearch = search === "" || line.toLowerCase().includes(search.toLowerCase())
      return matchesFilter && matchesSearch
    }) || []

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [filteredLines])

  const copyLogs = () => {
    navigator.clipboard.writeText(filteredLines.join("\n"))
  }

  const clearLogs = () => {
    // In a real app, this would call an API to clear logs
    console.log("Clear logs requested")
  }

  const getLogLevelColor = (line: string): string => {
    if (line.includes("[ERROR]")) return "text-destructive"
    if (line.includes("[WARN]")) return "text-yellow-500"
    if (line.includes("[INFO]")) return "text-primary"
    if (line.includes("[DEBUG]")) return "text-muted-foreground"
    return "text-foreground"
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-2">
          <Search className="h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search logs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-48"
          />
        </div>

        <div className="flex gap-1">
          {(["ALL", "INFO", "WARN", "ERROR", "DEBUG"] as const).map((level) => (
            <Badge
              key={level}
              variant={filter === level ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilter(level)}
            >
              {level}
            </Badge>
          ))}
        </div>

        <div className="flex gap-2 ml-auto">
          <Button size="sm" variant="outline" onClick={copyLogs}>
            <Copy className="h-4 w-4 mr-2" />
            Copy
          </Button>
          <Button size="sm" variant="outline" onClick={clearLogs}>
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="h-96 overflow-y-auto bg-card border border-border rounded-lg p-4 font-mono text-sm space-y-1"
      >
        {filteredLines.map((line, index) => (
          <div key={index} className={`${getLogLevelColor(line)} hover:bg-muted/30 px-2 py-1 rounded`}>
            {line}
          </div>
        ))}
        {filteredLines.length === 0 && (
          <div className="text-muted-foreground text-center py-8">No logs match the current filter</div>
        )}
      </div>
    </div>
  )
}
