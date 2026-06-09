const STYLES = {
  'BUY NOW': 'bg-profit-green/20 text-profit-green border-profit-green',
  'NEGOTIATE HARD': 'bg-amber/20 text-amber border-amber',
  'MONITOR': 'bg-blue-500/20 text-blue-400 border-blue-500',
  'WALK AWAY': 'bg-crimson/20 text-crimson border-crimson',
}

export default function VerdictBadge({ verdict }) {
  if (!verdict) return null
  return (
    <span className={`text-xs font-bold px-2 py-0.5 border rounded tracking-wider ${STYLES[verdict] || 'bg-white/10 text-bone border-bone'}`}>
      {verdict}
    </span>
  )
}
