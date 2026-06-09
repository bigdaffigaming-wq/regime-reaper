import { useNavigate } from 'react-router-dom'
import VerdictBadge from './VerdictBadge'
import ScoreBadge from './ScoreBadge'
import SourceBadge from './SourceBadge'

function daysSince(iso) {
  if (!iso) return null
  const days = Math.floor((Date.now() - new Date(iso)) / 86400000)
  if (days === 0) return 'Today'
  if (days === 1) return '1 day ago'
  return `${days}d ago`
}

export default function DealCard({ listing, analysis, onClick }) {
  const navigate = useNavigate()

  const handleClick = () => {
    if (onClick) onClick()
    else navigate(`/listing/${listing.id}`)
  }

  return (
    <div
      onClick={handleClick}
      className="bg-card border border-border rounded-lg overflow-hidden cursor-pointer hover:border-gold/50 transition-colors"
    >
      {/* Thumbnail */}
      {listing.image_url ? (
        <img
          src={listing.image_url}
          alt={listing.title}
          className="w-full h-40 object-cover"
          onError={e => { e.target.style.display = 'none' }}
        />
      ) : (
        <div className="w-full h-40 bg-obsidian flex items-center justify-center text-bone/10 text-4xl">
          ☠
        </div>
      )}

      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex-1 min-w-0">
            <h3 className="text-bone font-semibold text-sm truncate">{listing.title}</h3>
            <div className="text-bone/50 text-xs mt-0.5">{listing.location || 'Unknown location'}</div>
          </div>
          <SourceBadge source={listing.source} />
        </div>

        <div className="flex items-center gap-3 mt-2">
          <div className="text-gold font-bold text-base">
            ${(listing.price || 0).toLocaleString()}
          </div>
          {listing.mileage && (
            <div className="text-bone/50 text-xs">{listing.mileage.toLocaleString()} mi</div>
          )}
        </div>

        {analysis && (
          <div className="mt-3 pt-3 border-t border-border flex items-center justify-between">
            <ScoreBadge score={analysis.deal_score} />
            <VerdictBadge verdict={analysis.verdict} />
            <div className={`text-sm font-bold ${analysis.expected_profit >= 0 ? 'text-profit-green' : 'text-crimson'}`}>
              ${(analysis.expected_profit || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
          </div>
        )}

        <div className="mt-2 flex items-center justify-between">
          <span className={`text-xs px-2 py-0.5 rounded ${
            listing.status === 'new'       ? 'bg-blue-500/20 text-blue-400' :
            listing.status === 'watchlist' ? 'bg-gold/20 text-gold' :
            listing.status === 'rejected'  ? 'bg-crimson/20 text-crimson' :
            'bg-white/10 text-bone/50'
          }`}>
            {listing.status?.toUpperCase()}
          </span>
          <div className="flex items-center gap-2">
            {listing.title_status && listing.title_status !== 'clean' && (
              <span className="text-xs text-crimson">{listing.title_status.toUpperCase()} TITLE</span>
            )}
            {listing.created_at && (
              <span className="text-xs text-bone/25">{daysSince(listing.created_at)}</span>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
