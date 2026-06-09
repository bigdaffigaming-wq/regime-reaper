import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import DealCard from '../components/DealCard'

function CreditsBar() {
  const [credits, setCredits] = useState(null)

  useEffect(() => {
    api.getCredits().then(res => setCredits(res.data.scrapfly)).catch(() => {})
  }, [])

  if (!credits) return null

  const pct = credits.credits_limit > 0
    ? Math.round((credits.credits_used / credits.credits_limit) * 100)
    : 0
  const remaining = credits.credits_remaining
  const color = remaining < 100 ? 'bg-crimson' : remaining < 300 ? 'bg-amber' : 'bg-profit-green'

  return (
    <div className="bg-card border border-border rounded-lg px-4 py-2 flex items-center gap-4">
      <span className="text-bone/40 text-xs uppercase tracking-wider">Scrapfly Credits</span>
      <div className="flex-1 bg-obsidian rounded-full h-1.5 max-w-48">
        <div className={`h-1.5 rounded-full ${color}`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
      <span className={`text-xs font-bold ${remaining < 100 ? 'text-crimson' : remaining < 300 ? 'text-amber' : 'text-profit-green'}`}>
        {remaining.toLocaleString()} remaining
      </span>
      <span className="text-bone/30 text-xs">{credits.credits_used.toLocaleString()} / {credits.credits_limit.toLocaleString()}</span>
      {credits.reset_at && <span className="text-bone/20 text-xs">Resets: {new Date(credits.reset_at).toLocaleDateString()}</span>}
    </div>
  )
}

function ScannerWidget() {
  const [status, setStatus] = useState(null)
  const [interval, setIntervalVal] = useState(30)

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.getScanStatus()
      setStatus(res.data)
    } catch {}
  }, [])

  useEffect(() => {
    fetchStatus()
    const t = setInterval(fetchStatus, 15000)
    return () => clearInterval(t)
  }, [fetchStatus])

  const scanNow = async () => {
    await api.scanNow()
    setTimeout(fetchStatus, 1000)
  }

  const toggleScan = async () => {
    if (status?.enabled) {
      await api.stopScan()
    } else {
      await api.startScan(interval)
    }
    setTimeout(fetchStatus, 500)
  }

  const formatTime = (iso) => {
    if (!iso) return 'Never'
    return new Date(iso).toLocaleTimeString()
  }

  const enabled = status?.enabled
  const running = status?.running

  return (
    <div className="bg-card border border-border rounded-lg p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${running ? 'bg-amber animate-pulse' : enabled ? 'bg-profit-green animate-pulse' : 'bg-bone/20'}`} />
          <h2 className="text-gold text-sm font-bold tracking-wider uppercase">Auto Scanner</h2>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded font-bold ${running ? 'bg-amber/20 text-amber' : enabled ? 'bg-profit-green/20 text-profit-green' : 'bg-white/10 text-bone/30'}`}>
          {running ? 'SCANNING...' : enabled ? 'ACTIVE' : 'OFF'}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4 text-center">
        <div>
          <div className="text-bone/40 text-xs">Last Scan</div>
          <div className="text-bone text-xs font-medium">{formatTime(status?.last_scan)}</div>
        </div>
        <div>
          <div className="text-bone/40 text-xs">Found</div>
          <div className="text-profit-green text-sm font-bold">{status?.last_found ?? 0}</div>
        </div>
        <div>
          <div className="text-bone/40 text-xs">Alerted</div>
          <div className="text-gold text-sm font-bold">{status?.last_alerted ?? 0}</div>
        </div>
      </div>

      <div className="flex items-center gap-2 mb-3">
        <span className="text-bone/40 text-xs">Every</span>
        <select
          className="input-field text-xs py-1 flex-1"
          value={interval}
          onChange={e => setIntervalVal(Number(e.target.value))}
        >
          <option value={5}>5 min</option>
          <option value={15}>15 min</option>
          <option value={30}>30 min</option>
          <option value={60}>1 hour</option>
          <option value={120}>2 hours</option>
        </select>
      </div>

      <div className="flex gap-2">
        <button
          onClick={toggleScan}
          className={`flex-1 text-xs py-2 rounded font-bold tracking-wider transition-colors ${
            enabled
              ? 'bg-crimson/20 border border-crimson/50 text-crimson hover:bg-crimson/30'
              : 'bg-profit-green/20 border border-profit-green/50 text-profit-green hover:bg-profit-green/30'
          }`}
        >
          {enabled ? '⏹ STOP' : '▶ START'}
        </button>
        <button
          onClick={scanNow}
          disabled={running}
          className="flex-1 text-xs py-2 rounded font-bold tracking-wider border border-gold/50 text-gold hover:bg-gold/10 transition-colors disabled:opacity-40"
        >
          {running ? 'SCANNING...' : '☠️ SCAN NOW'}
        </button>
      </div>

      {status?.next_scan && enabled && (
        <div className="text-bone/30 text-xs text-center mt-2">
          Next scan: {formatTime(status.next_scan)}
        </div>
      )}
      {status?.error && (
        <div className="text-crimson text-xs mt-2 truncate">Error: {status.error}</div>
      )}
    </div>
  )
}

export default function Dashboard() {
  const [listings, setListings] = useState([])
  const [analyses, setAnalyses] = useState({})
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      api.getListings({ limit: 20 }),
      api.getInventory(),
    ]).then(([lRes, iRes]) => {
      setListings(lRes.data)
      setInventory(iRes.data)
    }).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    listings.forEach(async (l) => {
      try {
        const res = await api.getAnalysis(l.id)
        setAnalyses(prev => ({ ...prev, [l.id]: res.data }))
      } catch {}
    })
  }, [listings])

  const scoredListings = listings
    .filter(l => analyses[l.id])
    .sort((a, b) => (analyses[b.id]?.deal_score || 0) - (analyses[a.id]?.deal_score || 0))

  const watchlist = listings.filter(l => l.status === 'watchlist')
  const newLeads = listings.filter(l => l.status === 'new')
  const activeInventory = inventory.filter(i => i.inventory_status !== 'sold')
  const soldInventory = inventory.filter(i => i.inventory_status === 'sold')
  const monthlyProfit = soldInventory.reduce((sum, i) => sum + (i.net_profit || 0), 0)

  if (loading) return <div className="text-bone/50 text-center mt-20">Loading REAPER...</div>

  return (
    <div className="space-y-6">
      <CreditsBar />
      {/* Scanner + Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ScannerWidget />
        <div className="md:col-span-2 grid grid-cols-2 md:grid-cols-4 gap-4 content-start">
          {[
            { label: 'New Leads', value: newLeads.length, color: 'text-blue-400' },
            { label: 'Watchlist', value: watchlist.length, color: 'text-gold' },
            { label: 'In Inventory', value: activeInventory.length, color: 'text-amber' },
            { label: 'Monthly Profit', value: `$${monthlyProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: monthlyProfit >= 0 ? 'text-profit-green' : 'text-crimson' },
          ].map(stat => (
            <div key={stat.label} className="bg-card border border-border rounded-lg p-4">
              <div className="text-bone/50 text-xs uppercase tracking-wider">{stat.label}</div>
              <div className={`text-2xl font-bold mt-1 ${stat.color}`}>{stat.value}</div>
            </div>
          ))}
        </div>
      </div>


      {/* Best Deals */}
      {scoredListings.length > 0 && (
        <section>
          <h2 className="text-gold text-sm font-bold tracking-wider uppercase mb-3">Top Deals</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {scoredListings.slice(0, 6).map(l => (
              <DealCard key={l.id} listing={l} analysis={analyses[l.id]} />
            ))}
          </div>
        </section>
      )}

      {/* Watchlist Preview */}
      {watchlist.length > 0 && (
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-gold text-sm font-bold tracking-wider uppercase">Watchlist</h2>
            <button onClick={() => navigate('/watchlist')} className="text-xs text-bone/50 hover:text-gold">View All →</button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {watchlist.slice(0, 3).map(l => (
              <DealCard key={l.id} listing={l} analysis={analyses[l.id]} />
            ))}
          </div>
        </section>
      )}

      {listings.length === 0 && (
        <div className="text-center mt-20 text-bone/30">
          <div className="text-6xl mb-4">☠️</div>
          <p className="text-lg">No listings yet.</p>
          <p className="text-sm mt-2">Use Search Center or submit a manual listing to get started.</p>
        </div>
      )}
    </div>
  )
}
