import { useEffect, useState } from 'react'
import api from '../api/client'

export default function Settings() {
  const [settings, setSettings] = useState(null)
  const [form, setForm] = useState({})
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    api.getSettings().then(res => {
      setSettings(res.data)
      setForm({
        max_price: res.data.max_price,
        min_price: res.data.min_price,
        max_mileage: res.data.max_mileage,
        min_year: res.data.min_year,
        max_repair_budget: res.data.max_repair_budget,
        target_profit: res.data.target_profit,
        alert_score_threshold: res.data.alert_score_threshold,
        default_location: res.data.default_location,
        radius_miles: res.data.radius_miles,
        scan_frequency_minutes: res.data.scan_frequency_minutes,
      })
    })
  }, [])

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    try {
      await api.updateSettings({
        ...form,
        max_price: Number(form.max_price),
        min_price: Number(form.min_price),
        max_mileage: Number(form.max_mileage),
        min_year: Number(form.min_year),
        max_repair_budget: Number(form.max_repair_budget),
        target_profit: Number(form.target_profit),
        alert_score_threshold: Number(form.alert_score_threshold),
        radius_miles: Number(form.radius_miles),
        scan_frequency_minutes: Number(form.scan_frequency_minutes),
      })
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } finally {
      setSaving(false)
    }
  }

  if (!settings) return <div className="text-bone/50 text-center mt-20">Loading settings...</div>

  const fields = [
    { key: 'max_price', label: 'Max Price ($)', type: 'number' },
    { key: 'min_price', label: 'Min Price ($)', type: 'number' },
    { key: 'max_mileage', label: 'Max Mileage', type: 'number' },
    { key: 'min_year', label: 'Min Year', type: 'number' },
    { key: 'max_repair_budget', label: 'Max Repair Budget ($)', type: 'number' },
    { key: 'target_profit', label: 'Target Profit ($)', type: 'number' },
    { key: 'alert_score_threshold', label: 'Alert Score Threshold (0-100)', type: 'number' },
    { key: 'default_location', label: 'Default Location', type: 'text' },
    { key: 'radius_miles', label: 'Search Radius (miles)', type: 'number' },
    { key: 'scan_frequency_minutes', label: 'Scan Frequency (minutes)', type: 'number' },
  ]

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-gold font-bold text-xl tracking-wider">⚙ SETTINGS</h1>
      <form onSubmit={handleSave} className="bg-card border border-border rounded-lg p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {fields.map(f => (
            <div key={f.key}>
              <label className="text-xs text-bone/50 uppercase tracking-wider">{f.label}</label>
              <input
                type={f.type}
                className="input-field w-full mt-1"
                value={form[f.key] ?? ''}
                onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
              />
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4">
          <button type="submit" disabled={saving} className="btn-primary">
            {saving ? 'Saving...' : '💾 Save Settings'}
          </button>
          {saved && <span className="text-profit-green text-sm">✅ Saved</span>}
        </div>
      </form>

      <div className="bg-card border border-border rounded-lg p-6">
        <h2 className="text-gold text-xs font-bold tracking-wider uppercase mb-4">Discord Config</h2>
        <p className="text-bone/50 text-xs">
          Configure Discord in the backend <code className="text-gold">.env</code> file:
          <br /><br />
          <code className="text-bone">DISCORD_BOT_TOKEN=...</code><br />
          <code className="text-bone">DISCORD_WEBHOOK_URL=...</code><br />
          <code className="text-bone">DISCORD_GUILD_ID=...</code>
        </p>
      </div>
    </div>
  )
}
