import { useState } from 'react'
import { alertsAPI } from '../../services/api'
import clsx from 'clsx'
import { formatDistanceToNow } from 'date-fns'

const SEV_CONFIG = {
  critical: { badge: 'badge-critical', dot: 'bg-red-500',    icon: '🚨' },
  high:     { badge: 'badge-high',     dot: 'bg-orange-500', icon: '⚠️' },
  medium:   { badge: 'badge-medium',   dot: 'bg-yellow-500', icon: '⚡' },
  low:      { badge: 'badge-low',      dot: 'bg-green-500',  icon: 'ℹ️' },
}

const ATTACK_LABEL = {
  brute_force:         'Brute Force',
  sqli:                'SQL Injection',
  xss:                 'XSS Attack',
  cmd_injection:       'Command Injection',
  path_traversal:      'Path Traversal',
  anomaly:             'ML Anomaly',
  ddos:                'DDoS',
  credential_stuffing: 'Credential Stuffing',
  scanner:             'Port/Path Scanner',
}

export default function AlertsPanel({ alerts = [], onRefresh, loading }) {
  const [resolving, setResolving] = useState(null)

  const handleResolve = async (id) => {
    setResolving(id)
    try {
      await alertsAPI.resolve(id)
      onRefresh?.()
    } finally {
      setResolving(null)
    }
  }

  const handleAck = async (id) => {
    try {
      await alertsAPI.ack(id)
      onRefresh?.()
    } catch {}
  }

  if (loading && !alerts.length) {
    return (
      <div className="card-glow h-64 flex items-center justify-center">
        <div className="text-cyber-muted font-mono text-sm animate-pulse">Loading alerts...</div>
      </div>
    )
  }

  return (
    <div className="card-glow">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h2 className="section-title">Active Alerts</h2>
          {alerts.length > 0 && (
            <span className="bg-red-900/40 text-red-400 border border-red-800/50 text-xs px-2 py-0.5 rounded-full font-mono">
              {alerts.length}
            </span>
          )}
        </div>
        <button
          onClick={onRefresh}
          className="text-cyber-muted hover:text-cyber-accent text-xs font-mono transition-colors"
        >
          ↻ Refresh
        </button>
      </div>

      {alerts.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-cyber-muted">
          <div className="text-4xl mb-3 opacity-20">🔒</div>
          <p className="font-mono text-sm">No active alerts</p>
          <p className="font-mono text-xs mt-1 opacity-60">System is clean</p>
        </div>
      ) : (
        <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
          {alerts.map(alert => {
            const sc  = SEV_CONFIG[alert.severity] || SEV_CONFIG.low
            const isNew = !alert.acknowledged
            return (
              <div
                key={alert.id}
                className={clsx(
                  'rounded-xl p-3 border transition-all',
                  isNew
                    ? 'bg-cyber-surface border-cyber-border hover:border-cyber-accent/30'
                    : 'bg-cyber-bg/50 border-cyber-border/50 opacity-75'
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-start gap-3 flex-1 min-w-0">
                    <div className={clsx('w-2 h-2 rounded-full mt-1.5 flex-shrink-0', sc.dot,
                      isNew ? 'animate-pulse' : '')} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className={sc.badge}>{alert.severity.toUpperCase()}</span>
                        <span className="text-cyber-muted text-xs font-mono">
                          {ATTACK_LABEL[alert.alert_type] || alert.alert_type}
                        </span>
                        {isNew && (
                          <span className="bg-cyber-accent/20 text-cyber-accent border border-cyber-accent/30 text-xs px-1.5 py-0.5 rounded font-mono">
                            NEW
                          </span>
                        )}
                      </div>
                      <p className="text-cyber-text text-xs leading-relaxed mb-1">{alert.message}</p>
                      <div className="flex items-center gap-3 text-cyber-muted text-xs font-mono">
                        {alert.ip_address && <span>IP: {alert.ip_address}</span>}
                        {alert.username   && <span>User: {alert.username}</span>}
                        <span className="ml-auto">
                          {formatDistanceToNow(new Date(alert.timestamp * 1000), { addSuffix: true })}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-1 flex-shrink-0">
                    {!alert.acknowledged && (
                      <button
                        onClick={() => handleAck(alert.id)}
                        className="text-xs text-cyber-muted hover:text-cyber-accent font-mono px-2 py-0.5 border border-cyber-border rounded hover:border-cyber-accent/40 transition-all"
                      >
                        ACK
                      </button>
                    )}
                    <button
                      onClick={() => handleResolve(alert.id)}
                      disabled={resolving === alert.id}
                      className="text-xs text-green-400 font-mono px-2 py-0.5 border border-green-800/40 rounded hover:bg-green-900/20 transition-all"
                    >
                      {resolving === alert.id ? '...' : 'CLOSE'}
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
