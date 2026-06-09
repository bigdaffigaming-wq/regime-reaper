import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || '/api'
const ROLE = import.meta.env.VITE_USER_ROLE || 'owner'

const client = axios.create({
  baseURL: BASE,
  headers: { 'x-user-role': ROLE },
})

export const api = {
  // Health
  health: () => client.get('/health'),
  getCredits: () => client.get('/credits'),

  // Listings
  getListings: (params = {}) => client.get('/listings', { params }),
  getListing: (id) => client.get(`/listings/${id}`),
  createListing: (data) => client.post('/listings', data),
  updateListing: (id, data) => client.patch(`/listings/${id}`, data),
  deleteListing: (id) => client.delete(`/listings/${id}`),
  watchlistListing: (id) => client.post(`/listings/${id}/watchlist`),
  rejectListing: (id) => client.post(`/listings/${id}/reject`),
  enrichListing: (id) => client.post(`/listings/${id}/enrich`),

  // Analysis
  analyzeListing: (id) => client.post(`/analysis/${id}`),
  getAnalysis: (id) => client.get(`/analysis/${id}`),
  analyzeManual: (data) => client.post('/analysis/manual', data),

  // Search
  searchFacebook: (params) => client.post('/search/facebook', params),
  searchCraigslist: (params) => client.post('/search/craigslist', params),
  searchAll: (params) => client.post('/search', params),

  // Inventory
  getInventory: (params = {}) => client.get('/inventory', { params }),
  getInventoryItem: (id) => client.get(`/inventory/${id}`),
  createInventory: (listingId, data) => client.post(`/inventory/from-listing/${listingId}`, data),
  updateInventory: (id, data) => client.patch(`/inventory/${id}`, data),
  markSold: (id, salePrice) => client.post(`/inventory/${id}/mark-sold`, { sale_price: salePrice }),

  // Settings
  getSettings: () => client.get('/settings'),
  updateSettings: (data) => client.patch('/settings', data),

  // Repairs
  getRepairs: () => client.get('/repairs'),

  // Audit
  getAuditLogs: (params = {}) => client.get('/audit', { params }),

  // Contacts
  getContacts: (params = {}) => client.get('/contacts', { params }),
  createContact: (data) => client.post('/contacts', data),
  updateContact: (id, data) => client.patch(`/contacts/${id}`, data),
  deleteContact: (id) => client.delete(`/contacts/${id}`),

  // Scanner
  getScanStatus: () => client.get('/scan/status'),
  startScan: (interval = 30) => client.post(`/scan/start?interval_minutes=${interval}`),
  stopScan: () => client.post('/scan/stop'),
  scanNow: () => client.post('/scan/now'),
  setScanInterval: (minutes) => client.patch(`/scan/interval?minutes=${minutes}`),
}

export default api
