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
        className={`rounded-xl p-5 border ${
          matched
            ? "bg-green-50 border-green-200"
            : "bg-amber-50 border-amber-200"
        }`}
      >
        {matched && predicted ? (
          <div className="flex items-baseline justify-between">
            <span className="text-lg font-bold text-green-700">
              Predicted: {predicted.class_name}
            </span>
            <span className="text-2xl font-mono font-bold text-green-700">
              {pct(predicted.score)}
            </span>
          </div>
        ) : (
          <div>
            <p className="text-base font-bold text-amber-700">
              Chưa có output phù hợp
            </p>
            <p className="text-sm text-amber-700 mt-1">
              Hãy config thêm class bên tab 1 (Builder).
              {best && (
                <>
                  {" "}Best guess <b>{best.class_name}</b> at{" "}
                  <b>{pct(best.score)}</b> — {rejectReason(best, result.threshold)}
                </>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Per-concept breakdown for the predicted class */}
      {matched && predicted && result.concepts.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          <div className="flex justify-between items-baseline mb-3">
            <h3 className="text-sm font-semibold text-gray-700">
              Why "{predicted.class_name}"?
            </h3>
            <span className="text-xs text-gray-500">
              {predicted.num_present}/{predicted.num_concepts} concepts present
            </span>
          </div>
          <ul className="space-y-2">
            {result.concepts.map((c) => (
              <li key={c.concept} className="flex items-center gap-3">
                <span
                  className={`w-4 text-center text-sm ${
                    c.present ? "text-green-600" : "text-gray-300"
                  }`}
                >
                  {c.present ? "✓" : "·"}
                </span>
                <span className="w-40 text-sm text-gray-700 truncate">
                  {c.concept}
                </span>
                <div className="flex-1 h-2 bg-gray-100 rounded-full">
                  <div
                    className={`h-2 rounded-full ${
                      c.present ? "bg-green-500" : "bg-gray-300"
                    }`}
                    style={{ width: pct(c.probability) }}
                  />
                </div>
                <span className="w-12 text-right text-xs font-mono text-gray-500">
                  {pct(c.probability)}
                </span>
                <span className="w-10 text-right text-[10px] text-gray-400">
                  w{c.importance}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <p className="text-xs text-gray-400 text-right">
        Inference time: {result.inference_time_ms} ms
      </p>
    </div>
  );
}
