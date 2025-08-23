"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { ThresholdSlider } from "@/components/threshold-slider"
import { useSettings, saveSettings, useHealth } from "@/lib/api"
import { Settings, Target, Brain, RotateCcw, Save, RefreshCw, CheckCircle, AlertCircle, HelpCircle } from "lucide-react"

interface SettingsState {
  // Detection settings
  fire_threshold: number
  release_threshold: number
  rearm_frames: number
  frames_confirm: number
  decision_margin: number
  ratio_threshold: number
  single_label_threshold: number
  min_samples_per_action: number
  action_cooldown_sec: number
  // Training settings
  train_sample_every_ms: number
  train_motion_var_max: number
}

const defaultSettings: SettingsState = {
  fire_threshold: 0.8,
  release_threshold: 0.3,
  rearm_frames: 10,
  frames_confirm: 3,
  decision_margin: 0.1,
  ratio_threshold: 0.7,
  single_label_threshold: 0.9,
  min_samples_per_action: 50,
  action_cooldown_sec: 0.5,
  train_sample_every_ms: 100,
  train_motion_var_max: 0.2,
}

const settingsInfo = {
  fire_threshold: "Minimum confidence required to trigger an action. Higher values reduce false positives.",
  release_threshold: "Confidence below which an action is considered released. Lower values prevent flickering.",
  rearm_frames: "Number of frames to wait before the same action can be triggered again.",
  frames_confirm: "Number of consecutive frames above threshold required to confirm an action.",
  decision_margin: "Minimum difference between top two predictions for confident detection.",
  ratio_threshold: "Minimum ratio between highest and second-highest confidence for action firing.",
  single_label_threshold: "Confidence threshold when only one action is detected in the frame.",
  min_samples_per_action: "Minimum training samples required per action for reliable detection.",
  action_cooldown_sec: "Minimum time (seconds) between consecutive action triggers.",
  train_sample_every_ms: "Interval (milliseconds) between capturing training samples.",
  train_motion_var_max: "Maximum motion variance allowed during training sample capture.",
}

export function SettingsContent() {
  const { data: backendSettings, mutate: mutateSettings } = useSettings()
  const { data: health } = useHealth()
  const [settings, setSettings] = useState<SettingsState>(defaultSettings)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle")

  const isOnline = health?.ok && !health.error

  // Load settings from backend when available
  useEffect(() => {
    if (backendSettings) {
      setSettings(backendSettings)
      setHasUnsavedChanges(false)
    }
  }, [backendSettings])

  const updateSetting = (key: keyof SettingsState, value: number) => {
    setSettings((prev) => ({ ...prev, [key]: value }))
    setHasUnsavedChanges(true)
    setSaveStatus("idle")
  }

  const handleSave = async () => {
    setSaveStatus("saving")
    try {
      await saveSettings(settings)
      await mutateSettings()
      setHasUnsavedChanges(false)
      setSaveStatus("saved")
      setTimeout(() => setSaveStatus("idle"), 3000)
    } catch (error) {
      console.error("Failed to save settings:", error)
      setSaveStatus("error")
      setTimeout(() => setSaveStatus("idle"), 3000)
    }
  }

  const handleReload = async () => {
    try {
      await mutateSettings()
      setSaveStatus("idle")
    } catch (error) {
      console.error("Failed to reload settings:", error)
    }
  }

  const handleRestoreDefaults = () => {
    const confirm = window.confirm(
      "Are you sure you want to restore default settings? This will overwrite your current configuration.",
    )
    if (!confirm) return

    setSettings(defaultSettings)
    setHasUnsavedChanges(true)
    setSaveStatus("idle")
  }

  const SettingWithTooltip = ({
    label,
    info,
    children,
  }: {
    label: string
    info: string
    children: React.ReactNode
  }) => (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Label className="text-sm font-medium">{label}</Label>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <HelpCircle className="h-3 w-3 text-muted-foreground cursor-help" />
            </TooltipTrigger>
            <TooltipContent className="max-w-xs">
              <p className="text-xs">{info}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
      {children}
    </div>
  )

  return (
    <div className="space-y-6">
      {/* Status Alert */}
      {saveStatus !== "idle" && (
        <Alert className={saveStatus === "error" ? "border-destructive" : "border-primary"}>
          {saveStatus === "saved" ? (
            <CheckCircle className="h-4 w-4 text-primary" />
          ) : saveStatus === "error" ? (
            <AlertCircle className="h-4 w-4 text-destructive" />
          ) : null}
          <AlertDescription>
            {saveStatus === "saving" && "Saving settings..."}
            {saveStatus === "saved" && "Settings saved successfully!"}
            {saveStatus === "error" && "Failed to save settings. Please try again."}
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Detection Settings */}
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle className="font-heading text-xl flex items-center gap-2">
              <Target className="h-5 w-5 text-primary" />
              Detection Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <SettingWithTooltip label="Fire Threshold" info={settingsInfo.fire_threshold}>
              <ThresholdSlider
                label=""
                value={settings.fire_threshold}
                onChange={(value) => updateSetting("fire_threshold", value)}
                min={0}
                max={1}
                step={0.01}
              />
            </SettingWithTooltip>

            <SettingWithTooltip label="Release Threshold" info={settingsInfo.release_threshold}>
              <ThresholdSlider
                label=""
                value={settings.release_threshold}
                onChange={(value) => updateSetting("release_threshold", value)}
                min={0}
                max={1}
                step={0.01}
              />
            </SettingWithTooltip>

            <SettingWithTooltip label="Decision Margin" info={settingsInfo.decision_margin}>
              <ThresholdSlider
                label=""
                value={settings.decision_margin}
                onChange={(value) => updateSetting("decision_margin", value)}
                min={0}
                max={0.5}
                step={0.01}
              />
            </SettingWithTooltip>

            <SettingWithTooltip label="Ratio Threshold" info={settingsInfo.ratio_threshold}>
              <ThresholdSlider
                label=""
                value={settings.ratio_threshold}
                onChange={(value) => updateSetting("ratio_threshold", value)}
                min={0}
                max={1}
                step={0.01}
              />
            </SettingWithTooltip>

            <SettingWithTooltip label="Single Label Threshold" info={settingsInfo.single_label_threshold}>
              <ThresholdSlider
                label=""
                value={settings.single_label_threshold}
                onChange={(value) => updateSetting("single_label_threshold", value)}
                min={0}
                max={1}
                step={0.01}
              />
            </SettingWithTooltip>

            <SettingWithTooltip label="Action Cooldown (seconds)" info={settingsInfo.action_cooldown_sec}>
              <ThresholdSlider
                label=""
                value={settings.action_cooldown_sec}
                onChange={(value) => updateSetting("action_cooldown_sec", value)}
                min={0}
                max={2}
                step={0.1}
              />
            </SettingWithTooltip>

            <div className="grid grid-cols-2 gap-4">
              <SettingWithTooltip label="Rearm Frames" info={settingsInfo.rearm_frames}>
                <Input
                  type="number"
                  value={settings.rearm_frames}
                  onChange={(e) => updateSetting("rearm_frames", Number.parseInt(e.target.value) || 0)}
                  min={1}
                  max={100}
                  className="font-mono"
                />
              </SettingWithTooltip>

              <SettingWithTooltip label="Frames Confirm" info={settingsInfo.frames_confirm}>
                <Input
                  type="number"
                  value={settings.frames_confirm}
                  onChange={(e) => updateSetting("frames_confirm", Number.parseInt(e.target.value) || 0)}
                  min={1}
                  max={20}
                  className="font-mono"
                />
              </SettingWithTooltip>
            </div>

            <SettingWithTooltip label="Min Samples Per Action" info={settingsInfo.min_samples_per_action}>
              <Input
                type="number"
                value={settings.min_samples_per_action}
                onChange={(e) => updateSetting("min_samples_per_action", Number.parseInt(e.target.value) || 0)}
                min={10}
                max={500}
                className="font-mono"
              />
            </SettingWithTooltip>
          </CardContent>
        </Card>

        {/* Training Settings */}
        <Card className="glass-panel">
          <CardHeader>
            <CardTitle className="font-heading text-xl flex items-center gap-2">
              <Brain className="h-5 w-5 text-primary" />
              Training Settings
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <SettingWithTooltip label="Sample Interval (ms)" info={settingsInfo.train_sample_every_ms}>
              <Input
                type="number"
                value={settings.train_sample_every_ms}
                onChange={(e) => updateSetting("train_sample_every_ms", Number.parseInt(e.target.value) || 0)}
                min={50}
                max={1000}
                step={10}
                className="font-mono"
              />
            </SettingWithTooltip>

            <SettingWithTooltip label="Max Motion Variance" info={settingsInfo.train_motion_var_max}>
              <ThresholdSlider
                label=""
                value={settings.train_motion_var_max}
                onChange={(value) => updateSetting("train_motion_var_max", value)}
                min={0}
                max={1}
                step={0.01}
              />
            </SettingWithTooltip>

            {/* Training Tips */}
            <div className="mt-8 p-4 bg-muted/30 rounded-lg">
              <h4 className="font-heading font-semibold text-sm mb-3 text-primary">Training Tips</h4>
              <div className="space-y-2 text-xs text-muted-foreground">
                <div className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                  <span>Lower sample intervals capture more data but may include motion blur</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                  <span>Higher motion variance allows more movement during capture</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-1 h-1 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                  <span>Adjust based on your movement speed and camera setup</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <Card className="glass-panel">
        <CardContent className="pt-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              {hasUnsavedChanges && (
                <div className="text-sm text-yellow-500 flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  You have unsaved changes
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              <Button variant="outline" onClick={handleRestoreDefaults} disabled={saveStatus === "saving"}>
                <RotateCcw className="h-4 w-4 mr-2" />
                Restore Defaults
              </Button>

              <Button variant="outline" onClick={handleReload} disabled={!isOnline || saveStatus === "saving"}>
                <RefreshCw className="h-4 w-4 mr-2" />
                Reload from Backend
              </Button>

              <Button
                onClick={handleSave}
                disabled={!hasUnsavedChanges || !isOnline || saveStatus === "saving"}
                className="neon-glow"
              >
                <Save className="h-4 w-4 mr-2" />
                Save Settings
              </Button>
            </div>
          </div>

          {!isOnline && (
            <Alert className="border-destructive bg-destructive/10 mt-4">
              <AlertCircle className="h-4 w-4 text-destructive" />
              <AlertDescription className="text-destructive">
                Backend not running. Settings cannot be saved or reloaded.
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
