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
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm
                     focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          type="button"
          onClick={addConcept}
          disabled={!draft.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium
                     hover:bg-blue-700 disabled:opacity-50 transition"
        >
          Add
        </button>
      </div>

      {concepts.length === 0 ? (
        <p className="text-xs text-gray-400 italic">No concepts yet.</p>
      ) : (
        <ul className="space-y-1.5">
          {concepts.map((c, i) => (
            <li
              key={i}
              className="flex items-center gap-3 bg-white border border-gray-200
                         rounded-lg px-3 py-2"
            >
              <span className="flex-1 text-sm text-gray-800">{c.concept}</span>
              <label className="text-xs text-gray-400">importance</label>
              <select
                value={c.importance}
                onChange={(e) => updateImportance(i, Number(e.target.value))}
                className="border border-gray-300 rounded px-1.5 py-1 text-sm"
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
                className="text-gray-400 hover:text-red-600 font-bold"
              >
                x
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
