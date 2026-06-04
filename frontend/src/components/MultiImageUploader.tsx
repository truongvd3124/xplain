import { useCallback, useState } from "react";

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
  max?: number;
}

// Multi-image picker for reference images, with thumbnail previews.
export default function MultiImageUploader({
  files,
  onChange,
  max = 15,
}: Props) {
  const [dragOver, setDragOver] = useState(false);

  const addFiles = useCallback(
    (incoming: FileList | null) => {
      if (!incoming) return;
      const images = Array.from(incoming).filter((f) =>
        f.type.startsWith("image/")
      );
      onChange([...files, ...images].slice(0, max));
    },
    [files, onChange, max]
  );

  const removeAt = (index: number) =>
    onChange(files.filter((_, i) => i !== index));

  return (
    <div className="space-y-2">
      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          addFiles(e.dataTransfer.files);
        }}
        className={`block rounded-2xl p-5 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
          dragOver
            ? "border-violet-400 bg-violet-500/10"
            : "border-black/10 hover:border-violet-400/60 hover:bg-black/[0.03]"
        }`}
      >
        <input
          type="file"
          accept="image/*"
          multiple
          onChange={(e) => addFiles(e.target.files)}
          className="hidden"
        />
        <p className="text-sm font-medium text-[var(--ink-soft)]">
          Drop reference images here or click to browse
        </p>
        <p className="text-xs text-[var(--ink-soft)]/60 mt-1">
          <span className="mono text-violet-600">{files.length}/{max}</span> selected · 3+ images enables calibration
        </p>
      </label>

      {files.length > 0 && (
        <div className="grid grid-cols-5 gap-2 stagger">
          {files.map((file, i) => (
            <div key={i} className="relative group">
              <img
                src={URL.createObjectURL(file)}
                alt={`reference ${i + 1}`}
                className="w-full h-20 object-cover rounded-xl border border-black/10 shadow-md shadow-indigo-900/10"
              />
              <button
                type="button"
                onClick={() => removeAt(i)}
                className="absolute -top-1.5 -right-1.5 w-5 h-5 grid place-items-center bg-red-500 text-white
                           rounded-full text-xs font-bold opacity-0 group-hover:opacity-100
                           shadow-lg transition hover:scale-110"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
