import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type ClassifyResponse } from "../api/client";
import ResultView from "../components/ResultView";

export default function DetailPage() {
  const { id } = useParams<{ id: string }>();
  const [result, setResult] = useState<ClassifyResponse | null>(null);

  useEffect(() => {
    if (id) api.getClassification(Number(id)).then(setResult);
  }, [id]);

  if (!result) {
    return <p className="text-center text-gray-500 mt-12">Loading...</p>;
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <Link
        to="/history"
        className="text-sm text-blue-600 hover:underline mb-4 inline-block"
      >
        &larr; Back to History
      </Link>
      <ResultView result={result} />
    </div>
  );
}
