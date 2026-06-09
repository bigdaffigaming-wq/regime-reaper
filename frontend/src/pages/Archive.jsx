import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import SourceBadge from '../components/SourceBadge'
import VerdictBadge from '../components/VerdictBadge'
import ScoreBadge from '../components/ScoreBadge'

const STATUSES = ['all', 'new', 'reviewed', 'watchlist', 'contacted', 'rejected', 'bought', 'archived']
const SOURCES  = ['all', 'facebook', 'craigslist', 'manual']

export default function Archive() {
  const [listings, setListings]   = useState([])
  const [analyses, setAnalyses]   = useState({})
  const [loading, setLoading]     = useState(true)
  const [search, setSearch]       = useState('')
  const [filterStatus, setFilterStatus] = useState('all')
  const [filterSource, setFilterSource] = useState('all')
  const [filterVerdict, setFilterVerdict] = useState('all')
  const [page, setPage]           = useState(0)
  const PER_PAGE = 30
  const navigate = useNavigate()

  useEffect(() => {
    api.getListings({ limit: 500 }).then(res => {
      setListings(res.data)
      // Fetch analyses in background
      res.data.forEach(async l => {
        try {
          const a = await api.getAnalysis(l.id)
          setAnalyses(prev => ({ ...prev, [l.id]: a.data }))
        } catch {}
      })
    }).finally(() => setLoading(false))
  }, [])

  const filtered = listings.filter(l => {
    if (filterStatus !== 'all' && l.status !== filterStatus) return false
    if (filterSource !== 'all' && l.source !== filterSource) return false
    const a = analyses[l.id]
    if (filterVerdict !== 'all' && a?.verdict !== filterVerdict) return false
    if (search) {
      const q = search.toLowerCase()
      return (
        l.title?.toLowerCase().includes(q) ||
        l.make?.toLowerCase().includes(q) ||
        l.model?.toLowerCase().includes(q) ||
        l.location?.toLowerCase().includes(q)
      )
    }
    return true
  })

  const paginated = filtered.slice(page * PER_PAGE, (page + 1) * PER_PAGE)
  const totalPages = Math.ceil(filtered.length / PER_PAGE)

  const fmt = (iso) => iso ? new Date(iso).toLocaleDateString() : '—'

  if (loading) return <div className="text-bone/50 text-center mt-20">Loading archive...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-gold font-bold text-xl tracking-wider">📁 LEADS ARCHIVE</h1>
        <div className="text-bone/40 text-xs">{filtered.length} leads</div>
      </div>

      {/* Filters */}
      <div className="bg-card border border-border rounded-lg p-4 flex flex-wrap gap-3">
        <input
          className="input-field flex-1 min-w-48"
          placeholder="Search by title, make, model, location..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
        />
        <select className="input-field" value={filterStatus} onChange={e => { setFilterStatus(e.target.value); setPage(0) }}>
          {STATUSES.map(s => <option key={s} value={s}>{s === 'all' ? 'All Statuses' : s.toUpperCase()}</option>)}
        </select>
        <select className="input-field" value={filterSource} onChange={e => { setFilterSource(e.target.value); setPage(0) }}>
          {SOURCES.map(s => <option key={s} value={s}>{s === 'all' ? 'All Sources' : s.toUpperCase()}</option>)}
        </select>
        <select className="input-field" value={filterVerdict} onChange={e => { setFilterVerdict(e.target.value); setPage(0) }}>
          {['all', 'BUY NOW', 'NEGOTIATE HARD', 'MONITOR', 'WALK AWAY'].map(v =>
            <option key={v} value={v}>{v === 'all' ? 'All Verdicts' : v}</option>
          )}
        </select>
      </div>

      {/* Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-border text-bone/40 uppercase tracking-wider">
              <th className="text-left p-3">Listing</th>
              <th className="text-left p-3">Source</th>
              <th className="text-right p-3">Price</th>
              <th className="text-right p-3">Mileage</th>
              <th className="text-center p-3">Score</th>
              <th className="text-center p-3">Verdict</th>
              <th className="text-right p-3">Profit</th>
              <th className="text-center p-3">Status</th>
              <th className="text-right p-3">Found</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map(l => {
              const a = analyses[l.id]
              return (
                <tr
                  key={l.id}
                  onClick={() => navigate(`/listing/${l.id}`)}
                  className="border-b border-border/50 hover:bg-white/5 cursor-pointer transition-colors"
                >
                  <td className="p-3">
                    <div className="text-bone font-medium max-w-xs truncate">{l.title}</div>
                    <div className="text-bone/30 mt-0.5 truncate">{l.location}</div>
                  </td>
                  <td className="p-3"><SourceBadge source={l.source} /></td>
                  <td className="p-3 text-right text-gold font-bold">${(l.price || 0).toLocaleString()}</td>
                  <td className="p-3 text-right text-bone/50">{l.mileage ? `${l.mileage.toLocaleString()}` : '—'}</td>
                  <td className="p-3 text-center">{a ? <ScoreBadge score={a.deal_score} /> : <span className="text-bone/20">—</span>}</td>
                  <td className="p-3 text-center">{a ? <VerdictBadge verdict={a.verdict} /> : <span className="text-bone/20">—</span>}</td>
                  <td className={`p-3 text-right font-bold ${a?.expected_profit >= 0 ? 'text-profit-green' : 'text-crimson'}`}>
                    {a ? `$${(a.expected_profit || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}` : '—'}
                  </td>
                  <td className="p-3 text-center">
                    <span className={`px-1.5 py-0.5 rounded text-xs ${
                      l.status === 'watchlist' ? 'bg-gold/20 text-gold' :
                      l.status === 'bought'    ? 'bg-profit-green/20 text-profit-green' :
                      l.status === 'rejected'  ? 'bg-crimson/20 text-crimson' :
                      'bg-white/10 text-bone/40'
                    }`}>{l.status}</span>
                  </td>
                  <td className="p-3 text-right text-bone/30">{fmt(l.created_at)}</td>
                </tr>
              )
            })}
            {paginated.length === 0 && (
              <tr>
                <td colSpan={9} className="p-8 text-center text-bone/20">No leads match your filters</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-bone/40">
          <span>Page {page + 1} of {totalPages} — {filtered.length} total</span>
          <div className="flex gap-2">
            <button disabled={page === 0} onClick={() => setPage(p => p - 1)}
              className="px-3 py-1 border border-border rounded disabled:opacity-30 hover:border-gold/50 hover:text-gold">← Prev</button>
            <button disabled={page >= totalPages - 1} onClick={() => setPage(p => p + 1)}
              className="px-3 py-1 border border-border rounded disabled:opacity-30 hover:border-gold/50 hover:text-gold">Next →</button>
          </div>
        </div>
      )}
    </div>
  )
}
