import { useMemo, useState } from 'react'
import type { CandidateScore } from '../api/types'
import ConceptScoreChart from '../components/ConceptScoreChart'
import ImageDropzone from '../components/ImageDropzone'
import { useVerify } from '../hooks/useVerify'

export default function VerifyPage() {
  const [files, setFiles] = useState<File[]>([])
  const [selected, setSelected] = useState<number | null>(null)
  const verify = useVerify()

  const preview = useMemo(
    () => (files[0] ? URL.createObjectURL(files[0]) : null),
    [files],
  )

  const onVerify = async () => {
    if (!files[0]) return
    setSelected(null)
    await verify.mutateAsync(files[0])
  }

  const data = verify.data
  const candidate: CandidateScore | null =
    data == null
      ? null
      : selected != null
        ? (data.candidates.find((c) => c.profile_id === selected) ?? null)
        : (data.match ?? data.candidates[0] ?? null)

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-8">
      <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
        <h2 className="text-lg font-semibold">Verify one image against every profile</h2>
        <p className="text-sm text-slate-500">
          The image is scored against all built profiles; the best candidate that
          clears the evidence gate is reported as the match — otherwise “no match”.
        </p>
        <div className="grid gap-4 sm:grid-cols-[1fr_auto]">
          <ImageDropzone
            label="Drop ONE image here, or click to browse"
            files={files}
            onChange={(f) => {
              setFiles(f)
              verify.reset()
            }}
            multiple={false}
          />
          <button
            onClick={onVerify}
            disabled={!files.length || verify.isPending}
            className="self-start rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {verify.isPending ? 'Verifying…' : 'Verify'}
          </button>
        </div>
        {verify.isError && (
          <p className="rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
            {verify.error instanceof Error ? verify.error.message : 'verify failed'}
          </p>
        )}
      </section>

      {data && (
        <>
          {/* verdict banner */}
          {data.match ? (
            <div className="rounded-xl border border-green-300 bg-green-50 px-6 py-4">
              <p className="text-sm text-green-700">Best match</p>
              <p className="text-2xl font-bold text-green-800">
                {data.match.profile_name}{' '}
                <span className="text-lg font-semibold">
                  {(data.match.score * 100).toFixed(1)}%
                </span>
              </p>
            </div>
          ) : (
            <div className="rounded-xl border border-amber-300 bg-amber-50 px-6 py-4">
              <p className="text-lg font-bold text-amber-800">No match</p>
              <p className="text-sm text-amber-700">
                No profile passed the evidence gate (score ≥{' '}
                {(data.match_threshold * 100).toFixed(0)}% + concept/prototype/coverage
                floors). Create or refine a profile in the Builder tab.
              </p>
            </div>
          )}

          <div className="grid gap-6 md:grid-cols-[280px_1fr]">
            <div className="space-y-4">
              {preview && (
                <img
                  src={preview}
                  className="w-full rounded-xl border border-slate-200 object-cover"
                />
              )}
              {/* ranking table */}
              <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 text-left text-xs uppercase text-slate-500">
                    <tr>
                      <th className="px-3 py-2">Profile</th>
                      <th className="px-3 py-2">Score</th>
                      <th className="px-3 py-2">Gate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.candidates.map((c) => (
                      <tr
                        key={c.profile_id}
                        onClick={() => setSelected(c.profile_id)}
                        className={`cursor-pointer border-t border-slate-100 hover:bg-indigo-50/40 ${
                          candidate?.profile_id === c.profile_id ? 'bg-indigo-50' : ''
                        }`}
                      >
                        <td className="px-3 py-2 font-medium">{c.profile_name}</td>
                        <td className="px-3 py-2">{(c.score * 100).toFixed(1)}%</td>
                        <td className="px-3 py-2">{c.passes_gate ? '✅' : '—'}</td>
                      </tr>
                    ))}
                    {!data.candidates.length && (
                      <tr>
                        <td colSpan={3} className="px-3 py-4 text-center text-slate-400">
                          no built profiles yet
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            {/* candidate explanation */}
            {candidate && (
              <div className="space-y-4">
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  <h2 className="mb-1 text-base font-semibold">
                    Concept evidence — “{candidate.profile_name}”
                  </h2>
                  <p className="mb-2 text-xs text-slate-500">
                    concept {(candidate.concept_score * 100).toFixed(0)}% · prototype{' '}
                    {candidate.prototype_score != null
                      ? (candidate.prototype_score * 100).toFixed(0) + '%'
                      : '—'}{' '}
                    · coverage {candidate.num_present}/{candidate.num_concepts}
                  </p>
                  <ConceptScoreChart
                    concepts={candidate.concepts}
                    presenceThreshold={data.presence_threshold}
                  />
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
