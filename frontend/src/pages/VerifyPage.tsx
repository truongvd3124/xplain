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
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
      <header className="animate-fade-up">
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-black/[0.04] border border-black/10 text-violet-600">
          Step 2
        </span>
        <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
          Predict an <span className="text-gradient">image</span>
        </h1>
        <p className="mt-1.5 text-sm text-[var(--ink-soft)]">
          Upload a photo and the model verifies it against your saved class profiles.
        </p>
      </header>

      {profiles.length === 0 ? (
        <p className="glass rounded-2xl p-5 text-sm text-amber-700 animate-fade-up">
          No profiles yet. Create one in the Builder tab first.
        </p>
      ) : !result ? (
        <div className="glass glass-hover rounded-2xl p-5 space-y-4 animate-fade-up">
          <ImageUploader onFileSelect={setFile} selectedFile={file} />

          <button
            onClick={handleVerify}
            disabled={!file || loading}
            className="btn-grad w-full py-3 text-white rounded-xl text-sm font-semibold"
          >
            Predict
          </button>

          {error && (
            <p className="text-red-600 text-sm bg-red-500/10 border border-red-400/20 rounded-xl p-3">
              {error}
            </p>
          )}
        </div>
      ) : (
        <div className="space-y-4 animate-fade-up">
          <div className="grid grid-cols-[220px_1fr] gap-5 max-sm:grid-cols-1">
            <img
              src={result.image_url}
              alt="verified"
              className="w-full rounded-2xl border border-black/10 object-cover shadow-xl shadow-indigo-900/15 animate-pop"
            />
            <VerifyResultView result={result} />
          </div>
          <button
            onClick={reset}
            className="px-4 py-2 border border-black/10 rounded-xl text-sm
                       text-[var(--ink-soft)] hover:text-[var(--ink)] hover:border-violet-400/50 hover:bg-black/[0.04] transition"
          >
            ← Predict another image
          </button>
        </div>
      )}

      {loading && <LoadingOverlay message="Predicting..." />}
    </div>
  );
}
