export default function ScoreBadge({ score }) {
  if (score == null) return null
  const color =
    score >= 85 ? 'text-profit-green' :
    score >= 70 ? 'text-amber' :
    score >= 55 ? 'text-blue-400' :
    'text-crimson'

  return (
    <span className={`font-bold text-sm ${color}`}>
      {score}<span className="text-xs text-bone/50">/100</span>
    </span>
  )
}
