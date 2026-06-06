export type Mode = "auto" | "manual" | "hybrid";

export interface ConceptScore {
  name: string;
  score: number;
  source?: "bank" | "user" | null;
}

export interface LabelScore {
  name: string;
  score: number;
}

export interface InterventionMetrics {
  user_concept_count: number;
  user_concept_active: number;
  success_rate: number;
  contribution_ratio: number;
  alpha: number;
  bank_reconstr_norm: number;
  user_reconstr_norm: number;
  changed_prediction: boolean;
  confidence_delta: number;
  agreement: boolean;
}

export interface BankOnlyPrediction {
  predicted_class: string;
  confidence: number;
}

export interface ClassifyResponse {
  id: number;
  mode: Mode;
  predicted_class: string;
  confidence: number;
  feat_gap: number;
  concepts: ConceptScore[];
  user_contributions?: ConceptScore[] | null;
  dataset?: string | null;
  labels?: LabelScore[] | null;
  user_concepts?: string[] | null;
  intervention?: InterventionMetrics | null;
  bank_only?: BankOnlyPrediction | null;
  inference_time_ms: number;
  image_url: string;
  created_at: string;
}

export interface DatasetInfo {
  name: string;
  display_name: string;
  num_classes: number;
}

export interface HistoryItem {
  id: number;
  mode: string;
  predicted_class: string;
  confidence: number;
  image_url: string;
  created_at: string;
}

export interface PaginatedHistory {
  items: HistoryItem[];
  total: number;
  page: number;
  page_size: number;
}

interface ClassifyParams {
  mode: Mode;
  image: File;
  dataset?: string;
  concepts?: string[];
  labels?: string[];
  alpha?: number;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error((await res.text()) || res.statusText);
  return res.json();
}

export const api = {
  getDatasets: () => request<DatasetInfo[]>("/api/datasets"),

  classify: (params: ClassifyParams) => {
    const form = new FormData();
    form.append("mode", params.mode);
    form.append("image", params.image);
    if (params.dataset) form.append("dataset", params.dataset);
    if (params.concepts?.length) form.append("concepts", params.concepts.join(","));
    if (params.labels?.length) form.append("labels", params.labels.join(","));
    if (params.alpha !== undefined) form.append("alpha", String(params.alpha));
    return request<ClassifyResponse>("/api/classify", {
      method: "POST",
      body: form,
    });
  },

  getHistory: (page = 1, pageSize = 20) =>
    request<PaginatedHistory>(`/api/history?page=${page}&page_size=${pageSize}`),

  getClassification: (id: number) =>
    request<ClassifyResponse>(`/api/history/${id}`),
};
