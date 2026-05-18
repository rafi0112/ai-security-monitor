import {
  AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
} from 'recharts'
import { format } from 'date-fns'
import { useRef, useEffect, useState } from 'react'

// ── Debounced resize hook ─────────────────────────────────────────────────────
function useStableChartWidth() {
  const containerRef = useRef(null)
  const [width, setWidth] = useState(0)
  const resizeTimeoutRef = useRef(null)

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    // Set initial width immediately
    const initialWidth = container.getBoundingClientRect().width
    if (initialWidth > 0) setWidth(initialWidth)

    const observer = new ResizeObserver(() => {
      // Debounce: clear previous timeout and set a new one
      clearTimeout(resizeTimeoutRef.current)
      resizeTimeoutRef.current = setTimeout(() => {
        const w = container.getBoundingClientRect().width
        if (w > 0) setWidth(w)
      }, 200)
    })

    observer.observe(container)
    return () => {
      clearTimeout(resizeTimeoutRef.current)
      observer.disconnect()
    }
  }, [])

  return { containerRef, width }
}

// ── Custom tooltip ────────────────────────────────────────────────────────────
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-cyber-surface border border-cyber-border rounded-xl px-4 py-3 text-xs font-mono shadow-xl">
      <p className="text-cyber-muted mb-2">
        {label ? format(new Date(label), 'HH:mm MMM d') : ''}
      </p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-cyber-muted capitalize">{p.name}:</span>
          <span className="text-white font-semibold">{p.value}</span>
        </div>
      ))}
    </div>
  )
}

// ── Timeline Area Chart ───────────────────────────────────────────────────────
export function TimelineChart({ data = [] }) {
  const { containerRef, width } = useStableChartWidth()

  if (!data.length) return (
    <div className="h-48 flex items-center justify-center text-cyber-muted font-mono text-sm">
      No data — run a simulation first
    </div>
  )

  return (
    <div ref={containerRef} style={{ height: '200px', width: '100%', position: 'relative', contain: 'layout' }}>
      <ResponsiveContainer width={width || '100%'} height={200}>
        <AreaChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="gradTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#00d4ff" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00d4ff" stopOpacity={0}   />
              </linearGradient>
              <linearGradient id="gradAttacks" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#ff3366" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#ff3366" stopOpacity={0}   />
              </linearGradient>
              <linearGradient id="gradSuccess" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#00ff88" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00ff88" stopOpacity={0}   />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" vertical={false} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={v => format(new Date(v), 'HH:mm')}
              stroke="#5a7090"
              tick={{ fontSize: 10, fontFamily: 'JetBrains Mono' }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              stroke="#5a7090"
              tick={{ fontSize: 10, fontFamily: 'JetBrains Mono' }}
              tickLine={false}
              axisLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area type="monotone" dataKey="total"   name="Total"   stroke="#00d4ff" fill="url(#gradTotal)"   strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="attacks" name="Attacks" stroke="#ff3366" fill="url(#gradAttacks)" strokeWidth={2} dot={false} />
            <Area type="monotone" dataKey="success" name="Success" stroke="#00ff88" fill="url(#gradSuccess)" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
          </AreaChart>
        </ResponsiveContainer>
    </div>
  )
}

// ── Attack Distribution Donut ─────────────────────────────────────────────────
export function AttackDistChart({ data = [] }) {
  const { containerRef, width } = useStableChartWidth()

  if (!data.length) return (
    <div className="h-48 flex items-center justify-center text-cyber-muted font-mono text-sm">
      No attacks detected yet
    </div>
  )

  const RADIAN = Math.PI / 180
  const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
    if (percent < 0.05) return null
    const radius = innerRadius + (outerRadius - innerRadius) * 0.6
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)
    return (
      <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central"
            fontSize={10} fontFamily="JetBrains Mono">
        {(percent * 100).toFixed(0)}%
      </text>
    )
  }

  return (
    <div ref={containerRef} style={{ height: '200px', width: '100%', position: 'relative', contain: 'layout' }}>
      <ResponsiveContainer width={width || '100%'} height={200}>
        <PieChart>
          <Pie
            data={data}
            dataKey="count"
            nameKey="attack_type"
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={2}
            labelLine={false}
            label={renderCustomLabel}
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip
            formatter={(val, name) => [val, name.replace(/_/g, ' ')]}
            contentStyle={{
              background: '#0f1629',
              border: '1px solid #1e2d4a',
              borderRadius: '12px',
              fontFamily: 'JetBrains Mono',
              fontSize: 11,
            }}
          />
          <Legend
            formatter={v => <span className="text-cyber-muted text-xs font-mono capitalize">{v.replace(/_/g, ' ')}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}

// ── Top IPs Bar Chart ─────────────────────────────────────────────────────────
export function TopIPsChart({ data = [] }) {
  const { containerRef, width } = useStableChartWidth()

  if (!data.length) return (
    <div className="h-48 flex items-center justify-center text-cyber-muted font-mono text-sm">
      No IP data yet
    </div>
  )

  const chartData = data.slice(0, 8).map(d => ({
    ip:      d.ip.length > 15 ? d.ip.slice(0, 13) + '…' : d.ip,
    attacks: d.attacks,
    normal:  d.total - d.attacks,
  }))

  return (
    <div ref={containerRef} style={{ height: '200px', width: '100%', position: 'relative', contain: 'layout' }}>
      <ResponsiveContainer width={width || '100%'} height={200}>
        <BarChart data={chartData} margin={{ top: 5, right: 5, left: -20, bottom: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e2d4a" horizontal={true} vertical={false} />
          <XAxis
              dataKey="ip"
              stroke="#5a7090"
              tick={{ fontSize: 9, fontFamily: 'JetBrains Mono', fill: '#5a7090' }}
              angle={-30} textAnchor="end"
              tickLine={false} axisLine={false}
              interval={0}
            />
            <YAxis
              stroke="#5a7090"
              tick={{ fontSize: 10, fontFamily: 'JetBrains Mono' }}
              tickLine={false} axisLine={false}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="attacks" name="Attacks" fill="#ff3366" radius={[3,3,0,0]} stackId="a" />
            <Bar dataKey="normal"  name="Normal"  fill="#1e2d4a" radius={[3,3,0,0]} stackId="a" />
          </BarChart>
        </ResponsiveContainer>
    </div>
  )
}
