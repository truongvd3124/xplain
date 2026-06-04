import type { CandidateScore, VerifyResult } from "../api/client";

const pct = (x: number) => `${(x * 100).toFixed(0)}%`;

// Floors mirror the backend two-evidence gate (config.py). Used only to phrase
// a human-readable reason for a rejection.
const CONCEPT_FLOOR = 0.45;
const PROTOTYPE_FLOOR = 0.45;

// Explain why the best-scoring class still didn't qualify as a match.
function rejectReason(best: CandidateScore, threshold: number): string {
  if (best.score < threshold) {
    return `below the ${pct(threshold)} match threshold.`;
  }
  if (best.concept_score < CONCEPT_FLOOR) {
    return `too few of its concepts were detected (${pct(best.concept_score)}).`;
  }
  if (best.prototype_score != null && best.prototype_score < PROTOTYPE_FLOOR) {
    return `it doesn't look enough like the reference images (${pct(
      best.prototype_score
    )}).`;
  }
  return "it didn't pass the match check.";
}

// Render the predict outcome: predicted class (or "no match", with the reason)
// and the per-concept breakdown for the predicted class.
export default function VerifyResultView({ result }: { result: VerifyResult }) {
  const matched = result.decision === "match";
  const predicted = result.predicted;
  const best = result.ranking[0];

  return (
    <div className="space-y-5">
      {/* Verdict banner */}
      <div
        className={`relative overflow-hidden rounded-2xl p-5 border animate-pop ${
          matched
            ? "border-emerald-400/30 bg-emerald-500/10"
            : "border-amber-400/30 bg-amber-500/10"
        }`}
      >
        <div
          className={`absolute -top-10 -right-10 w-32 h-32 rounded-full blur-2xl ${
            matched ? "bg-emerald-400/30" : "bg-amber-400/25"
          }`}
          aria-hidden
        />
        {matched && predicted ? (
          <div className="relative flex items-center justify-between gap-4">
            <div>
              <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-emerald-600">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Match
              </span>
              <p className="mt-1 text-xl font-extrabold text-[var(--ink)] capitalize">
                {predicted.class_name}
              </p>
            </div>
            <span className="mono text-3xl font-bold text-emerald-600">
              {pct(predicted.score)}
            </span>
          </div>
        ) : (
          <div className="relative">
            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-amber-600">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" /> No match
            </span>
            <p className="mt-1 text-base font-bold text-amber-700">
              Chưa có output phù hợp
            </p>
            <p className="text-sm text-amber-800/80 mt-1">
              Hãy config thêm class bên tab 1 (Builder).
              {best && (
                <>
                  {" "}Best guess <b className="text-amber-800">{best.class_name}</b> at{" "}
                  <b className="text-amber-800">{pct(best.score)}</b> — {rejectReason(best, result.threshold)}
                </>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Per-concept breakdown for the predicted class */}
      {matched && predicted && result.concepts.length > 0 && (
        <div className="glass rounded-2xl p-4">
          <div className="flex justify-between items-baseline mb-3">
            <h3 className="text-sm font-semibold text-[var(--ink)]">
              Why “{predicted.class_name}”?
            </h3>
            <span className="text-xs mono text-[var(--ink-soft)]">
              {predicted.num_present}/{predicted.num_concepts} concepts present
            </span>
          </div>
          <ul className="space-y-2">
            {result.concepts.map((c) => (
              <li key={c.concept} className="flex items-center gap-3">
                <span
                  className={`w-4 text-center text-sm ${
                    c.present ? "text-emerald-500" : "text-black/20"
                  }`}
                >
                  {c.present ? "✓" : "·"}
                </span>
                <span className="w-40 text-sm text-[var(--ink-soft)] truncate">
                  {c.concept}
                </span>
                <div className="flex-1 h-2 bg-black/[0.06] rounded-full overflow-hidden">
                  <div
                    className={`h-2 rounded-full bar-grow ${
                      c.present
                        ? "bg-gradient-to-r from-emerald-400 to-teal-400"
                        : "bg-black/10"
                    }`}
                    style={{ width: pct(c.probability) }}
                  />
                </div>
                <span className="w-12 text-right text-xs mono text-[var(--ink-soft)]">
                  {pct(c.probability)}
                </span>
                <span className="w-10 text-right text-[10px] text-[var(--ink-soft)]/50">
                  w{c.importance}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-[var(--ink-soft)]/50 text-right mono">
        Inference time: {result.inference_time_ms} ms
      </p>
    </div>
  );
}
