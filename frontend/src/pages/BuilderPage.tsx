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
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-6">
      <header className="flex items-end justify-between gap-4 animate-fade-up">
        <div>
          <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-black/[0.04] border border-black/10 text-violet-600">
            Step 1
          </span>
          <h1 className="mt-3 text-3xl font-extrabold tracking-tight text-[var(--ink)]">
            Build a class <span className="text-gradient">profile</span>
          </h1>
          <p className="mt-1.5 text-sm text-[var(--ink-soft)]">
            Describe a class, let AI extract its visual concepts, and save it for verification.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setShowProfiles(true)}
          title="Saved profiles"
          className="shrink-0 flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm
                     text-[var(--ink-soft)] glass glass-hover hover:text-[var(--ink)]"
        >
          <span aria-hidden className="text-base leading-none">⚙</span>
          Saved
          <span className="inline-flex items-center justify-center min-w-5 h-5 px-1.5
                           text-xs font-bold rounded-full brand-gradient text-white">
            {profiles.length}
          </span>
        </button>
      </header>

      <section className="glass glass-hover rounded-2xl p-6 space-y-5 animate-fade-up">
        <div>
          <label className="block text-sm font-semibold text-[var(--ink-soft)] mb-1.5">
            Class name
          </label>
          <input
            type="text"
            value={className}
            onChange={(e) => setClassName(e.target.value)}
            placeholder='e.g. "dog"'
            className="field w-full rounded-xl px-3 py-2 text-sm"
          />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[var(--ink-soft)] mb-1.5">
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="A dog has floppy or pointed ears, a furry coat, four legs, a snout and a tail..."
            className="field w-full rounded-xl px-3 py-2 text-sm resize-none"
          />
          <button
            type="button"
            onClick={handleExtract}
            disabled={!description.trim() || extracting}
            className="btn-grad mt-2 inline-flex items-center gap-2 px-4 py-2 text-white rounded-xl text-sm font-semibold"
          >
            <span aria-hidden>✦</span>
            {extracting ? "Extracting..." : "Extract concepts with AI"}
          </button>
          {!llmAvailable && (
            <span className="ml-2 text-xs text-[var(--ink-soft)]/60">
              AI key not configured — you can still add concepts by hand.
            </span>
          )}
        </div>

        <div>
          <label className="block text-sm font-semibold text-[var(--ink-soft)] mb-1.5">
            Visual concepts{" "}
            <span className="mono text-violet-600">({concepts.length})</span>
          </label>
          <ConceptEditor concepts={concepts} onChange={setConcepts} />
        </div>

        <div>
          <label className="block text-sm font-semibold text-[var(--ink-soft)] mb-1.5">
            Reference images <span className="text-[var(--ink-soft)]/50">(optional)</span>
          </label>
          <MultiImageUploader files={images} onChange={setImages} />
        </div>

        <button
          type="button"
          onClick={handleSave}
          disabled={!canSave}
          className="btn-grad w-full py-3 text-white rounded-xl text-sm font-semibold"
        >
          Save profile
        </button>

        {error && (
          <p className="text-red-600 text-sm bg-red-500/10 border border-red-400/20 rounded-xl p-3 animate-pop">{error}</p>
        )}
        {notice && (
          <p className="text-emerald-700 text-sm bg-emerald-500/10 border border-emerald-400/20 rounded-xl p-3 animate-pop">
            {notice}
          </p>
        )}
      </section>

      {showProfiles && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 animate-fade-in"
          onClick={() => setShowProfiles(false)}
        >
          <div
            className="glass w-full max-w-lg max-h-[80vh] overflow-y-auto rounded-2xl
                       p-6 space-y-4 animate-pop"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-[var(--ink)]">
                Saved profiles{" "}
                <span className="mono text-violet-600">({profiles.length})</span>
              </h2>
              <button
                onClick={() => setShowProfiles(false)}
                title="Close"
                className="grid place-items-center w-8 h-8 rounded-lg text-[var(--ink-soft)]
                           hover:text-[var(--ink)] hover:bg-black/[0.06] text-xl leading-none transition"
              >
                ×
              </button>
            </div>

            {profiles.length === 0 ? (
              <p className="text-sm text-[var(--ink-soft)]/60 italic">No profiles yet.</p>
            ) : (
              <ul className="space-y-2 stagger">
                {profiles.map((p) => (
                  <li
                    key={p.id}
                    className="group flex items-center gap-3 rounded-xl px-4 py-3
                               bg-black/[0.04] border border-black/10 transition-colors hover:border-violet-400/40"
                  >
                    <div className="flex-1">
                      <span className="font-semibold text-[var(--ink)] capitalize">
                        {p.class_name}
                      </span>
                      <span className="text-xs text-[var(--ink-soft)]/60 ml-2 mono">
                        {p.num_concepts} concepts · {p.num_references} images
                      </span>
                    </div>
                    <button
                      onClick={() => handleDelete(p.id)}
                      className="text-xs text-[var(--ink-soft)]/50 hover:text-red-400 transition-colors"
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
