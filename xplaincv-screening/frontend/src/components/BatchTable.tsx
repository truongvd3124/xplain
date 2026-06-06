import { Link } from 'react-router-dom'
import type { BatchSummary } from '../api/types'
import StatusChip from './StatusChip'

export default function BatchTable({ batches }: { batches: BatchSummary[] }) {
  if (!batches.length) {
    return (
      <p className="rounded-lg border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
        No screening batches yet — upload images above to start one.
      </p>
    )
  }
  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-100 text-left text-xs uppercase text-slate-500">
          <tr>
            <th className="px-4 py-2">Batch</th>
            <th className="px-4 py-2">Profile</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Progress</th>
            <th className="px-4 py-2 text-green-700">Accepted</th>
            <th className="px-4 py-2 text-red-700">Rejected</th>
            <th className="px-4 py-2">Created</th>
          </tr>
        </thead>
        <tbody>
          {batches.map((b) => (
            <tr key={b.id} className="border-t border-slate-100 hover:bg-indigo-50/40">
              <td className="px-4 py-2">
                <Link to={`/batches/${b.id}`} className="font-semibold text-indigo-600 hover:underline">
                  #{b.id}
                </Link>
              </td>
              <td className="px-4 py-2">{b.profile_name}</td>
              <td className="px-4 py-2">
                <StatusChip value={b.status} />
                {b.error && <span className="ml-2 text-xs text-red-600">{b.error}</span>}
              </td>
              <td className="px-4 py-2">
                <div className="flex items-center gap-2">
                  <div className="h-1.5 w-24 overflow-hidden rounded bg-slate-200">
                    <div
                      className="h-full bg-indigo-500 transition-all"
                      style={{
                        width: `${b.total_images ? (100 * b.processed) / b.total_images : 0}%`,
                      }}
                    />
                  </div>
                  <span className="text-xs text-slate-500">
                    {b.processed}/{b.total_images}
                  </span>
                </div>
              </td>
              <td className="px-4 py-2 font-medium text-green-700">{b.accepted}</td>
              <td className="px-4 py-2 font-medium text-red-700">{b.rejected}</td>
              <td className="px-4 py-2 text-xs text-slate-500">
                {new Date(b.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
