interface NumberStatProps {
  label: string
  value: number | string
  className?: string
}

export function NumberStat({ label, value, className = "" }: NumberStatProps) {
  return (
    <div className={`text-center space-y-1 ${className}`}>
      <div className="text-2xl md:text-3xl font-heading font-bold font-mono text-primary">{value}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  )
}
