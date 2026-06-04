import { useCallback, useState } from "react";

interface Props {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
}

export default function ImageUploader({ onFileSelect, selectedFile }: Props) {
  const [dragOver, setDragOver] = useState(false);
  const preview = selectedFile ? URL.createObjectURL(selectedFile) : null;

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file?.type.startsWith("image/")) onFileSelect(file);
    },
    [onFileSelect]
  );

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelect(file);
  };

  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={handleDrop}
      className={`group relative block rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 border-2 border-dashed ${
        dragOver
          ? "border-violet-400 bg-violet-500/10 scale-[1.01]"
          : "border-black/10 hover:border-violet-400/60 hover:bg-black/[0.03]"
      }`}
    >
      <input
        type="file"
        accept="image/*"
        onChange={handleChange}
        className="hidden"
      />
      {preview ? (
        <img
          src={preview}
          alt="Preview"
          className="max-h-72 mx-auto rounded-xl shadow-xl shadow-indigo-900/15 animate-pop"
        />
      ) : (
        <div className="text-[var(--ink-soft)] py-4">
          <span className="mx-auto mb-3 grid place-items-center w-14 h-14 rounded-2xl bg-black/[0.04] border border-black/10 text-violet-600 transition-transform duration-300 group-hover:-translate-y-0.5 group-hover:scale-105">
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden>
              <path d="M12 16V4m0 0L8 8m4-4l4 4" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" />
              <path d="M4 15v2.5A2.5 2.5 0 006.5 20h11a2.5 2.5 0 002.5-2.5V15" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
            </svg>
          </span>
          <p className="text-base font-semibold text-[var(--ink)]">Drop an image here</p>
          <p className="text-sm mt-1">or click to browse</p>
        </div>
      )}
    </label>
  );
}
