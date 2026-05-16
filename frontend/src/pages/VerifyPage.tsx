import { useEffect, useState } from "react";
import { api, type ProfileSummary, type VerifyResult } from "../api/client";
import ImageUploader from "../components/ImageUploader";
import LoadingOverlay from "../components/LoadingOverlay";
import VerifyResultView from "../components/VerifyResultView";

// Tab 2: upload an image, predict the best-matching class from all profiles.
export default function VerifyPage() {
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<VerifyResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.listProfiles().then(setProfiles);
  }, []);

  const handleVerify = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      setResult(await api.verify(file));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Verification failed");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setFile(null);
    setResult(null);
    setError("");
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <header>
        <h1 className="text-2xl font-bold text-gray-900">Predict an image</h1>
      </header>

      {profiles.length === 0 ? (
        <p className="text-sm text-gray-500 bg-amber-50 border border-amber-200 rounded-lg p-4">
          No profiles yet. Create one in the Builder tab first.
        </p>
      ) : !result ? (
        <div className="space-y-4">
          <p className="text-xs text-gray-500">
            Comparing against {profiles.length} profile
            {profiles.length !== 1 ? "s" : ""}:{" "}
            <span className="text-gray-700">
              {profiles.map((p) => p.class_name).join(", ")}
            </span>
          </p>

          <ImageUploader onFileSelect={setFile} selectedFile={file} />

          <button
            onClick={handleVerify}
            disabled={!file || loading}
            className="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm
                       font-medium hover:bg-blue-700 disabled:opacity-50 transition"
          >
            Predict
          </button>

          {error && (
            <p className="text-red-600 text-sm bg-red-50 rounded-lg p-3">
              {error}
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="grid grid-cols-[200px_1fr] gap-5">
            <img
              src={result.image_url}
              alt="verified"
              className="w-full rounded-xl border border-gray-200 object-cover"
            />
            <VerifyResultView result={result} />
          </div>
          <button
            onClick={reset}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm
                       text-gray-700 hover:bg-gray-50 transition"
          >
            Predict another image
          </button>
        </div>
      )}

      {loading && <LoadingOverlay message="Predicting..." />}
    </div>
  );
}
