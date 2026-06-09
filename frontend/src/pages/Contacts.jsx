import { useEffect, useState } from 'react'
import api from '../api/client'

const ROLES = [
  { key: 'mechanic',    label: 'Mechanic',        icon: '🔧' },
  { key: 'detailer',   label: 'Detailer',         icon: '✨' },
  { key: 'insurance',  label: 'Insurance',        icon: '🛡️' },
  { key: 'tow',        label: 'Tow Service',      icon: '🚛' },
  { key: 'title_agent',label: 'Title Agent',      icon: '📋' },
  { key: 'buyer',      label: 'Buyer/Wholesaler', icon: '💰' },
  { key: 'inspector',  label: 'Inspector',        icon: '🔍' },
  { key: 'other',      label: 'Other',            icon: '👤' },
]

const EMPTY_FORM = {
  name: '', role: 'mechanic', company: '', phone: '',
  email: '', address: '', specialties: '', rate: '', rating: '', notes: '',
}

const STARS = [1, 2, 3, 4, 5]

export default function Contacts() {
  const [contacts, setContacts] = useState([])
  const [filterRole, setFilterRole] = useState('all')
  const [showForm, setShowForm] = useState(false)
  const [editId, setEditId] = useState(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const [saving, setSaving] = useState(false)

  const fetchContacts = () => {
    api.getContacts().then(res => setContacts(res.data))
  }

  useEffect(() => { fetchContacts() }, [])

  const openNew = () => { setForm(EMPTY_FORM); setEditId(null); setShowForm(true) }
  const openEdit = (c) => {
    setForm({
      name: c.name || '', role: c.role || 'mechanic', company: c.company || '',
      phone: c.phone || '', email: c.email || '', address: c.address || '',
      specialties: c.specialties || '', rate: c.rate || '',
      rating: c.rating || '', notes: c.notes || '',
    })
    setEditId(c.id)
    setShowForm(true)
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      const payload = { ...form, rating: form.rating ? Number(form.rating) : null }
      if (editId) {
        await api.updateContact(editId, payload)
      } else {
        await api.createContact(payload)
      }
      setShowForm(false)
      fetchContacts()
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this contact?')) return
    await api.deleteContact(id)
    fetchContacts()
  }

  const filtered = filterRole === 'all' ? contacts : contacts.filter(c => c.role === filterRole)
  const grouped = ROLES.reduce((acc, r) => {
    const items = filtered.filter(c => c.role === r.key)
    if (items.length) acc[r.key] = { ...r, items }
    return acc
  }, {})

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-gold font-bold text-xl tracking-wider">📞 CONTACTS</h1>
        <button onClick={openNew} className="btn-primary">+ Add Contact</button>
      </div>

      {/* Role filter */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => setFilterRole('all')}
          className={`text-xs px-3 py-1 rounded border ${filterRole === 'all' ? 'bg-gold text-obsidian border-gold' : 'border-border text-bone/50 hover:border-gold/40'}`}>
          All ({contacts.length})
        </button>
        {ROLES.map(r => {
          const count = contacts.filter(c => c.role === r.key).length
          if (!count) return null
          return (
            <button key={r.key} onClick={() => setFilterRole(r.key)}
              className={`text-xs px-3 py-1 rounded border ${filterRole === r.key ? 'bg-gold text-obsidian border-gold' : 'border-border text-bone/50 hover:border-gold/40'}`}>
              {r.icon} {r.label} ({count})
            </button>
          )
        })}
      </div>

      {/* Add/Edit Form */}
      {showForm && (
        <div className="bg-card border border-gold/30 rounded-lg p-5 space-y-4">
          <h2 className="text-gold text-sm font-bold tracking-wider">{editId ? 'EDIT CONTACT' : 'NEW CONTACT'}</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Name *</label>
              <input className="input-field w-full mt-1" placeholder="John Smith"
                value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Role *</label>
              <select className="input-field w-full mt-1" value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
                {ROLES.map(r => <option key={r.key} value={r.key}>{r.icon} {r.label}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Company</label>
              <input className="input-field w-full mt-1" placeholder="Smith Auto Repair"
                value={form.company} onChange={e => setForm(f => ({ ...f, company: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Phone</label>
              <input className="input-field w-full mt-1" placeholder="(555) 555-5555"
                value={form.phone} onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Email</label>
              <input className="input-field w-full mt-1" placeholder="john@email.com"
                value={form.email} onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Rate</label>
              <input className="input-field w-full mt-1" placeholder="$80/hr or flat $150"
                value={form.rate} onChange={e => setForm(f => ({ ...f, rate: e.target.value }))} />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-bone/40 uppercase tracking-wider">Address</label>
              <input className="input-field w-full mt-1" placeholder="123 Main St, Tampa FL"
                value={form.address} onChange={e => setForm(f => ({ ...f, address: e.target.value }))} />
            </div>
            <div>
              <label className="text-xs text-bone/40 uppercase tracking-wider">Rating</label>
              <div className="flex gap-1 mt-2">
                {STARS.map(s => (
                  <button key={s} type="button" onClick={() => setForm(f => ({ ...f, rating: s }))}
                    className={`text-xl ${Number(form.rating) >= s ? 'text-gold' : 'text-bone/20'}`}>★</button>
                ))}
              </div>
            </div>
            <div className="md:col-span-3">
              <label className="text-xs text-bone/40 uppercase tracking-wider">Specialties</label>
              <input className="input-field w-full mt-1" placeholder="Transmissions, AC, Japanese cars..."
                value={form.specialties} onChange={e => setForm(f => ({ ...f, specialties: e.target.value }))} />
            </div>
            <div className="md:col-span-3">
              <label className="text-xs text-bone/40 uppercase tracking-wider">Notes</label>
              <textarea className="input-field w-full mt-1 h-16 resize-none"
                placeholder="Fast turnaround, good prices, cash only..."
                value={form.notes} onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={handleSave} disabled={saving || !form.name} className="btn-primary">
              {saving ? 'Saving...' : '💾 Save'}
            </button>
            <button onClick={() => setShowForm(false)} className="btn-secondary">Cancel</button>
          </div>
        </div>
      )}

      {/* Contact Cards by Role */}
      {Object.values(grouped).map(group => (
        <div key={group.key}>
          <h2 className="text-bone/50 text-xs font-bold tracking-wider uppercase mb-3">
            {group.icon} {group.label}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {group.items.map(c => (
              <div key={c.id} className="bg-card border border-border rounded-lg p-4 hover:border-gold/30 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="text-bone font-semibold">{c.name}</div>
                    {c.company && <div className="text-bone/40 text-xs">{c.company}</div>}
                  </div>
                  {c.rating && (
                    <div className="text-gold text-xs">{'★'.repeat(c.rating)}{'☆'.repeat(5 - c.rating)}</div>
                  )}
                </div>
                <div className="space-y-1">
                  {c.phone && (
                    <a href={`tel:${c.phone}`} className="flex items-center gap-2 text-sm text-gold hover:underline">
                      📱 {c.phone}
                    </a>
                  )}
                  {c.email && (
                    <a href={`mailto:${c.email}`} className="flex items-center gap-2 text-xs text-bone/50 hover:text-gold">
                      ✉️ {c.email}
                    </a>
                  )}
                  {c.rate && <div className="text-xs text-profit-green">💵 {c.rate}</div>}
                  {c.specialties && <div className="text-xs text-bone/40 mt-1">{c.specialties}</div>}
                  {c.notes && <div className="text-xs text-bone/30 mt-1 italic">{c.notes}</div>}
                </div>
                <div className="flex gap-2 mt-3 pt-3 border-t border-border">
                  <button onClick={() => openEdit(c)} className="text-xs text-bone/40 hover:text-gold">✏️ Edit</button>
                  <button onClick={() => handleDelete(c.id)} className="text-xs text-bone/40 hover:text-crimson">🗑️ Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {contacts.length === 0 && !showForm && (
        <div className="text-center mt-20 text-bone/20">
          <div className="text-4xl mb-3">📞</div>
          <p>No contacts yet.</p>
          <p className="text-xs mt-1">Add your mechanic, detailer, insurance broker, and other service providers.</p>
        </div>
      )}
    </div>
  )
}
