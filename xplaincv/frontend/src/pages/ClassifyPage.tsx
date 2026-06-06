import { useEffect, useState } from "react";
import {
  api,
  type ClassifyResponse,
  type DatasetInfo,
  type Mode,
} from "../api/client";
import ImageUploader from "../components/ImageUploader";
import LoadingOverlay from "../components/LoadingOverlay";
import PresetSelector from "../components/PresetSelector";
import ResultView from "../components/ResultView";
import TagInput from "../components/TagInput";
import type { Preset } from "../data/presets";

const TABS: { id: Mode; label: string; description: string }[] = [
  {
    id: "auto",
    label: "Auto (ZCBM)",
    description:
      "Original ZCBM: bank search retrieves concepts automatically for classification.",
  },
  {
    id: "manual",
    label: "Manual",
    description:
      "User defines concepts AND labels. No concept bank used at all.",
  },
  {
    id: "hybrid",
    label: "Hybrid (Intervention)",
    description:
      "Bank search + user concepts merged. Measures how user concepts intervene in ZCBM.",
  },
];

export default function ClassifyPage() {
  const [mode, setMode] = useState<Mode>("auto");
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [dataset, setDataset] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [concepts, setConcepts] = useState<string[]>([]);
  const [labels, setLabels] = useState<string[]>([]);
  const [alpha, setAlpha] = useState(0.5);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ClassifyResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.getDatasets().then((ds) => {
      setDatasets(ds);
      const food = ds.find((d) => d.name === "food101");
      setDataset(food ? food.name : ds[0]?.name || "");
    });
  }, []);

  const canSubmit = (() => {
    if (!file || loading) return false;
    if (mode === "auto") return !!dataset;
    if (mode === "manual") return concepts.length > 0 && labels.length >= 2;
    if (mode === "hybrid") return !!dataset && concepts.length > 0;
    return false;
  })();

  const handleSubmit = async () => {
    if (!canSubmit || !file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.classify({
        mode,
        image: file,
        dataset: mode !== "manual" ? dataset : undefined,
        concepts: mode !== "auto" ? concepts : undefined,
        labels: mode === "manual" ? labels : undefined,
        alpha: mode === "hybrid" ? alpha : undefined,
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Classification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setResult(null);
    setError("");
  };

  const switchTab = (newMode: Mode) => {
    if (newMode === mode) return;
    setMode(newMode);
    setResult(null);
    setError("");
  };

  const applyPreset = (preset: Preset) => {
    setConcepts(preset.concepts);
    if (mode === "manual") setLabels(preset.labels);
  };

  const activeTab = TABS.find((t) => t.id === mode)!;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">XplainCV</h1>
      <p className="text-gray-500 text-sm mb-5">
        Zero-shot explainable classification - compare 3 modes side by side.
      </p>

      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {TABS.map((t) => (
          <button
            key={t.id}
            onClick={() => switchTab(t.id)}
            className={`px-5 py-2.5 text-sm font-medium border-b-2 transition -mb-px ${
              mode === t.id
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      <p className="text-xs text-gray-500 mb-5 italic">
        {activeTab.description}
      </p>

      {!result ? (
        <div className="space-y-4">
          <ImageUploader onFileSelect={setFile} selectedFile={file} />

          {(mode === "auto" || mode === "hybrid") && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Dataset (Classnames)
              </label>
              <select
                value={dataset}
                onChange={(e) => setDataset(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
              >
                {datasets.map((d) => (
                  <option key={d.name} value={d.name}>
                    {d.display_name} ({d.num_classes} classes)
                  </option>
                ))}
              </select>
            </div>
          )}

          {(mode === "manual" || mode === "hybrid") && (
            <>
              <PresetSelector
                onApply={applyPreset}
                includeLabels={mode === "manual"}
              />
              <TagInput
                tags={concepts}
                onChange={setConcepts}
                label={
                  mode === "hybrid"
                    ? "Your Concepts (intervention)"
                    : "Concepts"
                }
                placeholder='e.g. "has fur", "four legs", "whiskers"'
                color="blue"
              />
            </>
          )}

          {mode === "manual" && (
            <TagInput
              tags={labels}
              onChange={setLabels}
              label="Candidate Labels (min 2)"
              placeholder='e.g. "cat", "dog", "bird"'
              color="purple"
            />
          )}

          {mode === "hybrid" && (
            <div>
              <div className="flex items-baseline justify-between mb-1.5">
                <label className="text-sm font-medium text-gray-700">
                  Intervention weight α
                </label>
                <span className="text-xs font-mono text-blue-600">
                  {alpha.toFixed(2)}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={alpha}
                onChange={(e) => setAlpha(parseFloat(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-[10px] text-gray-400 mt-1">
                <span>0 = pure bank</span>
                <span>0.5 = balanced</span>
                <span>1 = pure user</span>
              </div>
            </div>
          )}

          <button
            onClick={handleSubmit}
            disabled={!canSubmit}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            Classify
          </button>

          {error && (
            <p className="text-red-600 text-sm bg-red-50 rounded-lg p-3">
              {error}
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <ResultView result={result} />
          <button
            onClick={handleReset}
            className="mt-2 px-4 py-2 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition"
          >
            Try Another Image
          </button>
        </div>
      )}

      {loading && <LoadingOverlay />}
    </div>
  );
}
