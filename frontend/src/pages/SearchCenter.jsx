import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../api/client'
import DealCard from '../components/DealCard'
import SourceBadge from '../components/SourceBadge'
import VerdictBadge from '../components/VerdictBadge'
import ScoreBadge from '../components/ScoreBadge'

function SearchResultCard({ listing: l, onNavigate }) {
  const [analysis, setAnalysis] = useState(null)
  const [analyzing, setAnalyzing] = useState(false)

  const quickAnalyze = async (e) => {
    e.stopPropagation()
    setAnalyzing(true)
    try {
      const res = await api.analyzeListing(l.id)
      setAnalysis(res.data)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="bg-card border border-border rounded-lg overflow-hidden hover:border-gold/50 transition-colors">
      {l.image_url ? (
        <img src={l.image_url} alt={l.title} className="w-full h-40 object-cover cursor-pointer"
          onClick={onNavigate} onError={e => { e.target.style.display = 'none' }} />
      ) : (
        <div className="w-full h-40 bg-obsidian flex items-center justify-center text-bone/10 text-4xl cursor-pointer" onClick={onNavigate}>☠</div>
      )}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-1 cursor-pointer" onClick={onNavigate}>
          <div className="text-bone font-semibold text-sm truncate flex-1">{l.title}</div>
          <SourceBadge source={l.source} />
        </div>
        <div className="text-gold font-bold text-base">${(l.price || 0).toLocaleString()}</div>
        {l.mileage && <div className="text-bone/50 text-xs mt-0.5">{l.mileage.toLocaleString()} mi</div>}
        <div className="text-bone/30 text-xs mt-0.5">{l.location}</div>

        {analysis ? (
          <div className="mt-3 pt-3 border-t border-border space-y-2">
            <div className="flex items-center justify-between">
              <ScoreBadge score={analysis.deal_score} />
              <VerdictBadge verdict={analysis.verdict} />
            </div>
            <div className={`text-sm font-bold ${analysis.expected_profit >= 0 ? 'text-profit-green' : 'text-crimson'}`}>
              Profit: ${(analysis.expected_profit || 0).toLocaleString(undefined, { maximumFractionDigits: 0 })}
            </div>
            <div className="text-bone/40 text-xs">Est. Repairs: ${(analysis.estimated_repair_cost || 0).toLocaleString()}</div>
            <button onClick={onNavigate} className="text-gold text-xs hover:underline">View full analysis →</button>
          </div>
        ) : (
          <div className="mt-3 flex gap-2">
            <button onClick={quickAnalyze} disabled={analyzing}
              className="flex-1 text-xs py-1.5 bg-gold/10 border border-gold/30 text-gold rounded hover:bg-gold/20 transition-colors disabled:opacity-50">
              {analyzing ? 'Analyzing...' : '☠️ Quick Analyze'}
            </button>
            <button onClick={onNavigate} className="text-xs px-3 py-1.5 border border-border text-bone/40 rounded hover:border-gold/40 hover:text-gold transition-colors">
              Open →
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const SOURCES = [
  { key: 'facebook',    label: 'Facebook',    live: true  },
  { key: 'craigslist',  label: 'Craigslist',  live: true  },
  { key: 'autotempest', label: 'AutoTempest', live: false },
  { key: 'cars_com',    label: 'Cars.com',    live: false },
]

const DEFAULT_FORM = {
  query: '',
  location: 'Tampa, FL',
  radius: 75,
  max_price: 2500,
  min_year: '',
  max_mileage: 200000,
}

export default function SearchCenter() {
  const [form, setForm] = useState(DEFAULT_FORM)
  const [enabledSources, setEnabledSources] = useState(['facebook'])
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [manualMode, setManualMode] = useState(false)
  const [manualForm, setManualForm] = useState({
    title: '', price: '', mileage: '', year: '', make: '',
    model: '', location: '', description: '', title_status: 'clean', url: '',
  })
  const navigate = useNavigate()

  const toggleSource = (key) => {
    const src = SOURCES.find(s => s.key === key)
    if (!src.live) return
    setEnabledSources(prev =>
      prev.includes(key) ? prev.filter(s => s !== key) : [...prev, key]
    )
  }

  const handleSearch = async (e) => {
    e.preventDefault()
    if (enabledSources.length === 0) {
      setError('Select at least one source.')
      return
    }
    setLoading(true)
    setError(null)
    setResults([])
    try {
      const res = await api.searchAll({
        query: form.query,
        location: form.location,
        radius: Number(form.radius),
        max_price: Number(form.max_price),
        min_year: form.min_year ? Number(form.min_year) : undefined,
        max_mileage: Number(form.max_mileage),
        sources: enabledSources,
      })
      setResults(res.data.listings || [])
      if ((res.data.listings || []).length === 0) {
        setError('No results found. Try a broader search or different keywords.')
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed. Check backend is running.')
    } finally {
      setLoading(false)
    }
  }

  const handleManualSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const createRes = await api.createListing({
        ...manualForm,
        price: Number(manualForm.price),
        mileage: manualForm.mileage ? Number(manualForm.mileage) : undefined,
        year: manualForm.year ? Number(manualForm.year) : undefined,
        source: 'manual',
      })
      await api.analyzeListing(createRes.data.id)
      navigate(`/listing/${createRes.data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit listing')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <h1 className="text-gold font-bold text-xl tracking-wider">🔍 SEARCH CENTER</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setManualMode(false)}
            className={`text-xs px-3 py-1 rounded border transition-colors ${!manualMode ? 'bg-gold text-obsidian border-gold' : 'border-border text-bone/50 hover:border-gold/50'}`}
          >
            Source Search
          </button>
          <button
            onClick={() => setManualMode(true)}
            className={`text-xs px-3 py-1 rounded border transition-colors ${manualMode ? 'bg-gold text-obsidian border-gold' : 'border-border text-bone/50 hover:border-gold/50'}`}
          >
            Manual Entry
          </button>
        </div>
      </div>

      {!manualMode ? (
        <form onSubmit={handleSearch} className="bg-card border border-border rounded-lg p-5 space-y-5">

          {/* Source toggles */}
          <div>
            <label className="text-xs text-bone/50 uppercase tracking-wider block mb-2">Sources</label>
            <div className="flex gap-3 flex-wrap">
              {SOURCES.map(src => {
                const active = enabledSources.includes(src.key)
                return (
                  <button
                    key={src.key}
                    type="button"
                    onClick={() => toggleSource(src.key)}
                    className={`px-3 py-1.5 rounded border text-xs font-bold tracking-wider transition-colors relative
                      ${!src.live ? 'opacity-30 cursor-not-allowed border-border text-bone/30' :
                        active ? 'border-gold bg-gold/10 text-gold' : 'border-border text-bone/50 hover:border-gold/40'}`}
                  >
                    {src.label}
                    {!src.live && (
                      <span className="absolute -top-2 -right-1 text-[9px] text-amber bg-obsidian px-1 rounded">
                        Phase 2
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
            <p className="text-bone/30 text-xs mt-2">Craigslist, AutoTempest, Cars.com coming in Phase 2.</p>
          </div>

          {/* Search fields */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="col-span-2 md:col-span-3">
              <label className="text-xs text-bone/50 uppercase tracking-wider">Search Query *</label>
              <input
                className="input-field w-full mt-1"
                placeholder="Toyota Camry"
                value={form.query}
                onChange={e => setForm(f => ({ ...f, query: e.target.value }))}
                required
              />
            </div>
            {[
              { key: 'location',    label: 'Location',        placeholder: 'Tampa, FL'  },
              { key: 'radius',      label: 'Radius (miles)',   placeholder: '75'         },
              { key: 'max_price',   label: 'Max Price ($)',    placeholder: '2500'       },
              { key: 'min_year',    label: 'Min Year',         placeholder: '2005'       },
              { key: 'max_mileage', label: 'Max Mileage',      placeholder: '200000'     },
            ].map(f => (
              <div key={f.key}>
                <label className="text-xs text-bone/50 uppercase tracking-wider">{f.label}</label>
                <input
                  className="input-field w-full mt-1"
                  placeholder={f.placeholder}
                  value={form[f.key]}
                  onChange={e => setForm(prev => ({ ...prev, [f.key]: e.target.value }))}
                />
              </div>
            ))}
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full text-sm py-3">
            {loading ? 'Searching...' : '☠️ SEARCH'}
          </button>

          {error && <div className="text-crimson text-sm">{error}</div>}
        </form>
      ) : (
        /* Manual Entry Form */
        <form onSubmit={handleManualSubmit} className="bg-card border border-border rounded-lg p-5 space-y-4">
          <h2 className="text-gold text-sm font-bold tracking-wider">MANUAL LISTING ENTRY</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="col-span-2 md:col-span-3">
              <label className="text-xs text-bone/50 uppercase tracking-wider">Listing Title *</label>
              <input className="input-field w-full mt-1" placeholder="2011 Toyota Camry LE" value={manualForm.title}
                onChange={e => setManualForm(f => ({ ...f, title: e.target.value }))} required />
            </div>
            {[
              { key: 'price',    label: 'Price ($)',  placeholder: '2400',      required: true },
              { key: 'mileage',  label: 'Mileage',    placeholder: '176000'                   },
              { key: 'year',     label: 'Year',       placeholder: '2011'                     },
              { key: 'make',     label: 'Make',       placeholder: 'Toyota'                   },
              { key: 'model',    label: 'Model',      placeholder: 'Camry'                    },
              { key: 'location', label: 'Location',   placeholder: 'Tampa, FL'                },
            ].map(f => (
              <div key={f.key}>
                <label className="text-xs text-bone/50 uppercase tracking-wider">{f.label}</label>
                <input className="input-field w-full mt-1" placeholder={f.placeholder} required={f.required}
                  value={manualForm[f.key]} onChange={e => setManualForm(p => ({ ...p, [f.key]: e.target.value }))} />
              </div>
            ))}
            <div>
              <label className="text-xs text-bone/50 uppercase tracking-wider">Title Status</label>
              <select className="input-field w-full mt-1" value={manualForm.title_status}
                onChange={e => setManualForm(f => ({ ...f, title_status: e.target.value }))}>
                <option value="clean">Clean</option>
                <option value="salvage">Salvage</option>
                <option value="rebuilt">Rebuilt</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-bone/50 uppercase tracking-wider">Listing URL</label>
              <input className="input-field w-full mt-1" placeholder="https://..." value={manualForm.url}
                onChange={e => setManualForm(f => ({ ...f, url: e.target.value }))} />
            </div>
            <div className="col-span-2 md:col-span-3">
              <label className="text-xs text-bone/50 uppercase tracking-wider">Description / Notes</label>
              <textarea className="input-field w-full mt-1 h-24 resize-none"
                placeholder="Cold AC, clean title, must sell moving, some rust on rocker panels..."
                value={manualForm.description}
                onChange={e => setManualForm(f => ({ ...f, description: e.target.value }))} />
            </div>
          </div>
          <button type="submit" disabled={loading} className="btn-primary w-full text-sm py-3">
            {loading ? 'Analyzing...' : '☠️ SUBMIT & ANALYZE'}
          </button>
          {error && <div className="text-crimson text-sm">{error}</div>}
        </form>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-gold text-sm font-bold tracking-wider uppercase">{results.length} Results</h2>
            <div className="flex gap-2">
              {[...new Set(results.map(r => r.source))].map(src => (
                <SourceBadge key={src} source={src} />
              ))}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((l, i) => (
              <SearchResultCard key={i} listing={l} onNavigate={() => navigate(`/listing/${l.id}`)} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
