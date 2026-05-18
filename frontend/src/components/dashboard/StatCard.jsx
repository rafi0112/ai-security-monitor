import clsx from 'clsx'

export default function StatCard({ icon, label, value, sub, color = 'accent', trend, loading }) {
  const colorMap = {
    accent: { val: 'text-cyber-accent',  bg: 'bg-cyber-accent/10',  border: 'border-cyber-accent/20' },
    red:    { val: 'text-red-400',       bg: 'bg-red-900/20',       border: 'border-red-800/30' },
    green:  { val: 'text-green-400',     bg: 'bg-green-900/20',     border: 'border-green-800/30' },
    orange: { val: 'text-orange-400',    bg: 'bg-orange-900/20',    border: 'border-orange-800/30' },
    yellow: { val: 'text-yellow-400',    bg: 'bg-yellow-900/20',    border: 'border-yellow-800/30' },
    purple: { val: 'text-purple-400',    bg: 'bg-purple-900/20',    border: 'border-purple-800/30' },
  }
  const c = colorMap[color] || colorMap.accent

  return (
    <div className={clsx(
      'card-glow relative overflow-hidden group border-cyber-border/30 hover:border-cyber-accent/30 transition-colors duration-200',
    )}>
      <div className="relative px-4 py-3">
        <div className="flex items-start justify-between mb-3">
          <div className={clsx('w-9 h-9 rounded-lg flex items-center justify-center text-lg border', c.bg, c.border)}>
            {icon}
          </div>
          {trend !== undefined && (
            <span className={clsx(
              'text-xs font-mono px-2 py-0.5 rounded-full border',
              trend > 0 ? 'text-red-400 bg-red-900/20 border-red-800/30' :
              trend < 0 ? 'text-green-400 bg-green-900/20 border-green-800/30' :
                          'text-cyber-muted bg-cyber-border/20 border-cyber-border'
            )}>
              {trend > 0 ? '↑' : trend < 0 ? '↓' : '—'} {Math.abs(trend)}%
            </span>
          )}
        </div>

        <div className={clsx(
          'text-3xl font-bold mb-1 counter-value transition-all',
          loading ? 'text-cyber-muted animate-pulse' : c.val
        )}>
          {loading ? '...' : value}
        </div>

        <div className="text-cyber-muted text-xs font-mono tracking-wider uppercase">{label}</div>
        {sub && <div className="text-cyber-muted text-xs mt-0.5">{sub}</div>}
      </div>

      {/* Bottom accent line */}
      <div className={clsx('absolute bottom-0 left-0 right-0 h-px opacity-40', c.bg.replace('/20', ''))}
           style={{ background: `linear-gradient(90deg, transparent, currentColor, transparent)` }} />
    </div>
  )
}
