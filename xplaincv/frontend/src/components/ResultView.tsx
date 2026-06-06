import type { ClassifyResponse } from "../api/client";
import ConceptChart from "./ConceptChart";

interface Props {
  result: ClassifyResponse;
}

const MODE_BADGE = {
  auto: { label: "Auto", class: "bg-gray-100 text-gray-700" },
  manual: { label: "Manual", class: "bg-purple-100 text-purple-700" },
  hybrid: { label: "Hybrid", class: "bg-blue-100 text-blue-700" },
};

export default function ResultView({ result }: Props) {
  const badge = MODE_BADGE[result.mode];
  const isHybrid = result.mode === "hybrid" && !!result.bank_only && !!result.intervention;

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <img
          src={result.image_url}
          alt="Classified"
          className="w-48 h-48 object-cover rounded-xl border border-gray-200"
        />
        <div className="flex-1 space-y-3">
          <div className="bg-white rounded-xl border border-gray-200 p-5">
            <div className="flex items-start gap-3 mb-2">
              <span className="text-3xl font-bold text-gray-900 capitalize">
                {result.predicted_class}
              </span>
              <span className="mt-1 px-2.5 py-0.5 rounded-full text-sm font-medium bg-green-100 text-green-800">
                {(result.confidence * 100).toFixed(1)}%
              </span>
            </div>
            <div className="flex flex-wrap gap-2 text-xs text-gray-500">
              <span
                className={`px-2 py-0.5 rounded-full font-medium ${badge.class}`}
              >
                {badge.label}
              </span>
              {result.dataset && <span>Dataset: {result.dataset}</span>}
              <span>Feat gap: {result.feat_gap.toFixed(3)}</span>
              <span>Time: {result.inference_time_ms}ms</span>
            </div>
          </div>

          {isHybrid && result.bank_only && result.intervention && (
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-semibold text-gray-500">
                  Bank-only vs Blended
                </h3>
                {result.intervention.changed_prediction ? (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800">
                    USER CHANGED PREDICTION
                  </span>
                ) : (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-gray-100 text-gray-600">
                    AGREE
                  </span>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-lg bg-gray-50 p-3">
                  <div className="text-[10px] font-semibold text-gray-500 mb-1">
                    BANK ONLY (α=0)
                  </div>
                  <div className="text-sm font-semibold capitalize truncate">
                    {result.bank_only.predicted_class}
                  </div>
                  <div className="text-xs text-gray-500">
                    {(result.bank_only.confidence * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="rounded-lg bg-blue-50 p-3">
                  <div className="text-[10px] font-semibold text-blue-700 mb-1">
                    BLENDED (α={result.intervention.alpha.toFixed(2)})
                  </div>
                  <div className="text-sm font-semibold capitalize truncate">
                    {result.predicted_class}
                  </div>
                  <div className="text-xs text-gray-500">
                    {(result.confidence * 100).toFixed(1)}%
                    <span
                      className={`ml-1 ${
                        result.intervention.confidence_delta >= 0
                          ? "text-green-600"
                          : "text-red-500"
                      }`}
                    >
                      ({result.intervention.confidence_delta >= 0 ? "+" : ""}
                      {(result.intervention.confidence_delta * 100).toFixed(1)}
                      pt)
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {result.intervention && (
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-xs font-semibold text-gray-500 mb-2">
                Intervention Metrics
              </h3>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">User concepts active</span>
                  <span className="font-medium">
                    {result.intervention.user_concept_active}/
                    {result.intervention.user_concept_count}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Success rate</span>
                  <span className="font-medium">
                    {(result.intervention.success_rate * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">User share (α)</span>
                  <span className="font-medium">
                    {(result.intervention.contribution_ratio * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Bank reconstr ‖·‖</span>
                  <span className="font-mono text-xs">
                    {result.intervention.bank_reconstr_norm.toFixed(3)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">User reconstr ‖·‖</span>
                  <span className="font-mono text-xs">
                    {result.intervention.user_reconstr_norm.toFixed(3)}
                  </span>
                </div>
              </div>
            </div>
          )}

          {result.labels && result.labels.length > 0 && (
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h3 className="text-xs font-semibold text-gray-500 mb-2">
                Label Scores
              </h3>
              {result.labels.map((l) => (
                <div key={l.name} className="flex justify-between py-1">
                  <span className="text-sm text-gray-700 capitalize">
                    {l.name}
                  </span>
                  <span className="text-sm font-medium text-gray-900">
                    {(l.score * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {isHybrid ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ConceptChart
            concepts={result.user_contributions || []}
            title="Your Concepts (intervention)"
            emptyMessage="No user concepts contributed."
          />
          <ConceptChart
            concepts={result.concepts}
            title={`Top Bank Concepts (${result.concepts.length})`}
          />
        </div>
      ) : (
        <ConceptChart concepts={result.concepts} />
      )}
    </div>
  );
}
