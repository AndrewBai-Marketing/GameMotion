"use client";
import { Slider } from "@/components/ui/slider";
import { Label } from "@/components/ui/label";

type Props = {
  label: string;
  value?: number;
  onChange: (v: number) => void;
  min?: number;
  max?: number;
  step?: number;
};

export default function ThresholdSlider({
  label,
  value = 0,
  onChange,
  min = 0,
  max = 1,
  step = 0.01,
}: Props) {
  const v = typeof value === "number" ? value : 0;
  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <Label className="text-sm font-medium">{label}</Label>
        <span className="text-sm font-mono text-primary">{v.toFixed(2)}</span>
      </div>
      <Slider
        value={[v]}
        min={min}
        max={max}
        step={step}
        onValueChange={(vals) => onChange(vals[0] ?? v)}
      />
    </div>
  );
}
