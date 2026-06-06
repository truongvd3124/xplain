import { PRESETS, type Preset } from "../data/presets";

interface Props {
  onApply: (preset: Preset) => void;
  includeLabels: boolean;
}

export default function PresetSelector({ onApply, includeLabels }: Props) {
  const grouped = PRESETS.reduce<Record<string, Preset[]>>((acc, p) => {
    (acc[p.category] = acc[p.category] || []).push(p);
    return acc;
  }, {});

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const name = e.target.value;
    if (!name) return;
    const preset = PRESETS.find((p) => p.name === name);
    if (preset) onApply(preset);
    e.target.value = "";
  };

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xs font-semibold text-amber-800 uppercase tracking-wide">
          Template
        </span>
        <span className="text-[11px] text-amber-700">
          Auto-fill {includeLabels ? "concepts + labels" : "concepts"}
        </span>
      </div>
      <select
        defaultValue=""
        onChange={handleChange}
        className="w-full border border-amber-300 rounded-md px-3 py-2 text-sm bg-white focus:outline-none focus:ring-2 focus:ring-amber-400"
      >
        <option value="" disabled>
          -- Select a template --
        </option>
        {Object.entries(grouped).map(([cat, list]) => (
          <optgroup key={cat} label={cat}>
            {list.map((p) => (
              <option key={p.name} value={p.name}>
                {p.name} ({p.concepts.length} concepts)
              </option>
            ))}
          </optgroup>
        ))}
      </select>
    </div>
  );
}
