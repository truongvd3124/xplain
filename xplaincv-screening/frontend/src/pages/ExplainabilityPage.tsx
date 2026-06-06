import { Link, useParams } from 'react-router-dom'
import ConceptScoreChart from '../components/ConceptScoreChart'
import StatusChip from '../components/StatusChip'
import { useResult } from '../hooks/useBatches'

function ScoreCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-center">
      <p className="text-xs uppercase text-slate-500">{label}</p>
      <p className="text-lg font-bold text-slate-800">{value}</p>
    </div>
  )
}

export default function ExplainabilityPage() {
  const { id } = useParams()
  const { data: r, isLoading, error } = useResult(Number(id))

  if (isLoading) return <p className="p-8 text-sm text-slate-500">Loading…</p>
  if (error || !r)
    return <p className="p-8 text-sm text-red-600">Failed to load result #{id}.</p>

  const passed = r.concepts.filter((c) => c.present)
  const failed = r.concepts.filter((c) => !c.present)

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <Link to={`/batches/${r.batch_id}`} className="text-xs text-indigo-600 hover:underline">
        ← back to batch #{r.batch_id}
      </Link>

      <div className="grid gap-6 md:grid-cols-[320px_1fr]">
        {/* image + verdict */}
        <div className="space-y-4">
          <img src={r.image_url} className="w-full rounded-xl border border-slate-200 object-cover" />
          <div className="flex items-center gap-3">
            <StatusChip value={r.final_decision} />
            <span className="text-lg font-bold">
              {(r.confidence_score * 100).toFixed(1)}%
            </span>
            <span className="text-sm text-slate-500">
              vs threshold {(r.threshold_score * 100).toFixed(0)}%
            </span>
          </div>
          {r.reject_reason && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">
              <p className="mb-1 text-xs font-semibold uppercase">Why rejected</p>
              {r.reject_reason}
            </div>
          )}
          <div className="grid grid-cols-3 gap-2">
            <ScoreCard label="concept" value={(r.concept_score * 100).toFixed(0) + '%'} />
            <ScoreCard
              label="prototype"
              value={r.prototype_score != null ? (r.prototype_score * 100).toFixed(0) + '%' : '—'}
            />
            <ScoreCard label="coverage" value={(r.coverage * 100).toFixed(0) + '%'} />
          </div>
        </div>

        {/* concepts */}
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 bg-white p-4">
            <h2 className="mb-2 text-base font-semibold">
              Concept evidence — “{r.profile_name}”
            </h2>
            <ConceptScoreChart concepts={r.concepts} presenceThreshold={r.presence_threshold} />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-xl border border-green-200 bg-green-50 p-4">
              <h3 className="mb-2 text-sm font-semibold text-green-800">
                ✓ Detected ({passed.length})
              </h3>
              <ul className="space-y-1 text-sm text-green-900">
                {passed.map((c) => (
                  <li key={c.concept} className="flex justify-between">
                    <span>{c.concept}</span>
                    <span className="font-mono">{(c.probability * 100).toFixed(0)}%</span>
                  </li>
                ))}
                {!passed.length && <li className="text-green-700/60">none</li>}
              </ul>
            </div>
            <div className="rounded-xl border border-red-200 bg-red-50 p-4">
              <h3 className="mb-2 text-sm font-semibold text-red-800">
                ✗ Missing ({failed.length})
              </h3>
              <ul className="space-y-1 text-sm text-red-900">
                {failed.map((c) => (
                  <li key={c.concept} className="flex justify-between">
                    <span>{c.concept}</span>
                    <span className="font-mono">{(c.probability * 100).toFixed(0)}%</span>
                  </li>
                ))}
                {!failed.length && <li className="text-red-700/60">none</li>}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
