import { useState } from "react";

interface Props {
  tags: string[];
  onChange: (tags: string[]) => void;
  label: string;
  placeholder: string;
  max?: number;
  color?: "blue" | "purple";
}

export default function TagInput({
  tags,
  onChange,
  label,
  placeholder,
  max = 50,
  color = "blue",
}: Props) {
  const [input, setInput] = useState("");

  const colors = {
    blue: {
      tag: "bg-blue-50 text-blue-700 border-blue-200",
      hover: "hover:text-blue-700",
      btn: "bg-blue-600 hover:bg-blue-700",
    },
    purple: {
      tag: "bg-purple-50 text-purple-700 border-purple-200",
      hover: "hover:text-purple-700",
      btn: "bg-purple-600 hover:bg-purple-700",
    },
  }[color];

  const addTag = (text: string) => {
    const trimmed = text.trim().toLowerCase();
    if (trimmed && !tags.includes(trimmed) && tags.length < max) {
      onChange([...tags, trimmed]);
    }
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addTag(input);
    }
  };

  return (
    <div className="space-y-2">
      <span className="block text-sm font-medium text-gray-700">
        {label} ({tags.length}/{max})
      </span>

      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => addTag(input)}
          disabled={!input.trim()}
          className={`px-4 py-2 text-white rounded-lg text-sm font-medium disabled:opacity-50 transition ${colors.btn}`}
        >
          Add
        </button>
      </div>

      {tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {tags.map((t, i) => (
            <span
              key={i}
              className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm border ${colors.tag}`}
            >
              {t}
              <button
                onClick={() => onChange(tags.filter((_, j) => j !== i))}
                className={`ml-0.5 opacity-50 ${colors.hover} font-bold`}
              >
                x
              </button>
            </span>
          ))}
        </div>
      )}

    </div>
  );
}
