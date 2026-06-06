import type { ConceptIn } from '../api/types'

interface Props {
  concepts: ConceptIn[]
  onChange: (concepts: ConceptIn[]) => void
}

/** Editable list of concepts with importance sliders (1-5). */
export default function ConceptEditor({ concepts, onChange }: Props) {
  const update = (i: number, patch: Partial<ConceptIn>) =>
    onChange(concepts.map((c, j) => (j === i ? { ...c, ...patch } : c)))

  const remove = (i: number) => onChange(concepts.filter((_, j) => j !== i))

  const add = () => onChange([...concepts, { concept: '', importance: 3 }])

  return (
    <div className="space-y-2">
      {concepts.map((c, i) => (
        <div key={i} className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-2">
          <input
            className="flex-1 rounded-md border border-slate-300 px-2 py-1 text-sm"
            value={c.concept}
            placeholder="visual concept, e.g. floppy ears"
            onChange={(e) => update(i, { concept: e.target.value })}
          />
          <label className="flex items-center gap-2 text-xs text-slate-500">
            importance
            <input
              type="range"
              min={1}
              max={5}
              value={c.importance}
              onChange={(e) => update(i, { importance: Number(e.target.value) })}
            />
            <span className="w-3 font-semibold text-slate-700">{c.importance}</span>
          </label>
          <button
            onClick={() => remove(i)}
            className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
          >
            remove
          </button>
        </div>
      ))}
      <button
        onClick={add}
        className="rounded-md border border-dashed border-slate-300 px-3 py-1.5 text-sm text-slate-500 hover:border-indigo-400 hover:text-indigo-600"
      >
        + add concept
      </button>
    </div>
  )
}
