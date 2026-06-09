import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../api/client'
import VerdictBadge from '../components/VerdictBadge'
import ScoreBadge from '../components/ScoreBadge'
import ProfitBox from '../components/ProfitBox'

function ContactPanel({ listing, onSave }) {
  const [editing, setEditing] = useState(false)
  const [form, setForm] = useState({
    seller_phone: listing.seller_phone || '',
    seller_email: listing.seller_email || '',
    seller_address: listing.seller_address || '',
    notes: listing.notes || '',
  })
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.updateListing(listing.id, form)
      onSave(form)
      setEditing(false)
    } finally {
      setSaving(false)
    }
  }

  const hasContact = listing.seller_phone || listing.seller_email || listing.seller_address || listing.notes

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-gold text-xs font-bold tracking-wider uppercase">Seller Contact & Notes</h2>
        <button onClick={() => setEditing(!editing)} className="text-xs text-bone/50 hover:text-gold">
          {editing ? 'Cancel' : '✏️ Edit'}
        </button>
      </div>

      {editing ? (
        <div className="space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Phone</label>
              <input className="input-field w-full mt-1" placeholder="(555) 555-5555"
                value={form.seller_phone} onChange={e => setForm(f => ({ ...f, seller_phone: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Email</label>
              <input className="input-field w-full mt-1" placeholder="seller@email.com"
                value={form.seller_email} onChange={e => setForm(f => ({ ...f, seller_email: e.target.value }))} />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-bone/40 uppercase tracking-wider">Address / Location</label>
              <input className="input-field w-full mt-1" placeholder="123 Main St, Tampa FL 33601"
                value={form.seller_address} onChange={e => setForm(f => ({ ...f, seller_address: e.target.value }))} />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-bone/40 uppercase tracking-wider">My Notes</label>
              <textarea className="input-field w-full mt-1 h-20 resize-none"
                placeholder="Called at 3pm, seller motivated, car needs brakes, meeting Saturday..."
                value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
            </div>
          </div>
          <button onClick={handleSave} disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : '💾 Save'}
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {hasContact ? (
            <>
              {listing.seller_phone && (
                <div className="flex items-center gap-3">
                  <span className="text-bone/40 text-xs w-16">Phone</span>
                  <a href={`tel:${listing.seller_phone}`} className="text-gold text-sm hover:underline font-medium">
                    {listing.seller_phone}
                  </a>
                </div>
              )}
              {listing.seller_email && (
                <div className="flex items-center gap-3">
                  <span className="text-bone/40 text-xs w-16">Email</span>
                  <a href={`mailto:${listing.seller_email}`} className="text-gold text-sm hover:underline">
                    {listing.seller_email}
                  </a>
                </div>
              )}
              {listing.seller_address && (
                <div className="flex items-center gap-3">
                  <span className="text-bone/40 text-xs w-16">Address</span>
                  <span className="text-bone text-sm">{listing.seller_address}</span>
                </div>
              )}
              {listing.notes && (
                <div className="mt-3 pt-3 border-t border-border">
                  <div className="text-bone/40 text-xs uppercase tracking-wider mb-1">Notes</div>
                  <p className="text-bone text-sm whitespace-pre-wrap">{listing.notes}</p>
                </div>
              )}
            </>
          ) : (
            <div className="text-bone/20 text-xs text-center py-3">
              No contact info saved. Click Edit to add seller phone, email, address, and notes.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const SPEC_LABELS = {
  condition: 'Condition',
  body_type: 'Body Type',
  cylinders: 'Cylinders',
  transmission: 'Transmission',
  drive: 'Drive',
  fuel: 'Fuel',
  paint_color: 'Paint Color',
  title_status: 'Title Status',
}

const SPEC_CATEGORIES = {
  'Vehicle': ['condition', 'body_type', 'paint_color'],
  'Drivetrain': ['cylinders', 'transmission', 'drive', 'fuel'],
}

function VehicleSpecs({ listing }) {
  let specs = {}
  try {
    const raw = listing.raw_data_json ? JSON.parse(listing.raw_data_json) : {}
    specs = raw.vehicle_specs || {}
  } catch {}

  // Augment with listing-level fields
  if (listing.title_status && !specs.title_status) specs.title_status = listing.title_status

  const hasSpecs = Object.keys(specs).length > 0
  if (!hasSpecs) return null

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h2 className="text-gold text-xs font-bold tracking-wider uppercase mb-3">Vehicle Specs</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1">
        {Object.entries(SPEC_CATEGORIES).map(([cat, keys]) => {
          const entries = keys.filter(k => specs[k])
          if (!entries.length) return null
          return (
            <div key={cat}>
              <div className="text-bone/30 text-xs uppercase tracking-widest mb-1 mt-2">{cat}</div>
              {entries.map(k => (
                <div key={k} className="flex justify-between text-sm py-0.5 border-b border-border/30">
                  <span className="text-bone/50">{SPEC_LABELS[k]}</span>
                  <span className={`text-bone capitalize font-medium ${k === 'title_status' && specs[k] !== 'clean' ? 'text-crimson' : ''}`}>
                    {specs[k]}
                  </span>
                </div>
              ))}
            </div>
          )
        })}
      </div>
    </div>
  )
}

function PhotoGallery({ listing }) {
  const [active, setActive] = useState(0)

  let photos = []
  try {
    const raw = listing.raw_data_json ? JSON.parse(listing.raw_data_json) : {}
    photos = raw._all_photos || []
  } catch {}
  if (!photos.length && listing.image_url) photos = [listing.image_url]
  if (!photos.length) return null

  return (
    <div className="rounded-lg overflow-hidden border border-border">
      <img
        src={photos[active]}
        alt={listing.title}
        className="w-full max-h-80 object-cover"
        onError={e => { e.target.src = '' }}
      />
      {photos.length > 1 && (
        <div className="flex gap-1.5 p-2 bg-obsidian overflow-x-auto">
          {photos.map((p, i) => (
            <img
              key={i}
              src={p}
              alt=""
              onClick={() => setActive(i)}
              className={`h-14 w-20 object-cover rounded cursor-pointer flex-shrink-0 transition-opacity ${i === active ? 'opacity-100 ring-1 ring-gold' : 'opacity-50 hover:opacity-80'}`}
              onError={e => { e.target.style.display = 'none' }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default function ListingDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [listing, setListing] = useState(null)
  const [analysis, setAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)
  const [loading, setLoading] = useState(true)
  const [enriching, setEnriching] = useState(false)

  useEffect(() => {
    Promise.all([
      api.getListing(id),
      api.getAnalysis(id).catch(() => null),
    ]).then(([lRes, aRes]) => {
      const l = lRes.data
      setListing(l)
      if (aRes) setAnalysis(aRes.data)
      // Auto-load description if missing and listing has a URL
      if (!l.description && l.url && (l.source === 'craigslist' || l.source === 'facebook')) {
        setEnriching(true)
        api.enrichListing(l.id).then(r => {
          if (r.data?.enriched) return api.getListing(l.id)
        }).then(r => {
          if (r) setListing(r.data)
        }).catch(() => {}).finally(() => setEnriching(false))
      }
    }).finally(() => setLoading(false))
  }, [id])

  const runAnalysis = async () => {
    setAnalyzing(true)
    try {
      const res = await api.analyzeListing(id)
      setAnalysis(res.data)
    } finally {
      setAnalyzing(false)
    }
  }

  const setStatus = async (status) => {
    await api.updateListing(id, { status })
    setListing(l => ({ ...l, status }))
  }

  const watchlist = () => api.watchlistListing(id).then(() => setListing(l => ({ ...l, status: 'watchlist' })))
  const reject = () => api.rejectListing(id).then(() => setListing(l => ({ ...l, status: 'rejected' })))

  const buyNow = async () => {
    const price = prompt('Purchase price ($):')
    if (!price) return
    await api.createInventory(id, { purchase_price: Number(price) })
    navigate('/inventory')
  }

  if (loading) return <div className="text-bone/50 text-center mt-20">Loading...</div>
  if (!listing) return <div className="text-crimson text-center mt-20">Listing not found</div>

  const redFlags = analysis ? JSON.parse(analysis.red_flags_json || '[]') : []
  const greenFlags = analysis ? JSON.parse(analysis.green_flags_json || '[]') : []
  const inspectionQs = analysis ? JSON.parse(analysis.inspection_questions_json || '[]') : []

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <button onClick={() => navigate(-1)} className="text-bone/50 hover:text-gold text-sm">← Back</button>
        <h1 className="text-bone font-bold text-lg flex-1">{listing.title}</h1>
        <span className={`text-xs px-2 py-0.5 rounded ${listing.status === 'watchlist' ? 'bg-gold/20 text-gold' : 'bg-white/10 text-bone/50'}`}>
          {listing.status?.toUpperCase()}
        </span>
      </div>

      {/* Photo Gallery */}
      <PhotoGallery listing={listing} />

      {/* Vehicle Specs */}
      <VehicleSpecs listing={listing} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Listing Info */}
        <div className="bg-card border border-border rounded-lg p-5 space-y-3">
          <h2 className="text-gold text-xs font-bold tracking-wider uppercase">Listing Info</h2>
          {[
            ['Source', listing.source],
            ['Price', `$${listing.price?.toLocaleString()}`],
            ['Mileage', listing.mileage ? `${listing.mileage.toLocaleString()} miles` : 'N/A'],
            ['Year', listing.year || 'N/A'],
            ['Make', listing.make || 'N/A'],
            ['Model', listing.model || 'N/A'],
            ['Location', listing.location || 'N/A'],
            ['Title Status', listing.title_status?.toUpperCase()],
            ['Seller', listing.seller_name || 'N/A'],
            ['VIN', listing.vin || 'N/A'],
          ].map(([k, v]) => (
            <div key={k} className="flex justify-between text-sm">
              <span className="text-bone/50">{k}</span>
              <span className={`text-bone ${k === 'Title Status' && listing.title_status !== 'clean' ? 'text-crimson font-bold' : ''}`}>{v}</span>
            </div>
          ))}
          {listing.url && (
            <a href={listing.url} target="_blank" rel="noopener noreferrer" className="text-gold text-xs hover:underline">View Original Listing →</a>
          )}
        </div>

        {/* Analysis */}
        <div className="bg-card border border-border rounded-lg p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-gold text-xs font-bold tracking-wider uppercase">Analysis</h2>
            {!analysis && (
              <button onClick={runAnalysis} disabled={analyzing} className="btn-primary text-xs px-3 py-1">
                {analyzing ? 'Analyzing...' : '☠️ Analyze'}
              </button>
            )}
          </div>

          {analysis ? (
            <>
              <div className="flex items-center justify-between">
                <ScoreBadge score={analysis.deal_score} />
                <VerdictBadge verdict={analysis.verdict} />
              </div>
              <ProfitBox profit={analysis.expected_profit} roi={analysis.roi_percent} />
              {[
                ['Est. Repairs', `$${(analysis.estimated_repair_cost || 0).toLocaleString()}`],
                ['Est. Resale', `$${(analysis.estimated_resale_value || 0).toLocaleString()}`],
                ['Recommended Offer', `$${(analysis.recommended_offer || 0).toLocaleString()}`],
                ['Risk Level', analysis.risk_level?.toUpperCase()],
              ].map(([k, v]) => (
                <div key={k} className="flex justify-between text-sm">
                  <span className="text-bone/50">{k}</span>
                  <span className={`text-bone ${k === 'Risk Level' && (analysis.risk_level === 'high' || analysis.risk_level === 'extreme') ? 'text-crimson font-bold' : ''}`}>{v}</span>
                </div>
              ))}

              {analysis.negotiation_message && (
                <div>
                  <div className="text-xs text-bone/50 uppercase tracking-wider mb-1">Negotiation Message</div>
                  <div className="text-xs text-bone bg-obsidian rounded p-2 italic">{analysis.negotiation_message}</div>
                </div>
              )}

              {analysis.llm_summary && (
                <div>
                  <div className="text-xs text-bone/50 uppercase tracking-wider mb-1">REAPER Notes</div>
                  <div className="text-xs text-bone">{analysis.llm_summary}</div>
                </div>
              )}
            </>
          ) : (
            <div className="text-bone/30 text-sm text-center py-6">No analysis yet. Click Analyze.</div>
          )}
        </div>
      </div>

      {/* Description Intel */}
      {analysis?.description_intel_json && (() => {
        let intel = null
        try { intel = JSON.parse(analysis.description_intel_json) } catch {}
        if (!intel) return null
        const hasMods = intel.modifications?.length > 0
        const hasIssues = intel.issues_mentioned?.length > 0
        const hasFacts = intel.key_facts?.length > 0
        if (!hasMods && !hasIssues && !hasFacts && !intel.engine && !intel.seller_signals) return null
        return (
          <div className="bg-card border border-gold/20 rounded-lg p-4">
            <h2 className="text-gold text-xs font-bold tracking-wider uppercase mb-3">REAPER Intel — From Description</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              {(intel.engine || intel.seller_signals) && (
                <div className="space-y-2">
                  {intel.engine && (
                    <div className="flex gap-2">
                      <span className="text-bone/40 w-20 shrink-0">Engine</span>
                      <span className="text-bone">{intel.engine}</span>
                    </div>
                  )}
                  {intel.seller_signals && (
                    <div className="flex gap-2">
                      <span className="text-bone/40 w-20 shrink-0">Seller</span>
                      <span className={`${intel.seller_signals.toLowerCase().includes('broker') || intel.seller_signals.toLowerCase().includes('dealer') || intel.seller_signals.toLowerCase().includes('atoban') ? 'text-crimson font-semibold' : 'text-bone'}`}>
                        {intel.seller_signals}
                      </span>
                    </div>
                  )}
                  {hasFacts && intel.key_facts.map((f, i) => (
                    <div key={i} className="flex gap-2">
                      <span className="text-bone/40 w-20 shrink-0">{i === 0 ? 'Key Facts' : ''}</span>
                      <span className="text-bone/80">• {f}</span>
                    </div>
                  ))}
                </div>
              )}
              <div className="space-y-3">
                {hasIssues && (
                  <div>
                    <div className="text-crimson/80 text-xs uppercase tracking-wider mb-1">Issues Admitted</div>
                    {intel.issues_mentioned.map((issue, i) => (
                      <div key={i} className="text-crimson/90 text-xs py-0.5">⚠ {issue}</div>
                    ))}
                  </div>
                )}
                {hasMods && (
                  <div>
                    <div className="text-bone/40 text-xs uppercase tracking-wider mb-1">Modifications</div>
                    {intel.modifications.map((mod, i) => (
                      <div key={i} className="text-bone/70 text-xs py-0.5">• {mod}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )
      })()}

      {/* Flags */}
      {(redFlags.length > 0 || greenFlags.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {redFlags.length > 0 && (
            <div className="bg-card border border-crimson/30 rounded-lg p-4">
              <h2 className="text-crimson text-xs font-bold tracking-wider uppercase mb-2">Red Flags</h2>
              {redFlags.map((f, i) => <div key={i} className="text-sm text-bone/80 py-0.5">• {f}</div>)}
            </div>
          )}
          {greenFlags.length > 0 && (
            <div className="bg-card border border-profit-green/30 rounded-lg p-4">
              <h2 className="text-profit-green text-xs font-bold tracking-wider uppercase mb-2">Green Flags</h2>
              {greenFlags.map((f, i) => <div key={i} className="text-sm text-bone/80 py-0.5">• {f}</div>)}
            </div>
          )}
        </div>
      )}

      {/* Seller Contact + Notes */}
      <ContactPanel listing={listing} onSave={(updated) => setListing(l => ({ ...l, ...updated }))} />

      {/* Description */}
      <div className="bg-card border border-border rounded-lg p-4">
        <h2 className="text-gold text-xs font-bold tracking-wider uppercase mb-2">Seller Description</h2>
        {listing.description ? (
          <p className="text-bone/70 text-sm whitespace-pre-wrap leading-relaxed">{listing.description}</p>
        ) : enriching ? (
          <p className="text-bone/30 text-sm animate-pulse">Loading description from listing page...</p>
        ) : (
          <p className="text-bone/20 text-sm">No description available. Run analysis to load full details.</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3 flex-wrap">
        {listing.status !== 'watchlist' && (
          <button onClick={watchlist} className="btn-secondary">👁 Add to Watchlist</button>
        )}
        {listing.status === 'watchlist' && (
          <button onClick={() => setStatus('new')} className="btn-secondary">✕ Remove from Watchlist</button>
        )}
        {listing.status !== 'rejected' && (
          <button onClick={reject} className="px-4 py-2 text-xs border border-crimson/50 text-crimson rounded hover:bg-crimson/10 transition-colors">🔴 Reject</button>
        )}
        {analysis && analysis.verdict !== 'WALK AWAY' && (
          <button onClick={buyNow} className="px-4 py-2 text-xs border border-profit-green text-profit-green rounded hover:bg-profit-green/10 transition-colors font-bold">
            ✅ MARK AS BOUGHT
          </button>
        )}
        {analysis && (
          <button onClick={runAnalysis} disabled={analyzing} className="btn-secondary">
            {analyzing ? 'Re-analyzing...' : '🔄 Re-Analyze'}
          </button>
        )}
      </div>
    </div>
  )
}
