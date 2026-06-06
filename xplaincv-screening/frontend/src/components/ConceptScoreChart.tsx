import {
  Bar,
  BarChart,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ConceptScoreRow } from '../api/types'

interface Props {
  concepts: ConceptScoreRow[]
  presenceThreshold: number
}

/** Horizontal bars: per-concept presence probability vs the presence threshold. */
export default function ConceptScoreChart({ concepts, presenceThreshold }: Props) {
  const data = concepts.map((c) => ({
    name: c.concept,
    probability: c.probability,
    present: c.present,
  }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, concepts.length * 44)}>
      <BarChart data={data} layout="vertical" margin={{ left: 30, right: 30 }}>
        <XAxis type="number" domain={[0, 1]} tickFormatter={(v) => v.toFixed(1)} />
        <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
        <Tooltip
          formatter={(value) => [Number(value).toFixed(3), 'probability']}
        />
        <ReferenceLine
          x={presenceThreshold}
          stroke="#475569"
          strokeDasharray="4 4"
          label={{ value: `threshold ${presenceThreshold}`, position: 'top', fontSize: 11 }}
        />
        <Bar dataKey="probability" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.present ? '#22c55e' : '#ef4444'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
