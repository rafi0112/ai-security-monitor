import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import { statsAPI } from '../../services/api'
import clsx from 'clsx'

const NAV = [
  { to: '/dashboard', icon: '⬡', label: 'Dashboard',  end: true },
]

export default function Layout() {
  const navigate = useNavigate()
  const [time, setTime] = useState(new Date())
  const [criticalCount, setCriticalCount] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const fetch = async () => {
      try {
        const ov = await statsAPI.overview()
        setCriticalCount(ov.critical_alerts || 0)
      } catch {}
    }
    fetch()
    const t = setInterval(fetch, 10000)
    return () => clearInterval(t)
  }, [])

  return (
    <div className="min-h-screen bg-cyber-bg flex flex-col">
      {/* ── Top Bar ─────────────────────────────────────────────────── */}
      <header className="border-b border-cyber-border bg-cyber-surface/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="flex items-center justify-between px-6 h-14">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-cyber-accent/20 border border-cyber-accent/40 flex items-center justify-center">
              <span className="text-sm">🛡️</span>
            </div>
            <span className="font-bold text-white text-sm" style={{ fontFamily: 'Orbitron, monospace' }}>
              AI<span className="text-cyber-accent">SEC</span>MON
            </span>
            <span className="text-cyber-muted text-xs ml-1 hidden sm:block">v1.0.0</span>
          </div>

          {/* Nav */}
          <nav className="flex items-center gap-1">
            {NAV.map(n => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.end}
                className={({ isActive }) => clsx(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-mono transition-all',
                  isActive
                    ? 'bg-cyber-accent/15 text-cyber-accent border border-cyber-accent/30'
                    : 'text-cyber-muted hover:text-white hover:bg-cyber-border/30'
                )}
              >
                <span>{n.icon}</span>
                <span>{n.label}</span>
              </NavLink>
            ))}
          </nav>

          {/* Right: status + clock */}
          <div className="flex items-center gap-4">
            {criticalCount > 0 && (
              <div className="flex items-center gap-2 bg-red-900/30 border border-red-700/50 rounded-lg px-3 py-1">
                <div className="pulse-dot bg-red-500" />
                <span className="text-red-400 text-xs font-mono font-bold">
                  {criticalCount} CRITICAL
                </span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <div className="pulse-dot bg-cyber-green" />
              <span className="text-cyber-muted text-xs font-mono hidden sm:block">LIVE</span>
            </div>
            <div className="text-cyber-muted text-xs font-mono hidden md:block">
              {time.toLocaleTimeString()}
            </div>
            <button
              onClick={() => navigate('/login')}
              className="text-xs text-cyber-muted hover:text-cyber-accent font-mono transition-colors"
            >
              LOGIN DEMO →
            </button>
          </div>
        </div>
      </header>

      {/* ── Accent line ─────────────────────────────────────────────── */}
      <div className="accent-line" />

      {/* ── Page Content ────────────────────────────────────────────── */}
      <main className="flex-1 bg-cyber-grid">
        <Outlet />
      </main>
    </div>
  )
}
