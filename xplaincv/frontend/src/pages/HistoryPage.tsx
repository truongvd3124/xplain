import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type PaginatedHistory } from "../api/client";

const MODE_BADGE: Record<string, string> = {
  auto: "bg-gray-100 text-gray-700",
  manual: "bg-purple-100 text-purple-700",
  hybrid: "bg-blue-100 text-blue-700",
};

export default function HistoryPage() {
  const [data, setData] = useState<PaginatedHistory | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    api.getHistory(page).then(setData);
  }, [page]);

  if (!data) {
    return <p className="text-center text-gray-500 mt-12">Loading...</p>;
  }

  if (data.total === 0) {
    return (
      <div className="text-center mt-12">
        <p className="text-gray-500">No classifications yet.</p>
        <Link
          to="/"
          className="inline-block mt-3 text-blue-600 text-sm hover:underline"
        >
          Classify your first image
        </Link>
      </div>
    );
  }

  const totalPages = Math.ceil(data.total / data.page_size);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-4">History</h1>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {data.items.map((item) => (
          <Link
            key={item.id}
            to={`/history/${item.id}`}
            className="border border-gray-200 rounded-xl overflow-hidden hover:shadow-md transition"
          >
            <img
              src={item.image_url}
              alt={item.predicted_class}
              className="w-full h-36 object-cover"
            />
            <div className="p-3">
              <div className="flex items-center justify-between mb-0.5">
                <p className="font-medium text-sm text-gray-900 capitalize truncate">
                  {item.predicted_class}
                </p>
                <span
                  className={`ml-1 px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                    MODE_BADGE[item.mode] || "bg-gray-100"
                  }`}
                >
                  {item.mode}
                </span>
              </div>
              <p className="text-xs text-gray-500">
                {(item.confidence * 100).toFixed(1)}%
              </p>
            </div>
          </Link>
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2 mt-6">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-3 py-1 text-sm border rounded disabled:opacity-40"
          >
            Prev
          </button>
          <span className="px-3 py-1 text-sm text-gray-600">
            {page} / {totalPages}
          </span>
          <button
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-3 py-1 text-sm border rounded disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
