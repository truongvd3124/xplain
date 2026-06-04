import { useState } from "react";
import type { Concept } from "../api/client";

interface Props {
  concepts: Concept[];
  onChange: (concepts: Concept[]) => void;
}

const DEFAULT_IMPORTANCE = 3;

// Editable list of visual concepts. Each row has the concept text and an
// importance selector (1-5); concepts can be added by hand or removed.
export default function ConceptEditor({ concepts, onChange }: Props) {
  const [draft, setDraft] = useState("");

  const addConcept = () => {
    const text = draft.trim().toLowerCase();
    if (!text || concepts.some((c) => c.concept === text)) {
      setDraft("");
      return;
    }
    onChange([...concepts, { concept: text, importance: DEFAULT_IMPORTANCE }]);
    setDraft("");
  };

  const updateImportance = (index: number, importance: number) =>
    onChange(
      concepts.map((c, i) => (i === index ? { ...c, importance } : c))
    );

  const removeAt = (index: number) =>
    onChange(concepts.filter((_, i) => i !== index));

  return (
    <div className="space-y-2">
      <div className="flex gap-2">
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addConcept();
            }
          }}
          placeholder='Add a visual concept, e.g. "floppy ears"'
          className="field flex-1 rounded-xl px-3 py-2 text-sm"
        />
        <button
          type="button"
          onClick={addConcept}
          disabled={!draft.trim()}
          className="btn-grad px-4 py-2 text-white rounded-xl text-sm font-semibold"
        >
          Add
        </button>
      </div>

      {concepts.length === 0 ? (
        <p className="text-xs text-[var(--ink-soft)]/60 italic">No concepts yet.</p>
      ) : (
        <ul className="space-y-1.5 stagger">
          {concepts.map((c, i) => (
            <li
              key={i}
              className="flex items-center gap-3 rounded-xl px-3 py-2 bg-black/[0.04]
                         border border-black/10 transition-colors hover:border-violet-400/40"
            >
              <span className="grid place-items-center w-6 h-6 shrink-0 rounded-lg brand-gradient text-[10px] font-bold text-white">
                {c.importance}
              </span>
              <span className="flex-1 text-sm text-[var(--ink)]">{c.concept}</span>
              <label className="text-xs text-[var(--ink-soft)]/60">importance</label>
              <select
                value={c.importance}
                onChange={(e) => updateImportance(i, Number(e.target.value))}
                className="field rounded-lg px-1.5 py-1 text-sm"
              >
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => removeAt(i)}
                className="text-[var(--ink-soft)]/50 hover:text-red-400 font-bold text-lg leading-none transition-colors"
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
