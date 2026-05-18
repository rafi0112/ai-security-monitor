import { useState, useRef } from 'react'
import { statsAPI, logsAPI, alertsAPI } from '../services/api'
import { usePolling } from '../hooks/usePolling'
import StatCard        from '../components/dashboard/StatCard'
import AttemptsTable   from '../components/dashboard/AttemptsTable'
import SimulationPanel from '../components/dashboard/SimulationPanel'
import AlertsPanel     from '../components/alerts/AlertsPanel'
import { TimelineChart, AttackDistChart, TopIPsChart } from '../components/charts/Charts'
import clsx from 'clsx'

export default function DashboardPage() {
  const [timeRange,    setTimeRange]    = useState(24)
  const [tableFilters, setTableFilters] = useState({ severity: 'all', attack: 'all' })
  const [tablePage,    setTablePage]    = useState(1)

  // Store latest values in refs so polling closures always see current values
  const timeRangeRef    = useRef(timeRange)
  const tableFiltersRef = useRef(tableFilters)
  const tablePageRef    = useRef(tablePage)
  timeRangeRef.current    = timeRange
  tableFiltersRef.current = tableFilters
  tablePageRef.current    = tablePage

  // All polling hooks use refs internally — no remounts on state change
  const overview     = usePolling(() => statsAPI.overview(), 8_000)
  const timeline     = usePolling(() => statsAPI.timeline(timeRangeRef.current), 15_000, [timeRange])
  const distribution = usePolling(() => statsAPI.distribution(timeRangeRef.current), 15_000, [timeRange])
  const topIPs       = usePolling(() => statsAPI.topIPs(10), 15_000)
  const attempts     = usePolling(
    () => logsAPI.attempts(tablePageRef.current, 50, tableFiltersRef.current.severity, tableFiltersRef.current.attack),
    8_000,
    [tablePage, tableFilters]
  )
  const alerts = usePolling(() => alertsAPI.list('false', 'all'), 6_000)

  // Called after simulation — refetch all without remounting
  const handleSimulated = () => {
    setTimeout(() => {
      overview.refetch()
      timeline.refetch()
      distribution.refetch()
      topIPs.refetch()
      attempts.refetch()
      alerts.refetch()
    }, 1200)
  }

  const ov = overview.data || {}

  return (
    <div className="max-w-screen-2xl mx-auto px-4 py-6 space-y-6">

      {/* ── Header ────────────────────────────────────────────────── */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1" style={{ fontFamily: 'Orbitron, monospace' }}>
            SECURITY DASHBOARD
          </h1>
          <p className="text-cyber-muted text-sm font-mono">
            Real-time AI-powered threat monitoring · Last {timeRange}h
          </p>
        </div>
        <div className="flex items-center gap-1 bg-cyber-surface rounded-lg p-1 border border-cyber-border">
          {[6, 24, 48, 168].map(h => (
            <button key={h}
              onClick={() => { setTimeRange(h); setTimeout(() => { timeline.refetch(); distribution.refetch() }, 100) }}
              className={clsx('text-xs font-mono px-3 py-1.5 rounded-md transition-all',
                timeRange === h ? 'bg-cyber-accent text-cyber-bg font-bold' : 'text-cyber-muted hover:text-white'
              )}>
              {h === 168 ? '7d' : `${h}h`}
            </button>
          ))}
        </div>
      </div>

      {/* ── Stat Cards ────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <StatCard icon="🎯" label="Total Attempts" value={ov.total_attempts ?? '—'} sub="Last 24h"          color="accent"  loading={overview.loading} />
        <StatCard icon="✅" label="Successful"      value={ov.successful ?? '—'}     sub={ov.success_rate != null ? `${ov.success_rate}% rate` : ''} color="green" loading={overview.loading} />
        <StatCard icon="❌" label="Failed"           value={ov.failed ?? '—'}                                color="red"     loading={overview.loading} />
        <StatCard icon="⚔️" label="Attacks"         value={ov.attacks ?? '—'}        sub={ov.attack_rate != null ? `${ov.attack_rate}% of traffic` : ''} color="orange" loading={overview.loading} />
        <StatCard icon="🚨" label="Active Alerts"   value={ov.active_alerts ?? '—'}  sub={ov.critical_alerts ? `${ov.critical_alerts} critical` : 'all clear'} color={ov.critical_alerts > 0 ? 'red' : 'yellow'} loading={overview.loading} />
        <StatCard icon="🚫" label="Blocked IPs"     value={ov.blocked_ips ?? '—'}    sub={`${ov.unique_ips ?? 0} unique seen`} color="purple" loading={overview.loading} />
      </div>

      {/* ── Charts Row ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-2 card-glow">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="section-title">Traffic Timeline</h2>
              <p className="text-cyber-muted text-xs mt-0.5 font-mono">Logins, failures &amp; attacks over time</p>
            </div>
            <div className="flex items-center gap-3 text-xs font-mono">
              <span className="flex items-center gap-1.5 text-cyber-accent"><span className="w-3 h-0.5 bg-cyber-accent inline-block rounded" /> Total</span>
              <span className="flex items-center gap-1.5 text-red-400"><span className="w-3 h-0.5 bg-red-400 inline-block rounded" /> Attacks</span>
              <span className="flex items-center gap-1.5 text-green-400"><span className="w-3 h-0.5 bg-green-400 inline-block rounded" /> Success</span>
            </div>
          </div>
          <TimelineChart data={timeline.data?.timeline ?? []} />
        </div>

        <div className="card-glow">
          <div className="mb-4">
            <h2 className="section-title">Attack Types</h2>
            <p className="text-cyber-muted text-xs mt-0.5 font-mono">Distribution by category</p>
          </div>
          <AttackDistChart data={distribution.data?.distribution ?? []} />
        </div>
      </div>

      {/* ── Alerts + Top IPs ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <AlertsPanel
          alerts={alerts.data?.alerts ?? []}
          onRefresh={alerts.refetch}
          loading={alerts.loading}
        />

        <div className="card-glow">
          <div className="mb-4">
            <h2 className="section-title">Top IP Addresses</h2>
            <p className="text-cyber-muted text-xs mt-0.5 font-mono">Most active IPs — attacks highlighted</p>
          </div>
          <TopIPsChart data={topIPs.data?.top_ips ?? []} />
          <div className="mt-3 space-y-1 max-h-48 overflow-y-auto">
            {(topIPs.data?.top_ips ?? []).slice(0, 8).map((ip, i) => (
              <div key={ip.ip} className="flex items-center gap-3 text-xs font-mono py-1.5 border-b border-cyber-border/30 last:border-0">
                <span className="text-cyber-muted w-4">{i + 1}</span>
                <span className={clsx('flex-1 truncate', ip.blocked ? 'text-red-400' : 'text-cyber-accent')}>
                  {ip.blocked && <span className="mr-1">🚫</span>}{ip.ip}
                </span>
                <span className="text-cyber-muted">{ip.total} req</span>
                {ip.attacks > 0 && <span className="text-red-400">{ip.attacks} atk</span>}
                <span className={clsx('px-1.5 py-0.5 rounded border text-xs',
                  ip.max_severity === 'critical' ? 'badge-critical' :
                  ip.max_severity === 'high'     ? 'badge-high'     :
                  ip.max_severity === 'medium'   ? 'badge-medium'   : 'badge-low'
                )}>{((ip.max_risk ?? 0) * 100).toFixed(0)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Attack Simulator ──────────────────────────────────────── */}
      <SimulationPanel onSimulated={handleSimulated} />

      {/* ── Attempts Table ────────────────────────────────────────── */}
      <AttemptsTable
        attempts={attempts.data?.attempts ?? []}
        total={attempts.data?.total ?? 0}
        loading={attempts.loading}
        onFilterChange={(f) => { setTableFilters(f); setTablePage(1) }}
      />

      {/* ── Pagination ────────────────────────────────────────────── */}
      {(attempts.data?.pages ?? 0) > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            disabled={tablePage === 1}
            onClick={() => setTablePage(p => p - 1)}
            className="btn-ghost py-1.5 px-3 text-xs disabled:opacity-30"
          >← Prev</button>
          <span className="text-cyber-muted text-xs font-mono">
            Page {tablePage} of {attempts.data.pages}
          </span>
          <button
            disabled={tablePage === attempts.data.pages}
            onClick={() => setTablePage(p => p + 1)}
            className="btn-ghost py-1.5 px-3 text-xs disabled:opacity-30"
          >Next →</button>
        </div>
      )}

      {/* ── Footer ────────────────────────────────────────────────── */}
      <div className="border-t border-cyber-border pt-4 flex items-center justify-between text-cyber-muted text-xs font-mono">
        <span>AI Security Monitor · Phase 1 · IsolationForest + Rule Engine</span>
        <span>Avg Risk: <span className="text-cyber-accent">
          {ov.avg_risk_score != null ? `${(ov.avg_risk_score * 100).toFixed(1)}%` : '—'}
        </span></span>
      </div>
    </div>
  )
}
