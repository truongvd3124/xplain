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
      className={`block border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${
        dragOver
          ? "border-blue-500 bg-blue-50"
          : "border-gray-300 hover:border-gray-400"
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
          className="max-h-64 mx-auto rounded-lg"
        />
      ) : (
        <div className="text-gray-500">
          <p className="text-lg font-medium">Drop an image here</p>
          <p className="text-sm mt-1">or click to browse</p>
        </div>
      )}
    </label>
  );
}
