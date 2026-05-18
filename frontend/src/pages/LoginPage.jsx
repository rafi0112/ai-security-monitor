import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'
import clsx from 'clsx'

const SEVERITY_CONFIG = {
  critical: { color: 'text-red-400',    bg: 'bg-red-900/30 border-red-700/50',    icon: '🚨', label: 'CRITICAL' },
  high:     { color: 'text-orange-400', bg: 'bg-orange-900/30 border-orange-700/50', icon: '⚠️', label: 'HIGH' },
  medium:   { color: 'text-yellow-400', bg: 'bg-yellow-900/30 border-yellow-700/50', icon: '⚡', label: 'MEDIUM' },
  low:      { color: 'text-green-400',  bg: 'bg-green-900/30 border-green-700/50',  icon: '✅', label: 'LOW' },
}

const ATTACK_LABELS = {
  brute_force:         '🔨 Brute Force',
  sqli:                '💉 SQL Injection',
  xss:                 '📜 XSS',
  cmd_injection:       '💻 Command Injection',
  path_traversal:      '📂 Path Traversal',
  anomaly:             '🤖 ML Anomaly',
  ddos:                '🌊 DDoS',
  credential_stuffing: '🔑 Cred Stuffing',
  none:                '✅ Clean',
}

export default function LoginPage() {
  const navigate   = useNavigate()
  const [form,     setForm]     = useState({ username: '', password: '' })
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [history,  setHistory]  = useState([])
  const [showPass, setShowPass] = useState(false)

  const handleSubmit = async (e) => {
    e?.preventDefault()
    if (!form.username || !form.password) return

    setLoading(true)
    setResult(null)
    try {
      const data = await authAPI.login(form.username, form.password)
      setResult(data)
      setHistory(prev => [{ ...data, ts: Date.now(), username: form.username }, ...prev].slice(0, 20))
    } catch (err) {
      const status = err.response?.status
      const msg = err.response?.data?.detail || err.message
      const isBlocked = status === 429
      setResult({
        success: false,
        message: msg,
        security: isBlocked ? { blocked: true, blocked_status: msg } : null,
      })
    } finally {
      setLoading(false)
    }
  }

  const fillAttack = (type) => {
    const payloads = {
      sqli:   { username: "admin' OR '1'='1--", password: "anything" },
      xss:    { username: "<script>alert('xss')</script>", password: "pass" },
      brute:  { username: "admin", password: "wrong_password" },
      normal: { username: "alice", password: "alice_pass" },
      admin:  { username: "admin", password: "admin123" },
    }
    setForm(payloads[type] || form)
  }

  const sev = result?.security?.severity || 'low'
  const sc  = SEVERITY_CONFIG[sev] || SEVERITY_CONFIG.low

  return (
    <div className="min-h-screen bg-cyber-bg bg-cyber-grid flex">
      {/* ── Left: Login Form ─────────────────────────────────────────── */}
      <div className="w-full max-w-md flex flex-col justify-center px-10 py-16 relative">

        {/* Decorative vertical line */}
        <div className="absolute right-0 top-0 bottom-0 w-px bg-gradient-to-b from-transparent via-cyber-border to-transparent" />

        <div className="mb-10">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 rounded-lg bg-cyber-accent/20 border border-cyber-accent/40 flex items-center justify-center">
              <span className="text-cyber-accent text-sm">🛡️</span>
            </div>
            <span className="section-title text-xs">AI Security Monitor</span>
          </div>
          <h1 className="text-3xl font-bold text-white mb-1" style={{ fontFamily: 'Orbitron, monospace' }}>
            SECURE LOGIN
          </h1>
          <p className="text-cyber-muted text-sm">Every attempt is analyzed by AI in real-time</p>
        </div>

        {/* Quick-fill attack buttons */}
        <div className="mb-6">
          <p className="text-cyber-muted text-xs mb-2 font-mono">// QUICK TEST PAYLOADS</p>
          <div className="grid grid-cols-3 gap-2">
            {[
              { key: 'normal', label: '✅ Normal', color: 'border-green-800/50 text-green-400 hover:bg-green-900/20' },
              { key: 'admin',  label: '👤 Admin',  color: 'border-cyber-border text-cyber-muted hover:bg-cyber-border/20' },
              { key: 'brute',  label: '🔨 Brute',  color: 'border-orange-800/50 text-orange-400 hover:bg-orange-900/20' },
              { key: 'sqli',   label: '💉 SQLi',   color: 'border-red-800/50 text-red-400 hover:bg-red-900/20' },
              { key: 'xss',    label: '📜 XSS',    color: 'border-yellow-800/50 text-yellow-400 hover:bg-yellow-900/20' },
            ].map(({ key, label, color }) => (
              <button
                key={key}
                onClick={() => fillAttack(key)}
                className={clsx(
                  'border rounded-lg px-2 py-1.5 text-xs font-mono transition-all',
                  color
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-cyber-muted text-xs font-mono mb-1.5 block">USERNAME</label>
            <input
              className="input-field font-mono"
              placeholder="Enter username..."
              value={form.username}
              onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
              autoComplete="off"
              spellCheck={false}
            />
          </div>
          <div>
            <label className="text-cyber-muted text-xs font-mono mb-1.5 block">PASSWORD</label>
            <div className="relative">
              <input
                type={showPass ? 'text' : 'password'}
                className="input-field font-mono pr-10"
                placeholder="Enter password..."
                value={form.password}
                onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                autoComplete="off"
              />
              <button
                type="button"
                onClick={() => setShowPass(!showPass)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-cyber-muted hover:text-cyber-accent transition-colors"
                title={showPass ? 'Hide password' : 'Show password'}
              >
                {showPass ? '�' : '🔓'}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className={clsx(
              'w-full py-3 rounded-lg font-semibold text-sm transition-all duration-200',
              'border font-mono tracking-widest',
              loading
                ? 'bg-cyber-border/20 border-cyber-border text-cyber-muted cursor-not-allowed'
                : 'bg-cyber-accent/10 border-cyber-accent text-cyber-accent hover:bg-cyber-accent hover:text-cyber-bg'
            )}
          >
            {loading ? '[ ANALYZING... ]' : '[ AUTHENTICATE ]'}
          </button>
        </form>

        {/* Result Card */}
        {result && (
          <div className={clsx(
            'mt-5 border rounded-xl p-4 animate-fade-in',
            result.success
              ? 'bg-green-900/20 border-green-700/50'
              : result.security?.blocked
              ? 'bg-red-900/30 border-red-700/50'
              : sc.bg
          )}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="text-lg">
                  {result.success ? '✅' : result.security?.blocked ? '🚫' : sc.icon}
                </span>
                <span className={clsx('font-mono font-bold text-sm',
                  result.success ? 'text-green-400' :
                  result.security?.blocked ? 'text-red-400' :
                  sc.color
                )}>
                  {result.success ? 'LOGIN SUCCESSFUL' : result.security?.blocked ? 'IP BLOCKED' : 'ACCESS DENIED'}
                </span>
              </div>
              {result.security && !result.security.blocked && (
                <span className={clsx(
                  'text-xs font-mono px-2 py-0.5 rounded border',
                  `badge-${sev}`
                )}>
                  {sc.label}
                </span>
              )}
            </div>

            {result.security?.blocked ? (
              <div className="space-y-2 text-xs font-mono">
                <div className="bg-black/20 rounded-lg p-3">
                  <div className="text-red-400 font-semibold mb-1">⏱️ TEMPORARY BAN</div>
                  <div className="text-cyber-muted">{result.security.blocked_status}</div>
                </div>
              </div>
            ) : result.security && !result.success ? (
              <div className="space-y-2 text-xs font-mono">
                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-black/20 rounded-lg p-2">
                    <div className="text-cyber-muted mb-0.5">ATTACK TYPE</div>
                    <div className="text-white">{ATTACK_LABELS[result.security.attack_type] || result.security.attack_type}</div>
                  </div>
                  <div className="bg-black/20 rounded-lg p-2">
                    <div className="text-cyber-muted mb-0.5">RISK SCORE</div>
                    <div className="text-white">{(result.security.risk_score * 100).toFixed(1)}%</div>
                  </div>
                </div>

                {/* Risk bar */}
                <div className="risk-bar">
                  <div
                    className={clsx(
                      'h-full rounded-full transition-all',
                      result.security.risk_score > 0.8 ? 'bg-red-500' :
                      result.security.risk_score > 0.5 ? 'bg-orange-500' :
                      result.security.risk_score > 0.2 ? 'bg-yellow-500' : 'bg-green-500'
                    )}
                    style={{ width: `${Math.max(2, result.security.risk_score * 100)}%` }}
                  />
                </div>

                {/* Reasons */}
                {result.security.reasons?.length > 0 && (
                  <div className="space-y-1">
                    {result.security.reasons.map((r, i) => (
                      <div key={i} className="text-cyber-muted flex gap-2">
                        <span className="text-cyber-accent">›</span>
                        <span>{r}</span>
                      </div>
                    ))}
                  </div>
                )}

                {result.security.blocked && (
                  <div className="flex items-center gap-2 text-red-400 bg-red-900/20 rounded p-2 mt-1">
                    <span>🚫</span>
                    <span>IP blocked for 1 minute</span>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}

        <button
          onClick={() => navigate('/dashboard')}
          className="mt-6 text-center text-cyber-muted hover:text-cyber-accent text-xs font-mono transition-colors"
        >
          → View Security Dashboard
        </button>
      </div>

      {/* ── Right: Live Attempt History ──────────────────────────────── */}
      <div className="flex-1 overflow-hidden flex flex-col p-10">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title">Live Attempt Log</h2>
          <div className="flex items-center gap-2">
            <div className="pulse-dot bg-cyber-green" />
            <span className="text-cyber-muted text-xs font-mono">MONITORING ACTIVE</span>
          </div>
        </div>

        {history.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-cyber-muted">
            <div className="text-6xl mb-4 opacity-20">🛡️</div>
            <p className="font-mono text-sm">No attempts yet</p>
            <p className="font-mono text-xs mt-1">Try a login above to see AI analysis</p>
          </div>
        ) : (
          <div className="space-y-2 overflow-y-auto flex-1">
            {history.map((h, i) => {
              const s = SEVERITY_CONFIG[h.security?.severity || 'low']
              return (
                <div
                  key={i}
                  className={clsx(
                    'border rounded-xl p-3 font-mono text-xs animate-fade-in',
                    i === 0 ? 'border-cyber-accent/40 bg-cyber-card' : 'border-cyber-border bg-cyber-surface/50'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span>{h.success ? '✅' : s?.icon || '❌'}</span>
                      <span className="text-white font-semibold">{h.username}</span>
                      <span className="text-cyber-muted">from</span>
                      <span className="text-cyber-accent">{h.security?.ip || '127.0.0.1'}</span>
                    </div>
                    {h.security && (
                      <span className={`badge-${h.security.severity || 'low'}`}>
                        {(h.security.severity || 'low').toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-4 text-cyber-muted">
                    <span>{ATTACK_LABELS[h.security?.attack_type] || '—'}</span>
                    <span>Risk: {((h.security?.risk_score || 0) * 100).toFixed(1)}%</span>
                    <span className="ml-auto">{new Date(h.ts).toLocaleTimeString()}</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
