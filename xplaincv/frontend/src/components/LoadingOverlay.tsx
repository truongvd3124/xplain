import { useEffect, useState } from "react";

export default function LoadingOverlay() {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 text-center shadow-xl">
        <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="mt-4 text-gray-700 font-medium">Analyzing image...</p>
        <p className="mt-1 text-sm text-gray-500">
          This takes about 12 seconds ({elapsed}s)
        </p>
      </div>
    </div>
  );
}
