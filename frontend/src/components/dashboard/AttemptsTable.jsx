import { useState } from 'react'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'

const SEV_BADGE = {
  critical: 'badge-critical',
  high:     'badge-high',
  medium:   'badge-medium',
  low:      'badge-low',
}

const ATTACK_MAP = {
  brute_force:         { label: 'Brute Force',    icon: '🔨', color: 'text-orange-400' },
  sqli:                { label: 'SQL Injection',   icon: '💉', color: 'text-red-400'    },
  xss:                 { label: 'XSS',             icon: '📜', color: 'text-yellow-400' },
  cmd_injection:       { label: 'Cmd Injection',   icon: '💻', color: 'text-red-400'    },
  path_traversal:      { label: 'Path Traversal',  icon: '📂', color: 'text-purple-400' },
  anomaly:             { label: 'ML Anomaly',      icon: '🤖', color: 'text-cyan-400'   },
  ddos:                { label: 'DDoS',            icon: '🌊', color: 'text-pink-400'   },
  credential_stuffing: { label: 'Cred Stuffing',   icon: '🔑', color: 'text-yellow-400' },
  none:                { label: 'Clean',           icon: '✅', color: 'text-green-400'  },
}

export default function AttemptsTable({ attempts = [], total = 0, loading, onFilterChange }) {
  const [severityFilter, setSeverityFilter] = useState('all')
  const [attackFilter,   setAttackFilter]   = useState('all')
  const [expanded,       setExpanded]       = useState(null)

  const handleSeverity = (v) => {
    setSeverityFilter(v)
    onFilterChange?.({ severity: v, attack: attackFilter })
  }
  const handleAttack = (v) => {
    setAttackFilter(v)
    onFilterChange?.({ severity: severityFilter, attack: v })
  }

  return (
    <div className="card-glow">
      <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
        <div>
          <h2 className="section-title">Login Attempts</h2>
          <p className="text-cyber-muted text-xs mt-0.5 font-mono">
            {total} total · showing {attempts.length}
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          {/* Severity filter */}
          <div className="flex items-center gap-1 bg-cyber-surface rounded-lg p-1 border border-cyber-border">
            {['all', 'critical', 'high', 'medium', 'low'].map(v => (
              <button
                key={v}
                onClick={() => handleSeverity(v)}
                className={clsx(
                  'text-xs font-mono px-2 py-1 rounded-md transition-all capitalize',
                  severityFilter === v
                    ? 'bg-cyber-accent text-cyber-bg font-bold'
                    : 'text-cyber-muted hover:text-white'
                )}
              >
                {v}
              </button>
            ))}
          </div>

          {/* Attack filter */}
          <select
            value={attackFilter}
            onChange={e => handleAttack(e.target.value)}
            className="text-xs font-mono bg-cyber-surface border border-cyber-border text-cyber-text rounded-lg px-3 py-1.5 focus:outline-none focus:border-cyber-accent"
          >
            <option value="all">All Types</option>
            {Object.entries(ATTACK_MAP).map(([k, v]) => (
              <option key={k} value={k}>{v.icon} {v.label}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr className="border-b border-cyber-border text-cyber-muted text-left">
              <th className="pb-2 pr-4 font-medium">TIME</th>
              <th className="pb-2 pr-4 font-medium">IP ADDRESS</th>
              <th className="pb-2 pr-4 font-medium">USERNAME</th>
              <th className="pb-2 pr-4 font-medium">RESULT</th>
              <th className="pb-2 pr-4 font-medium">ATTACK TYPE</th>
              <th className="pb-2 pr-4 font-medium">SEVERITY</th>
              <th className="pb-2 font-medium">RISK SCORE</th>
            </tr>
          </thead>
          <tbody>
            {loading && !attempts.length ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-cyber-muted">
                  <div className="animate-pulse">Loading...</div>
                </td>
              </tr>
            ) : attempts.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-12 text-center text-cyber-muted">
                  No attempts found · try running a simulation
                </td>
              </tr>
            ) : (
              attempts.map((row, i) => {
                const atk = ATTACK_MAP[row.attack_type] || ATTACK_MAP.none
                const isOpen = expanded === row.id

                return (
                  <>
                    <tr
                      key={row.id}
                      onClick={() => setExpanded(isOpen ? null : row.id)}
                      className={clsx(
                        'border-b border-cyber-border/50 cursor-pointer transition-colors',
                        i % 2 === 0 ? 'bg-transparent' : 'bg-cyber-surface/20',
                        'hover:bg-cyber-border/20',
                        row.attack_type !== 'none' ? 'border-l-2' : '',
                        row.severity === 'critical' ? 'border-l-red-500' :
                        row.severity === 'high'     ? 'border-l-orange-500' :
                        row.severity === 'medium'   ? 'border-l-yellow-500' : ''
                      )}
                    >
                      <td className="py-2 pr-4 text-cyber-muted whitespace-nowrap">
                        {formatDistanceToNow(new Date(row.timestamp * 1000), { addSuffix: true })}
                      </td>
                      <td className="py-2 pr-4 text-cyber-accent whitespace-nowrap">
                        {row.blocked && <span className="text-red-400 mr-1">🚫</span>}
                        {row.ip_address}
                      </td>
                      <td className="py-2 pr-4 text-white max-w-[120px] truncate" title={row.username}>
                        {row.username}
                      </td>
                      <td className="py-2 pr-4">
                        <span className={row.success ? 'text-green-400' : 'text-red-400'}>
                          {row.success ? '✅ Success' : '❌ Failed'}
                        </span>
                      </td>
                      <td className="py-2 pr-4">
                        <span className={atk.color}>
                          {atk.icon} {atk.label}
                        </span>
                      </td>
                      <td className="py-2 pr-4">
                        <span className={SEV_BADGE[row.severity] || 'badge-low'}>
                          {row.severity?.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-2">
                        <div className="flex items-center gap-2">
                          <div className="risk-bar w-16">
                            <div
                              className={clsx(
                                'h-full rounded-full',
                                row.risk_score > 0.8 ? 'bg-red-500' :
                                row.risk_score > 0.5 ? 'bg-orange-500' :
                                row.risk_score > 0.2 ? 'bg-yellow-500' : 'bg-green-500'
                              )}
                              style={{ width: `${Math.max(2, (row.risk_score || 0) * 100)}%` }}
                            />
                          </div>
                          <span className="text-cyber-muted w-10 text-right">
                            {((row.risk_score || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                    </tr>

                    {/* Expanded detail row */}
                    {isOpen && (
                      <tr key={`${row.id}-detail`} className="bg-cyber-surface/40">
                        <td colSpan={7} className="px-4 py-3">
                          <div className="text-xs text-cyber-muted">
                            <span className="text-cyber-accent">User-Agent:</span> {row.user_agent || 'N/A'}
                          </div>
                          {row.raw_payload && (() => {
                            try {
                              const p = JSON.parse(row.raw_payload)
                              return p.reasons?.length > 0 ? (
                                <div className="mt-1 space-y-0.5">
                                  {p.reasons.map((r, ri) => (
                                    <div key={ri} className="text-xs text-cyber-muted">
                                      <span className="text-cyber-accent">›</span> {r}
                                    </div>
                                  ))}
                                </div>
                              ) : null
                            } catch { return null }
                          })()}
                        </td>
                      </tr>
                    )}
                  </>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
