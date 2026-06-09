import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import DealCard from '../components/DealCard'

const COLUMNS = [
  { status: 'new', label: 'New Leads' },
  { status: 'reviewed', label: 'Reviewed' },
  { status: 'watchlist', label: 'Watchlist' },
  { status: 'contacted', label: 'Contacted' },
  { status: 'appointment_set', label: 'Appt Set' },
  { status: 'negotiating', label: 'Negotiating' },
]

export default function Watchlist() {
  const [listings, setListings] = useState([])
  const [analyses, setAnalyses] = useState({})
  const navigate = useNavigate()

  useEffect(() => {
    api.getListings({ limit: 100 }).then(res => {
      const all = res.data
      setListings(all)
      all.forEach(async l => {
        try {
          const a = await api.getAnalysis(l.id)
          setAnalyses(prev => ({ ...prev, [l.id]: a.data }))
        } catch {}
      })
    })
  }, [])

  const moveStatus = async (listingId, newStatus) => {
    await api.updateListing(listingId, { status: newStatus })
    setListings(prev => prev.map(l => l.id === listingId ? { ...l, status: newStatus } : l))
  }

  return (
    <div>
      <h1 className="text-gold font-bold text-xl tracking-wider mb-6">👁 WATCHLIST</h1>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 overflow-x-auto">
        {COLUMNS.map(col => {
          const colListings = listings.filter(l => l.status === col.status)
          return (
            <div key={col.status} className="min-w-0">
              <div className="text-xs font-bold text-bone/50 uppercase tracking-wider mb-3 flex items-center justify-between">
                <span>{col.label}</span>
                <span className="bg-white/10 rounded px-1.5 py-0.5">{colListings.length}</span>
              </div>
              <div className="space-y-3">
                {colListings.map(l => (
                  <div key={l.id} className="group">
                    <DealCard
                      listing={l}
                      analysis={analyses[l.id]}
                      onClick={() => navigate(`/listing/${l.id}`)}
                    />
                    <div className="hidden group-hover:flex gap-1 mt-1 flex-wrap">
                      {COLUMNS.filter(c => c.status !== col.status).slice(0, 3).map(c => (
                        <button
                          key={c.status}
                          onClick={() => moveStatus(l.id, c.status)}
                          className="text-xs px-1.5 py-0.5 bg-white/5 hover:bg-gold/20 text-bone/50 hover:text-gold rounded"
                        >
                          → {c.label}
                        </button>
                      ))}
                      <button
                        onClick={() => moveStatus(l.id, 'rejected')}
                        className="text-xs px-1.5 py-0.5 bg-crimson/10 hover:bg-crimson/20 text-crimson rounded"
                      >
                        ✕ Remove
                      </button>
                    </div>
                  </div>
                ))}
                {colListings.length === 0 && (
                  <div className="text-bone/20 text-xs text-center py-4">Empty</div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
