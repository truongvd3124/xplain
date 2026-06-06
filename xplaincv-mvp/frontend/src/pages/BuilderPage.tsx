import { useEffect, useState } from "react";
import {
  api,
  type Concept,
  type ProfileSummary,
} from "../api/client";
import ConceptEditor from "../components/ConceptEditor";
import LoadingOverlay from "../components/LoadingOverlay";
import MultiImageUploader from "../components/MultiImageUploader";

// Tab 1: build a class profile -- describe a class, let AI extract visual
// concepts, attach reference images, and save it for later verification.
export default function BuilderPage() {
  const [className, setClassName] = useState("");
  const [description, setDescription] = useState("");
  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [images, setImages] = useState<File[]>([]);

  const [llmAvailable, setLlmAvailable] = useState(false);
  const [profiles, setProfiles] = useState<ProfileSummary[]>([]);
  const [showProfiles, setShowProfiles] = useState(false);
  const [extracting, setExtracting] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const refreshProfiles = () => api.listProfiles().then(setProfiles);

  useEffect(() => {
    api.getHealth().then((h) => setLlmAvailable(h.llm_available));
    refreshProfiles();
  }, []);

  const handleExtract = async () => {
    setError("");
    setNotice("");
    setExtracting(true);
    try {
      const result = await api.extract(className, description);
      if (result.source === "unavailable") {
        setNotice("AI extraction is off (no API key). Add concepts manually below.");
      } else if (result.concepts.length === 0) {
        setNotice("The AI returned no usable concepts. Try a richer description.");
      } else {
        // Merge, skipping concepts already in the list.
        const existing = new Set(concepts.map((c) => c.concept));
        const merged = [
          ...concepts,
          ...result.concepts.filter((c) => !existing.has(c.concept)),
        ];
        setConcepts(merged);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Extraction failed");
    } finally {
      setExtracting(false);
    }
  };

  const handleSave = async () => {
    setError("");
    setNotice("");
    setSaving(true);
    try {
      const profile = await api.createProfile(
        className,
        description,
        concepts,
        images
      );
      setNotice(
        `Saved profile "${profile.class_name}" ` +
          `(${profile.num_concepts} concepts, ${profile.num_references} images).`
      );
      setClassName("");
      setDescription("");
      setConcepts([]);
      setImages([]);
      refreshProfiles();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    await api.deleteProfile(id);
    refreshProfiles();
  };

  const canSave = className.trim() !== "" && concepts.length > 0 && !saving;

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Build a class profile</h1>
        </div>
        <button
          type="button"
          onClick={() => setShowProfiles(true)}
          title="Saved profiles"
          className="shrink-0 flex items-center gap-2 px-3 py-2 border border-gray-300
                     rounded-lg text-sm text-gray-700 hover:bg-gray-50 transition"
        >
          <span aria-hidden className="text-base leading-none">⚙</span>
          Saved profiles
          <span className="inline-flex items-center justify-center min-w-5 h-5 px-1.5
                           text-xs font-medium rounded-full bg-blue-100 text-blue-700">
            {profiles.length}
          </span>
        </button>
      </header>

      <section className="bg-white border border-gray-200 rounded-xl p-5 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Class name
          </label>
          <input
            type="text"
            value={className}
            onChange={(e) => setClassName(e.target.value)}
            placeholder='e.g. "dog"'
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="A dog has floppy or pointed ears, a furry coat, four legs, a snout and a tail..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm
                       focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="button"
            onClick={handleExtract}
            disabled={!description.trim() || extracting}
            className="mt-2 px-4 py-2 bg-amber-500 text-white rounded-lg text-sm
                       font-medium hover:bg-amber-600 disabled:opacity-50 transition"
          >
            {extracting ? "Extracting..." : "Extract concepts with AI"}
          </button>
          {!llmAvailable && (
            <span className="ml-2 text-xs text-gray-400">
              AI key not configured - you can still add concepts by hand.
            </span>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Visual concepts ({concepts.length})
          </label>
          <ConceptEditor concepts={concepts} onChange={setConcepts} />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            Reference images (optional)
          </label>
          <MultiImageUploader files={images} onChange={setImages} />
        </div>

        <button
          type="button"
          onClick={handleSave}
          disabled={!canSave}
          className="w-full py-2.5 bg-blue-600 text-white rounded-lg text-sm
                     font-medium hover:bg-blue-700 disabled:opacity-50 transition"
        >
          Save profile
        </button>

        {error && (
          <p className="text-red-600 text-sm bg-red-50 rounded-lg p-3">{error}</p>
        )}
        {notice && (
          <p className="text-green-700 text-sm bg-green-50 rounded-lg p-3">
            {notice}
          </p>
        )}
      </section>

      {showProfiles && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4"
          onClick={() => setShowProfiles(false)}
        >
          <div
            className="w-full max-w-lg max-h-[80vh] overflow-y-auto bg-white rounded-xl
                       shadow-xl p-5 space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-gray-900">
                Saved profiles ({profiles.length})
              </h2>
              <button
                onClick={() => setShowProfiles(false)}
                title="Close"
                className="text-gray-400 hover:text-gray-700 text-xl leading-none"
              >
                ×
              </button>
            </div>

            {profiles.length === 0 ? (
              <p className="text-sm text-gray-400 italic">No profiles yet.</p>
            ) : (
              <ul className="space-y-2">
                {profiles.map((p) => (
                  <li
                    key={p.id}
                    className="flex items-center gap-3 border border-gray-200
                               rounded-lg px-4 py-3"
                  >
                    <div className="flex-1">
                      <span className="font-medium text-gray-900">
                        {p.class_name}
                      </span>
                      <span className="text-xs text-gray-400 ml-2">
                        {p.num_concepts} concepts · {p.num_references} images
                      </span>
                    </div>
                    <button
                      onClick={() => handleDelete(p.id)}
                      className="text-xs text-gray-400 hover:text-red-600"
                    >
                      Delete
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {(extracting || saving) && <LoadingOverlay />}
    </div>
  );
}
