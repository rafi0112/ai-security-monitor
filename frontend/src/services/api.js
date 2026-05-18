import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 10_000,
})

// ── Auth ─────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (username, password) =>
    api.post('/auth/login', { username, password }).then(r => r.data),
}

// ── Stats ────────────────────────────────────────────────────────────────────
export const statsAPI = {
  overview:     ()          => api.get('/stats/overview').then(r => r.data),
  timeline:     (hours=24)  => api.get(`/stats/timeline?hours=${hours}`).then(r => r.data),
  topIPs:       (limit=10)  => api.get(`/stats/top-ips?limit=${limit}`).then(r => r.data),
  distribution: (hours=24)  => api.get(`/stats/attack-distribution?hours=${hours}`).then(r => r.data),
}

// ── Logs ─────────────────────────────────────────────────────────────────────
export const logsAPI = {
  attempts: (page=1, limit=50, severity='all', attack='all') =>
    api.get(`/logs?page=${page}&limit=${limit}&severity=${severity}&attack=${attack}`).then(r => r.data),
  events: (limit=100) =>
    api.get(`/logs/events?limit=${limit}`).then(r => r.data),
}

// ── Alerts ───────────────────────────────────────────────────────────────────
export const alertsAPI = {
  list:    (resolved='false', severity='all') =>
    api.get(`/alerts?resolved=${resolved}&severity=${severity}`).then(r => r.data),
  ack:     (id) => api.patch(`/alerts/${id}/ack`).then(r => r.data),
  resolve: (id) => api.patch(`/alerts/${id}/resolve`).then(r => r.data),
  delete:  (id) => api.delete(`/alerts/${id}`).then(r => r.data),
}

// ── Simulate ─────────────────────────────────────────────────────────────────
export const simulateAPI = {
  bruteForce:    (attempts=20)  => api.post(`/simulate/brute-force?attempts=${attempts}`).then(r => r.data),
  sqli:          (attempts=10)  => api.post(`/simulate/sqli?attempts=${attempts}`).then(r => r.data),
  ddos:          (requests=50)  => api.post(`/simulate/ddos?requests=${requests}`).then(r => r.data),
  mixed:         ()             => api.post('/simulate/mixed').then(r => r.data),
  normalTraffic: (events=50)    => api.post(`/simulate/normal-traffic?events=${events}`).then(r => r.data),
  reset:         ()             => api.delete('/simulate/reset').then(r => r.data),
}

export default api
