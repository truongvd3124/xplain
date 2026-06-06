import { useState } from 'react'
import BatchTable from '../components/BatchTable'
import ImageDropzone from '../components/ImageDropzone'
import { useBatches, useCreateBatch } from '../hooks/useBatches'
import { useProfiles } from '../hooks/useProfiles'

export default function DashboardPage() {
  const batches = useBatches()
  const profiles = useProfiles()
  const createBatch = useCreateBatch()

  const [profileId, setProfileId] = useState<number | ''>('')
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)

  const builtProfiles = (profiles.data ?? []).filter((p) => p.is_built)

  const submit = async () => {
    if (!profileId || !files.length) return
    setError(null)
    try {
      await createBatch.mutateAsync({ profileId: Number(profileId), files })
      setFiles([])
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-8">
      <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold">New screening batch</h2>
        {error && (
          <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
            {error}
          </div>
        )}
        <div className="flex items-center gap-3">
          <label className="text-sm text-slate-600">Screen against profile:</label>
          <select
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
            value={profileId}
            onChange={(e) => setProfileId(e.target.value ? Number(e.target.value) : '')}
          >
            <option value="">— select —</option>
            {builtProfiles.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} (threshold {p.threshold_score})
              </option>
            ))}
          </select>
          {!builtProfiles.length && (
            <span className="text-xs text-amber-600">
              No built profiles yet — create one in the Profile Builder.
            </span>
          )}
        </div>
        <ImageDropzone
          label="Drop the images to screen here, or click to browse"
          files={files}
          onChange={setFiles}
        />
        <button
          onClick={submit}
          disabled={!profileId || !files.length || createBatch.isPending}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {createBatch.isPending
            ? 'Submitting…'
            : `Screen ${files.length || ''} image(s)`}
        </button>
      </section>

      <section className="space-y-3">
        <h2 className="text-base font-semibold text-slate-700">Screening batches</h2>
        <BatchTable batches={batches.data ?? []} />
      </section>
    </div>
  )
}
