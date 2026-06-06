import { Link } from 'react-router-dom'
import type { ResultSummary } from '../api/types'
import StatusChip from './StatusChip'

export default function ResultGrid({ results }: { results: ResultSummary[] }) {
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
      {results.map((r) => (
        <Link
          key={r.id}
          to={`/results/${r.id}`}
          className="group overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition hover:shadow-md"
        >
          <img
            src={r.image_url}
            className="h-40 w-full object-cover transition group-hover:scale-105"
            loading="lazy"
          />
          <div className="space-y-1 p-3">
            <div className="flex items-center justify-between">
              <StatusChip value={r.final_decision} />
              <span className="text-sm font-semibold text-slate-700">
                {(r.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
            {r.reject_reason && (
              <p className="line-clamp-2 text-xs text-slate-500">{r.reject_reason}</p>
            )}
          </div>
        </Link>
      ))}
    </div>
  )
}
