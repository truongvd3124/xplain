import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import ResultGrid from '../components/ResultGrid'
import StatusChip from '../components/StatusChip'
import { useBatch } from '../hooks/useBatches'

export default function BatchDetailPage() {
  const { id } = useParams()
  const [page, setPage] = useState(1)
  const { data, isLoading, error } = useBatch(Number(id), page)

  if (isLoading) return <p className="p-8 text-sm text-slate-500">Loading…</p>
  if (error || !data)
    return <p className="p-8 text-sm text-red-600">Failed to load batch #{id}.</p>

  const { batch, results, total_results, page_size } = data
  const pages = Math.max(1, Math.ceil(total_results / page_size))

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <Link to="/" className="text-xs text-indigo-600 hover:underline">
            ← back to dashboard
          </Link>
          <h1 className="text-xl font-bold">
            Batch #{batch.id} · {batch.profile_name}
          </h1>
          <div className="flex items-center gap-3 text-sm text-slate-600">
            <StatusChip value={batch.status} />
            <span>
              {batch.processed}/{batch.total_images} processed
            </span>
            <span className="text-green-700">{batch.accepted} accepted</span>
            <span className="text-red-700">{batch.rejected} rejected</span>
          </div>
          {batch.error && <p className="text-sm text-red-600">{batch.error}</p>}
        </div>
      </div>

      {(batch.status === 'pending' || batch.status === 'processing') && (
        <div className="h-2 overflow-hidden rounded bg-slate-200">
          <div
            className="h-full bg-indigo-500 transition-all"
            style={{
              width: `${batch.total_images ? (100 * batch.processed) / batch.total_images : 0}%`,
            }}
          />
        </div>
      )}

      <ResultGrid results={results} />

      {pages > 1 && (
        <div className="flex items-center justify-center gap-3 text-sm">
          <button
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
          >
            ← prev
          </button>
          <span>
            page {page} / {pages}
          </span>
          <button
            disabled={page >= pages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded border border-slate-300 px-3 py-1 disabled:opacity-40"
          >
            next →
          </button>
        </div>
      )}
    </div>
  )
}
