import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import api from '../api/client'

export default function Analytics() {
  const [inventory, setInventory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getInventory().then(res => setInventory(res.data)).finally(() => setLoading(false))
  }, [])

  const sold = inventory.filter(i => i.inventory_status === 'sold')

  const totalProfit = sold.reduce((s, i) => s + (i.net_profit || 0), 0)
  const avgProfit = sold.length ? totalProfit / sold.length : 0
  const avgROI = sold.length ? sold.reduce((s, i) => s + (i.roi_percent || 0), 0) / sold.length : 0
  const avgDays = sold.length ? sold.reduce((s, i) => s + (i.days_held || 0), 0) / sold.length : 0

  const stats = [
    { label: 'Total Profit', value: `$${totalProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: totalProfit >= 0 ? 'text-profit-green' : 'text-crimson' },
    { label: 'Avg Profit / Deal', value: `$${avgProfit.toLocaleString(undefined, { maximumFractionDigits: 0 })}`, color: 'text-gold' },
    { label: 'Avg ROI', value: `${avgROI.toFixed(1)}%`, color: 'text-amber' },
    { label: 'Avg Days Held', value: `${Math.round(avgDays)}`, color: 'text-blue-400' },
    { label: 'Total Flips', value: sold.length, color: 'text-bone' },
  ]

  const profitData = sold.map((i, idx) => ({
    name: `#${i.id}`,
    profit: Math.round(i.net_profit || 0),
  }))

  if (loading) return <div className="text-bone/50 text-center mt-20">Loading analytics...</div>

  return (
    <div className="space-y-6">
      <h1 className="text-gold font-bold text-xl tracking-wider">📊 ANALYTICS</h1>

      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {stats.map(s => (
          <div key={s.label} className="bg-card border border-border rounded-lg p-4">
            <div className="text-bone/50 text-xs uppercase tracking-wider">{s.label}</div>
            <div className={`text-xl font-bold mt-1 ${s.color}`}>{s.value}</div>
          </div>
        ))}
      </div>

      {profitData.length > 0 ? (
        <div className="bg-card border border-border rounded-lg p-5">
          <h2 className="text-gold text-xs font-bold tracking-wider uppercase mb-4">Profit Per Deal</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={profitData}>
              <XAxis dataKey="name" stroke="#E8E4D855" tick={{ fontSize: 10 }} />
              <YAxis stroke="#E8E4D855" tick={{ fontSize: 10 }} tickFormatter={v => `$${v}`} />
              <Tooltip
                contentStyle={{ background: '#1A1A1A', border: '1px solid #2A2A2A', color: '#E8E4D8' }}
                formatter={v => [`$${v}`, 'Profit']}
              />
              <Bar dataKey="profit">
                {profitData.map((entry, i) => (
                  <Cell key={i} fill={entry.profit >= 0 ? '#6AFF4F' : '#C1121F'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="text-center mt-10 text-bone/30">
          <p>No sold vehicles yet. Data will appear after your first flip.</p>
        </div>
      )}
    </div>
  )
}
