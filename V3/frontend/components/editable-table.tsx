"use client"

import { useState } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { KeybindBadge } from "./keybind-badge"
import { Check, X, Edit } from "lucide-react"

interface EditableTableProps {
  data: Array<{
    id: string
    action: string
    type: "keyboard" | "mouse"
    keys: string[]
    hold_ms: number
  }>
  onUpdate: (id: string, field: string, value: any) => void
  onTest?: (id: string) => void
}

export function EditableTable({ data, onUpdate, onTest }: EditableTableProps) {
  const [editingCell, setEditingCell] = useState<string | null>(null)
  const [editValue, setEditValue] = useState<string>("")

  const startEdit = (cellId: string, currentValue: any) => {
    setEditingCell(cellId)
    setEditValue(Array.isArray(currentValue) ? currentValue.join(", ") : currentValue.toString())
  }

  const saveEdit = (id: string, field: string) => {
    let value: any = editValue
    if (field === "keys") {
      value = editValue
        .split(",")
        .map((k) => k.trim())
        .filter((k) => k)
    } else if (field === "hold_ms") {
      value = Number.parseInt(editValue) || 0
    }
    onUpdate(id, field, value)
    setEditingCell(null)
  }

  const cancelEdit = () => {
    setEditingCell(null)
    setEditValue("")
  }

  return (
    <div className="rounded-lg border border-border overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead>Action</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Keys/Buttons</TableHead>
            <TableHead>Hold (ms)</TableHead>
            <TableHead className="w-20">Test</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((row) => (
            <TableRow key={row.id} className="hover:bg-muted/30">
              <TableCell className="font-medium">{row.action}</TableCell>
              <TableCell>
                <span className="capitalize text-muted-foreground">{row.type}</span>
              </TableCell>
              <TableCell>
                {editingCell === `${row.id}-keys` ? (
                  <div className="flex items-center gap-2">
                    <Input
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="h-8"
                      placeholder="space, ctrl, a"
                    />
                    <Button size="sm" variant="ghost" onClick={() => saveEdit(row.id, "keys")}>
                      <Check className="h-3 w-3" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={cancelEdit}>
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div
                    className="flex items-center gap-2 cursor-pointer hover:bg-muted/50 p-1 rounded"
                    onClick={() => startEdit(`${row.id}-keys`, row.keys)}
                  >
                    <KeybindBadge keys={row.keys} />
                    <Edit className="h-3 w-3 opacity-50" />
                  </div>
                )}
              </TableCell>
              <TableCell>
                {editingCell === `${row.id}-hold_ms` ? (
                  <div className="flex items-center gap-2">
                    <Input
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      className="h-8 w-20"
                      type="number"
                    />
                    <Button size="sm" variant="ghost" onClick={() => saveEdit(row.id, "hold_ms")}>
                      <Check className="h-3 w-3" />
                    </Button>
                    <Button size="sm" variant="ghost" onClick={cancelEdit}>
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div
                    className="flex items-center gap-2 cursor-pointer hover:bg-muted/50 p-1 rounded font-mono"
                    onClick={() => startEdit(`${row.id}-hold_ms`, row.hold_ms)}
                  >
                    {row.hold_ms}
                    <Edit className="h-3 w-3 opacity-50" />
                  </div>
                )}
              </TableCell>
              <TableCell>
                {onTest && (
                  <Button size="sm" variant="outline" onClick={() => onTest(row.id)} className="h-8">
                    Test
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
