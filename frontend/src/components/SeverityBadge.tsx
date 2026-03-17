type Props = {
  severity: string
}

function severityClass(severity: string): string {
  const s = severity.toLowerCase()
  if (s === 'mild') return 'bg-emerald-50 text-emerald-800 ring-emerald-200'
  if (s === 'moderate') return 'bg-amber-50 text-amber-800 ring-amber-200'
  if (s === 'severe') return 'bg-rose-50 text-rose-800 ring-rose-200'
  return 'bg-slate-50 text-slate-800 ring-slate-200'
}

export default function SeverityBadge({ severity }: Props) {
  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-3 py-1 text-sm font-medium ring-1 ring-inset',
        severityClass(severity),
      ].join(' ')}
    >
      {severity}
    </span>
  )
}

