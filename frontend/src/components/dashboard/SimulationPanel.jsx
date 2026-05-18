import { useState } from 'react'
import { simulateAPI } from '../../services/api'
import clsx from 'clsx'

const SIMULATIONS = [
  {
    key:     'normal',
    label:   'Normal Traffic',
    desc:    'Generate 50 normal login events as baseline',
    icon:    '✅',
    color:   'green',
    action:  () => simulateAPI.normalTraffic(50),
  },
  {
    key:     'brute',
    label:   'Brute Force',
    desc:    '20 rapid failures from single IP → triggers detection',
    icon:    '🔨',
    color:   'orange',
    action:  () => simulateAPI.bruteForce(20),
  },
  {
    key:     'sqli',
    label:   'SQL Injection',
    desc:    'SQL injection payloads in login credentials',
    icon:    '💉',
    color:   'red',
    action:  () => simulateAPI.sqli(10),
  },
  {
    key:     'ddos',
    label:   'DDoS Burst',
    desc:    'High-rate request burst from multiple IPs',
    icon:    '🌊',
    color:   'purple',
    action:  () => simulateAPI.ddos(50),
  },
  {
    key:     'mixed',
    label:   'Full Scenario',
    desc:    'Complete attack lifecycle: normal → escalation → attack',
    icon:    '🎯',
    color:   'accent',
    action:  () => simulateAPI.mixed(),
  },
]

const COLOR_MAP = {
  green:  'border-green-800/40 hover:border-green-600/60 hover:bg-green-900/10',
  orange: 'border-orange-800/40 hover:border-orange-600/60 hover:bg-orange-900/10',
  red:    'border-red-800/40 hover:border-red-600/60 hover:bg-red-900/10',
  purple: 'border-purple-800/40 hover:border-purple-600/60 hover:bg-purple-900/10',
  accent: 'border-cyber-accent/30 hover:border-cyber-accent/60 hover:bg-cyber-accent/5',
}

export default function SimulationPanel({ onSimulated }) {
  const [loading,  setLoading]  = useState(null)
  const [resetting, setResetting] = useState(false)
  const [lastRun,  setLastRun]  = useState(null)

  const run = async (sim) => {
    setLoading(sim.key)
    try {
      await sim.action()
      setLastRun(sim.key)
      // Give backend a moment to process, then refresh
      setTimeout(() => onSimulated?.(), 1000)
    } catch (e) {
      console.error('Simulation failed:', e)
    } finally {
      setLoading(null)
    }
  }

  const reset = async () => {
    if (!confirm('Clear ALL security data? This cannot be undone.')) return
    setResetting(true)
    try {
      await simulateAPI.reset()
      onSimulated?.()
    } finally {
      setResetting(false)
    }
  }

  return (
    <div className="card-glow">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="section-title">Attack Simulator</h2>
          <p className="text-cyber-muted text-xs mt-0.5 font-mono">
            // Generate realistic attack traffic for demo & testing
          </p>
        </div>
        {lastRun && (
          <span className="text-cyber-green text-xs font-mono">
            ✓ {lastRun} launched
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 mb-4">
        {SIMULATIONS.map(sim => (
          <button
            key={sim.key}
            onClick={() => run(sim)}
            disabled={loading !== null}
            className={clsx(
              'relative text-left p-3 border rounded-xl transition-all duration-200 group',
              COLOR_MAP[sim.color],
              loading === sim.key ? 'opacity-80' : '',
              loading !== null && loading !== sim.key ? 'opacity-40 cursor-not-allowed' : ''
            )}
          >
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-xl">{sim.icon}</span>
              <span className="text-white text-sm font-semibold">{sim.label}</span>
              {loading === sim.key && (
                <span className="ml-auto text-cyber-accent text-xs font-mono animate-pulse">RUNNING...</span>
              )}
            </div>
            <p className="text-cyber-muted text-xs font-mono leading-relaxed">{sim.desc}</p>
          </button>
        ))}
      </div>

      <div className="border-t border-cyber-border pt-3 flex items-center justify-between">
        <span className="text-cyber-muted text-xs font-mono">
          // All simulations run as background tasks
        </span>
        <button
          onClick={reset}
          disabled={resetting}
          className="btn-danger text-xs py-1.5 px-3"
        >
          {resetting ? 'Clearing...' : '⚠️ Reset All Data'}
        </button>
      </div>
    </div>
  )
}
