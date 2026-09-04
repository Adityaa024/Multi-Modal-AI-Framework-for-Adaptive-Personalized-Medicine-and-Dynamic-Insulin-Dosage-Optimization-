type Props = {
  severity: string
}

function severityClass(severity: string): string {
  const s = severity.toLowerCase()
  if (s === 'mild') return 'badge badge-mild'
  if (s === 'moderate') return 'badge badge-moderate'
  if (s === 'severe') return 'badge badge-severe'
  return 'badge badge-default'
}

export default function SeverityBadge({ severity }: Props) {
  return (
    <span className={severityClass(severity)}>
      {severity}
    </span>
  )
}
