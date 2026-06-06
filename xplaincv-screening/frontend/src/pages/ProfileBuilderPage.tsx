import { useState } from 'react'
import type { ConceptIn, ProfileDetail } from '../api/types'
import ConceptEditor from '../components/ConceptEditor'
import ImageDropzone from '../components/ImageDropzone'
import {
  useAddReferenceImages,
  useBuildProfile,
  useCreateProfile,
  useDeleteProfile,
  useExtractConcepts,
  useProfiles,
} from '../hooks/useProfiles'

const STEPS = ['1 · Describe & extract concepts', '2 · Reference images', '3 · Build & calibrate']

export default function ProfileBuilderPage() {
  const [step, setStep] = useState(0)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [concepts, setConcepts] = useState<ConceptIn[]>([])
  const [dropped, setDropped] = useState<string[]>([])
  const [profile, setProfile] = useState<ProfileDetail | null>(null)
  const [refFiles, setRefFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)

  const profiles = useProfiles()
  const extract = useExtractConcepts()
  const create = useCreateProfile()
  const addRefs = useAddReferenceImages()
  const build = useBuildProfile()
  const remove = useDeleteProfile()

  const run = async (fn: () => Promise<void>) => {
    setError(null)
    try {
      await fn()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    }
  }

  const onExtract = () =>
    run(async () => {
      const res = await extract.mutateAsync({ name, description })
      setConcepts(res.concepts)
      setDropped(res.dropped)
    })

  const onCreateAndNext = () =>
    run(async () => {
      const valid = concepts.filter((c) => c.concept.trim())
      const p = await create.mutateAsync({ name, description, concepts: valid })
      setProfile(p)
      setStep(1)
    })

  const onUploadRefs = () =>
    run(async () => {
      if (!profile) return
      if (refFiles.length) {
        const p = await addRefs.mutateAsync({ id: profile.id, files: refFiles })
        setProfile(p)
        setRefFiles([])
      }
      setStep(2)
    })

  const onBuild = () =>
    run(async () => {
      if (!profile) return
      const p = await build.mutateAsync(profile.id)
      setProfile(p)
    })

  const reset = () => {
    setStep(0)
    setName('')
    setDescription('')
    setConcepts([])
    setDropped([])
    setProfile(null)
    setRefFiles([])
    setError(null)
  }

  const busy = extract.isPending || create.isPending || addRefs.isPending || build.isPending

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-4 py-8">
      {/* stepper */}
      <ol className="flex gap-2 text-sm">
        {STEPS.map((label, i) => (
          <li
            key={label}
            className={`flex-1 rounded-lg border px-3 py-2 text-center ${
              i === step
                ? 'border-indigo-500 bg-indigo-50 font-semibold text-indigo-700'
                : i < step
                  ? 'border-green-300 bg-green-50 text-green-700'
                  : 'border-slate-200 bg-white text-slate-400'
            }`}
          >
            {label}
          </li>
        ))}
      </ol>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 px-4 py-2 text-sm text-red-700">
          {error}
        </div>
      )}

      {step === 0 && (
        <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Describe the class you want to accept</h2>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Class name, e.g. dog"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <textarea
            className="h-28 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="Plain-language description: what does this class look like?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <button
            onClick={onExtract}
            disabled={!name.trim() || busy}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {extract.isPending ? 'Extracting…' : 'Extract concepts with AI'}
          </button>

          {dropped.length > 0 && (
            <p className="text-xs text-amber-600">
              Filtered out (noise / class echo): {dropped.join(', ')}
            </p>
          )}

          {concepts.length > 0 && (
            <>
              <h3 className="pt-2 text-sm font-semibold text-slate-600">
                Review & edit the visual concepts
              </h3>
              <ConceptEditor concepts={concepts} onChange={setConcepts} />
              <button
                onClick={onCreateAndNext}
                disabled={busy || !concepts.some((c) => c.concept.trim())}
                className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {create.isPending ? 'Saving…' : 'Save profile → next'}
              </button>
            </>
          )}
        </section>
      )}

      {step === 1 && profile && (
        <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold">
            Reference images for “{profile.name}”{' '}
            <span className="text-sm font-normal text-slate-500">
              (recommended: at least 3 — they calibrate the accept threshold)
            </span>
          </h2>
          <ImageDropzone
            label="Drop reference images here, or click to browse"
            files={refFiles}
            onChange={setRefFiles}
          />
          <div className="flex gap-3">
            <button
              onClick={onUploadRefs}
              disabled={busy}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {addRefs.isPending
                ? 'Uploading…'
                : refFiles.length
                  ? `Upload ${refFiles.length} image(s) → next`
                  : 'Skip (concept-only profile) → next'}
            </button>
          </div>
        </section>
      )}

      {step === 2 && profile && (
        <section className="space-y-4 rounded-xl border border-slate-200 bg-white p-6">
          <h2 className="text-lg font-semibold">Build & calibrate “{profile.name}”</h2>
          <p className="text-sm text-slate-500">
            Embeds {profile.num_concepts} concepts and {profile.num_references} reference
            image(s) with CLIP, then calibrates the accept threshold.
          </p>
          {!profile.is_built ? (
            <button
              onClick={onBuild}
              disabled={busy}
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
            >
              {build.isPending ? 'Building…' : 'Build profile'}
            </button>
          ) : (
            <div className="space-y-2 rounded-lg border border-green-300 bg-green-50 p-4 text-sm">
              <p className="font-semibold text-green-800">Profile built ✓</p>
              <p>
                Accept threshold: <b>{profile.threshold_score}</b>
                {profile.calibration && profile.calibration.method !== 'default' && (
                  <>
                    {' '}· prototype window [{profile.calibration.proto_lo},{' '}
                    {profile.calibration.proto_hi}] ({profile.calibration.method})
                  </>
                )}
              </p>
              <button
                onClick={reset}
                className="rounded-md bg-indigo-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-indigo-700"
              >
                Create another profile
              </button>
            </div>
          )}
        </section>
      )}

      {/* existing profiles */}
      <section className="space-y-3">
        <h2 className="text-base font-semibold text-slate-700">Existing profiles</h2>
        {(profiles.data ?? []).map((p) => (
          <div
            key={p.id}
            className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm"
          >
            <div>
              <span className="font-semibold">{p.name}</span>{' '}
              <span className="text-slate-500">
                · {p.num_concepts} concepts · {p.num_references} refs · threshold{' '}
                {p.threshold_score} · {p.is_built ? 'built' : 'not built'}
              </span>
            </div>
            <button
              onClick={() => remove.mutate(p.id)}
              className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
            >
              delete
            </button>
          </div>
        ))}
      </section>
    </div>
  )
}
