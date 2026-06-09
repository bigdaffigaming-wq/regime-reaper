import { useEffect, useState } from 'react'
import api from '../api/client'
import ProfitBox from '../components/ProfitBox'

const STATUS_COLUMNS = [
  'bought', 'repairing', 'cleaning', 'ready_to_list', 'listed', 'pending_sale', 'sold',
]

const STATUS_COLORS = {
  bought: 'text-blue-400',
  repairing: 'text-amber',
  cleaning: 'text-purple-400',
  ready_to_list: 'text-gold',
  listed: 'text-profit-green',
  pending_sale: 'text-orange-400',
  sold: 'text-bone/50',
}

export default function Inventory() {
  const [inventory, setInventory] = useState([])
  const [listings, setListings] = useState({})
  const [selling, setSelling] = useState(null)
  const [salePrice, setSalePrice] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getInventory().then(res => {
      setInventory(res.data)
      res.data.forEach(async inv => {
        try {
          const l = await api.getListing(inv.listing_id)
          setListings(prev => ({ ...prev, [inv.id]: l.data }))
        } catch {}
      })
    }).finally(() => setLoading(false))
  }, [])

  const updateStatus = async (invId, status) => {
    await api.updateInventory(invId, { inventory_status: status })
    setInventory(prev => prev.map(i => i.id === invId ? { ...i, inventory_status: status } : i))
  }

  const handleSold = async (invId) => {
    if (!salePrice) return
    const res = await api.markSold(invId, Number(salePrice))
    setInventory(prev => prev.map(i => i.id === invId ? res.data : i))
    setSelling(null)
    setSalePrice('')
  }

  const totalProfit = inventory.filter(i => i.inventory_status === 'sold').reduce((s, i) => s + (i.net_profit || 0), 0)
  const active = inventory.filter(i => i.inventory_status !== 'sold')
  const sold = inventory.filter(i => i.inventory_status === 'sold')

  if (loading) return <div className="text-bone/50 text-center mt-20">Loading inventory...</div>

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-gold font-bold text-xl tracking-wider">📦 INVENTORY</h1>
        <div className="text-right">
          <div className="text-bone/50 text-xs">Total Realized Profit</div>
          <div className={`text-xl font-bold ${totalProfit >= 0 ? 'text-profit-green' : 'text-crimson'}`}>
            ${totalProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-card border border-border rounded p-3">
          <div className="text-bone/50 text-xs">Active</div>
          <div className="text-xl font-bold text-amber">{active.length}</div>
        </div>
        <div className="bg-card border border-border rounded p-3">
          <div className="text-bone/50 text-xs">Sold</div>
          <div className="text-xl font-bold text-profit-green">{sold.length}</div>
        </div>
        <div className="bg-card border border-border rounded p-3">
          <div className="text-bone/50 text-xs">Avg Profit</div>
          <div className="text-xl font-bold text-profit-green">
            ${sold.length > 0 ? (totalProfit / sold.length).toLocaleString(undefined, { maximumFractionDigits: 0 }) : '0'}
          </div>
        </div>
        <div className="bg-card border border-border rounded p-3">
          <div className="text-bone/50 text-xs">Avg Days Held</div>
          <div className="text-xl font-bold text-gold">
            {sold.length > 0 ? Math.round(sold.reduce((s, i) => s + (i.days_held || 0), 0) / sold.length) : '—'}
          </div>
        </div>
      </div>

      {/* Active Inventory */}
      {active.length > 0 && (
        <section>
          <h2 className="text-gold text-sm font-bold tracking-wider uppercase mb-3">Active</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {active.map(inv => {
              const listing = listings[inv.id]
              return (
                <div key={inv.id} className="bg-card border border-border rounded-lg p-4 space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-bone font-semibold text-sm">{listing?.title || `Listing #${inv.listing_id}`}</div>
                      <div className={`text-xs font-bold mt-0.5 ${STATUS_COLORS[inv.inventory_status] || 'text-bone/50'}`}>
                        {inv.inventory_status.toUpperCase().replace('_', ' ')}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-bone/50 text-xs">Invested</div>
                      <div className="text-gold font-bold">${inv.total_invested.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
                    </div>
                  </div>

                  <div className="flex gap-2 flex-wrap">
                    {STATUS_COLUMNS.filter(s => s !== inv.inventory_status && s !== 'sold').map(s => (
                      <button key={s} onClick={() => updateStatus(inv.id, s)}
                        className="text-xs px-2 py-0.5 bg-white/5 hover:bg-gold/20 text-bone/50 hover:text-gold rounded">
                        → {s.replace('_', ' ')}
                      </button>
                    ))}
                    <button onClick={() => setSelling(inv.id)}
                      className="text-xs px-2 py-0.5 bg-profit-green/10 hover:bg-profit-green/20 text-profit-green rounded font-bold">
                      ✅ SOLD
                    </button>
                  </div>

                  {selling === inv.id && (
                    <div className="flex gap-2">
                      <input
                        type="number"
                        className="input-field flex-1"
                        placeholder="Sale price ($)"
                        value={salePrice}
                        onChange={e => setSalePrice(e.target.value)}
                      />
                      <button onClick={() => handleSold(inv.id)} className="btn-primary px-3 text-xs">Save</button>
                      <button onClick={() => setSelling(null)} className="text-xs px-2 text-bone/50">✕</button>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* Sold */}
      {sold.length > 0 && (
        <section>
          <h2 className="text-gold text-sm font-bold tracking-wider uppercase mb-3">Sold</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sold.map(inv => {
              const listing = listings[inv.id]
              return (
                <div key={inv.id} className="bg-card border border-border rounded-lg p-4 opacity-70 hover:opacity-100 transition-opacity">
                  <div className="text-bone font-semibold text-sm mb-2">{listing?.title || `Listing #${inv.listing_id}`}</div>
                  <ProfitBox profit={inv.net_profit} roi={inv.roi_percent} />
                  <div className="mt-2 flex justify-between text-xs text-bone/50">
                    <span>Invested: ${inv.total_invested.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
                    <span>{inv.days_held || '?'} days</span>
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {inventory.length === 0 && (
        <div className="text-center mt-20 text-bone/30">
          <p className="text-lg">No inventory yet.</p>
          <p className="text-sm mt-2">Buy a deal from the Listing Detail page to start tracking.</p>
        </div>
      )}
    </div>
  )
}
