const COLORS = {
  facebook: 'bg-blue-600/30 text-blue-300',
  craigslist: 'bg-purple-600/30 text-purple-300',
  autotempest: 'bg-orange-600/30 text-orange-300',
  cars_com: 'bg-green-600/30 text-green-300',
  manual: 'bg-gray-600/30 text-gray-300',
}

export default function SourceBadge({ source }) {
  if (!source) return null
  return (
    <span className={`text-xs px-2 py-0.5 rounded font-medium ${COLORS[source] || 'bg-white/10 text-bone'}`}>
      {source.toUpperCase()}
    </span>
  )
}
