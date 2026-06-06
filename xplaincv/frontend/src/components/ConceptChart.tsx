import type { ConceptScore } from "../api/client";

interface Props {
  concepts: ConceptScore[];
  title?: string;
  emptyMessage?: string;
}

export default function ConceptChart({
  concepts,
  title = "Contributing Concepts",
  emptyMessage,
}: Props) {
  const maxScore = Math.max(...concepts.map((c) => Math.abs(c.score)), 0.01);

  if (concepts.length === 0 && emptyMessage) {
    return (
      <div className="space-y-1.5">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
        <p className="text-xs text-gray-500 italic">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-1.5">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">{title}</h3>
      {concepts.map((c, i) => (
        <div key={i} className="flex items-center gap-2">
          <div className="w-56 flex items-center justify-end gap-1.5 shrink-0">
            {c.source === "user" && (
              <span className="px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-[10px] font-semibold">
                USER
              </span>
            )}
            {c.source === "bank" && (
              <span className="px-1.5 py-0.5 bg-gray-100 text-gray-500 rounded text-[10px] font-semibold">
                BANK
              </span>
            )}
            <span
              className="text-xs text-gray-600 truncate"
              title={c.name}
            >
              {c.name}
            </span>
          </div>
          <div className="flex-1 h-5 bg-gray-100 rounded overflow-hidden">
            <div
              className={`h-full rounded transition-all ${
                c.score > 0 ? "bg-blue-500" : "bg-red-400"
              }`}
              style={{ width: `${(Math.abs(c.score) / maxScore) * 100}%` }}
            />
          </div>
          <span className="w-16 text-xs text-gray-400 tabular-nums">
            {c.score > 0 ? "+" : ""}
            {c.score.toFixed(4)}
          </span>
        </div>
      ))}
    </div>
  );
}
