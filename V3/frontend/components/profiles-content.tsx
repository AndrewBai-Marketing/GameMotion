"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { EditableTable } from "@/components/editable-table"
import { useProfiles, useProfile, saveProfile, testAction, useHealth } from "@/lib/api"
import { getStoredValue, setStoredValue, STORAGE_KEYS } from "@/lib/storage"
import { Plus, Trash2, Save, Download, Upload, FileText, CheckCircle, AlertCircle, Gamepad2 } from "lucide-react"

interface ProfileAction {
  id: string
  action: string
  type: "keyboard" | "mouse"
  keys: string[]
  hold_ms: number
}

export function ProfilesContent() {
  const { data: profiles } = useProfiles()
  const { data: health } = useHealth()
  const [selectedProfile, setSelectedProfile] = useState(() => getStoredValue(STORAGE_KEYS.SELECTED_PROFILE, ""))
  const { data: profileData, mutate: mutateProfile } = useProfile(selectedProfile)

  const [actions, setActions] = useState<ProfileAction[]>([])
  const [selectedActionId, setSelectedActionId] = useState<string | null>(null)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle")
  const [newActionName, setNewActionName] = useState("")

  const isOnline = health?.ok && !health.error

  // Load profile data when selected profile changes
  useEffect(() => {
    if (profileData?.actions) {
      const actionsList = Object.entries(profileData.actions).map(([action, config]) => ({
        id: action,
        action,
        type: config.type,
        keys: config.keys,
        hold_ms: config.hold_ms,
      }))
      setActions(actionsList)
      setHasUnsavedChanges(false)
    } else {
      setActions([])
    }
  }, [profileData])

  const handleProfileSelect = (profile: string) => {
    if (hasUnsavedChanges) {
      const confirm = window.confirm("You have unsaved changes. Are you sure you want to switch profiles?")
      if (!confirm) return
    }
    setSelectedProfile(profile)
    setStoredValue(STORAGE_KEYS.SELECTED_PROFILE, profile)
    setHasUnsavedChanges(false)
    setSaveStatus("idle")
  }

  const handleActionUpdate = (id: string, field: string, value: any) => {
    setActions((prev) => prev.map((action) => (action.id === id ? { ...action, [field]: value } : action)))
    setHasUnsavedChanges(true)
    setSaveStatus("idle")
  }

  const handleAddAction = () => {
    if (!newActionName.trim()) return

    const newAction: ProfileAction = {
      id: newActionName.toUpperCase(),
      action: newActionName.toUpperCase(),
      type: "keyboard",
      keys: ["space"],
      hold_ms: 50,
    }

    setActions((prev) => [...prev, newAction])
    setNewActionName("")
    setHasUnsavedChanges(true)
    setSaveStatus("idle")
  }

  const handleDeleteAction = () => {
    if (!selectedActionId) return

    const confirm = window.confirm("Are you sure you want to delete this action?")
    if (!confirm) return

    setActions((prev) => prev.filter((action) => action.id !== selectedActionId))
    setSelectedActionId(null)
    setHasUnsavedChanges(true)
    setSaveStatus("idle")
  }

  const handleSaveProfile = async () => {
    if (!selectedProfile) return

    setSaveStatus("saving")
    try {
      const profileConfig = {
        display_name: selectedProfile.replace(".exe", ""),
        exe_name: selectedProfile,
        actions: actions.reduce(
          (acc, action) => ({
            ...acc,
            [action.action]: {
              type: action.type,
              keys: action.keys,
              hold_ms: action.hold_ms,
            },
          }),
          {},
        ),
      }

      await saveProfile(selectedProfile, profileConfig)
      await mutateProfile()
      setHasUnsavedChanges(false)
      setSaveStatus("saved")
      setTimeout(() => setSaveStatus("idle"), 3000)
    } catch (error) {
      console.error("Failed to save profile:", error)
      setSaveStatus("error")
      setTimeout(() => setSaveStatus("idle"), 3000)
    }
  }

  const handleTestAction = async (actionId: string) => {
    if (!selectedProfile || !isOnline) return

    try {
      await testAction(selectedProfile, actionId)
    } catch (error) {
      console.error("Failed to test action:", error)
    }
  }

  const handleExportProfile = () => {
    if (!profileData) return

    const dataStr = JSON.stringify(profileData, null, 2)
    const dataBlob = new Blob([dataStr], { type: "application/json" })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement("a")
    link.href = url
    link.download = `${selectedProfile.replace(".exe", "")}_profile.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleImportProfile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const imported = JSON.parse(e.target?.result as string)
        if (imported.actions) {
          const actionsList = Object.entries(imported.actions).map(([action, config]: [string, any]) => ({
            id: action,
            action,
            type: config.type,
            keys: config.keys,
            hold_ms: config.hold_ms,
          }))
          setActions(actionsList)
          setHasUnsavedChanges(true)
          setSaveStatus("idle")
        }
      } catch (error) {
        console.error("Failed to import profile:", error)
        alert("Failed to import profile. Please check the file format.")
      }
    }
    reader.readAsText(file)
    event.target.value = ""
  }

  return (
    <div className="space-y-6">
      {/* Profile Selection */}
      <Card className="glass-panel">
        <CardHeader>
          <CardTitle className="font-heading text-xl flex items-center gap-2">
            <Gamepad2 className="h-5 w-5 text-primary" />
            Profile Selection
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <Label className="tracking-normal mx-0 my-2.5" htmlFor="profile-select">Active Profile</Label>
              <Select value={selectedProfile} onValueChange={handleProfileSelect}>
                <SelectTrigger id="profile-select">
                  <SelectValue placeholder="Select a profile..." />
                </SelectTrigger>
                <SelectContent>
                  {profiles?.map((profile) => (
                    <SelectItem key={profile} value={profile}>
                      {profile}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {hasUnsavedChanges && (
              <Badge variant="outline" className="text-yellow-500 border-yellow-500">
                Unsaved Changes
              </Badge>
            )}
          </div>

          {saveStatus !== "idle" && (
            <Alert className={saveStatus === "error" ? "border-destructive" : "border-primary"}>
              {saveStatus === "saved" ? (
                <CheckCircle className="h-4 w-4 text-primary" />
              ) : saveStatus === "error" ? (
                <AlertCircle className="h-4 w-4 text-destructive" />
              ) : null}
              <AlertDescription>
                {saveStatus === "saving" && "Saving profile..."}
                {saveStatus === "saved" && "Profile saved successfully!"}
                {saveStatus === "error" && "Failed to save profile. Please try again."}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Actions Management */}
      {selectedProfile && (
        <Card className="glass-panel">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="font-heading text-xl">Action Mappings</CardTitle>
              <div className="flex items-center gap-2">
                <Button size="sm" variant="outline" onClick={handleExportProfile} disabled={!profileData}>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
                <Button size="sm" variant="outline" asChild>
                  <label className="cursor-pointer">
                    <Upload className="h-4 w-4 mr-2" />
                    Import
                    <input type="file" accept=".json" onChange={handleImportProfile} className="hidden" />
                  </label>
                </Button>
                <Button onClick={handleSaveProfile} disabled={!hasUnsavedChanges || saveStatus === "saving"}>
                  <Save className="h-4 w-4 mr-2" />
                  Save Profile
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Add New Action */}
            <div className="flex items-end gap-3">
              <div className="flex-1">
                <Label className="my-2.5" htmlFor="new-action">Add New Action</Label>
                <Input
                  id="new-action"
                  value={newActionName}
                  onChange={(e) => setNewActionName(e.target.value)}
                  placeholder="e.g., JUMP, FIRE, RELOAD"
                  onKeyDown={(e) => e.key === "Enter" && handleAddAction()}
                />
              </div>
              <Button onClick={handleAddAction} disabled={!newActionName.trim()}>
                <Plus className="h-4 w-4 mr-2" />
                Add Action
              </Button>
            </div>

            {/* Actions Table */}
            {actions.length > 0 ? (
              <div className="space-y-4">
                <EditableTable
                  data={actions}
                  onUpdate={handleActionUpdate}
                  onTest={isOnline ? handleTestAction : undefined}
                />

                <div className="flex items-center gap-3">
                  <Button size="sm" variant="destructive" onClick={handleDeleteAction} disabled={!selectedActionId}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Selected
                  </Button>
                  <div className="text-sm text-muted-foreground">
                    Click on a row to select it, then use the Test button or delete it.
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <div className="text-lg font-medium mb-2">No Actions Configured</div>
                <div className="text-sm">Add your first action mapping to get started.</div>
              </div>
            )}

            {!isOnline && (
              <Alert className="border-destructive bg-destructive/10">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <AlertDescription className="text-destructive">
                  Backend not running. Test functionality is disabled.
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {!selectedProfile && (
        <Card className="glass-panel">
          <CardContent className="text-center py-12">
            <Gamepad2 className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50" />
            <div className="text-lg font-medium mb-2">Select a Profile</div>
            <div className="text-sm text-muted-foreground">
              Choose a profile from the dropdown above to manage its action mappings.
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
