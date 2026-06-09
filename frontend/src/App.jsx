import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import SearchCenter from './pages/SearchCenter'
import Watchlist from './pages/Watchlist'
import Inventory from './pages/Inventory'
import Settings from './pages/Settings'
import Analytics from './pages/Analytics'
import ListingDetail from './pages/ListingDetail'
import Archive from './pages/Archive'
import Contacts from './pages/Contacts'

const NAV = [
  { to: '/', label: '☠ DASHBOARD' },
  { to: '/search', label: '🔍 SEARCH' },
  { to: '/watchlist', label: '👁 WATCHLIST' },
  { to: '/archive', label: '📁 ARCHIVE' },
  { to: '/inventory', label: '📦 INVENTORY' },
  { to: '/contacts', label: '📞 CONTACTS' },
  { to: '/analytics', label: '📊 ANALYTICS' },
  { to: '/settings', label: '⚙ SETTINGS' },
]

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-obsidian">
        {/* Top Nav */}
        <nav className="border-b border-border px-6 py-3 flex items-center gap-8">
          <span className="text-gold font-bold text-lg tracking-widest">☠️ REGIME REAPER</span>
          <div className="flex gap-4 ml-4">
            {NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === '/'}
                className={({ isActive }) =>
                  `text-xs tracking-wider px-3 py-1 rounded transition-colors ${
                    isActive
                      ? 'bg-gold text-obsidian font-bold'
                      : 'text-bone hover:text-gold'
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </div>
          <div className="ml-auto text-xs text-bone/50">Harvest Value. Reap Profit.</div>
        </nav>

        {/* Page Content */}
        <main className="flex-1 p-6">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<SearchCenter />} />
            <Route path="/watchlist" element={<Watchlist />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/archive" element={<Archive />} />
            <Route path="/contacts" element={<Contacts />} />
            <Route path="/listing/:id" element={<ListingDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
