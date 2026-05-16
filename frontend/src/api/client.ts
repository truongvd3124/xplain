// API client + shared types. Mirrors backend/app/schemas.py.

export interface Concept {
  concept: string;
  importance: number; // 1-5
}

export interface ExtractResult {
  concepts: Concept[];
  source: "llm" | "unavailable";
}

export interface ProfileSummary {
  id: string;
  class_name: string;
  description: string;
  num_concepts: number;
  num_references: number;
  created_at: string;
}

export interface Calibration {
  method: string;
  proto_lo: number;
  proto_hi: number;
  ref_scores: number[];
}

export interface ProfileDetail extends ProfileSummary {
  concepts: Concept[];
  calibration: Calibration;
}

export interface ConceptPresence {
  concept: string;
  importance: number;
  probability: number;
  present: boolean;
}

export interface CandidateScore {
  profile_id: string;
  class_name: string;
  score: number;
  concept_score: number;
  prototype_score: number | null;
  num_present: number;
  num_concepts: number;
}

export interface VerifyResult {
  decision: "match" | "no_match";
  predicted: CandidateScore | null;
  concepts: ConceptPresence[]; // breakdown for the predicted class
  ranking: CandidateScore[]; // every profile, sorted desc
  threshold: number; // global MATCH_THRESHOLD
  image_url: string;
  inference_time_ms: number;
}

export interface Health {
  status: string;
  llm_available: boolean;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    // FastAPI errors arrive as {"detail": "..."}; fall back to raw text.
    let message = res.statusText;
    try {
      const body = await res.json();
      message = body.detail ?? message;
    } catch {
      /* keep statusText */
    }
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  getHealth: () => request<Health>("/api/health"),

  extract: (class_name: string, description: string) =>
    request<ExtractResult>("/api/extract", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ class_name, description }),
    }),

  listProfiles: () => request<ProfileSummary[]>("/api/profiles"),

  getProfile: (id: string) => request<ProfileDetail>(`/api/profiles/${id}`),

  createProfile: (
    class_name: string,
    description: string,
    concepts: Concept[],
    images: File[]
  ) => {
    const form = new FormData();
    form.append("class_name", class_name);
    form.append("description", description);
    form.append("concepts", JSON.stringify(concepts));
    images.forEach((img) => form.append("images", img));
    return request<ProfileDetail>("/api/profiles", {
      method: "POST",
      body: form,
    });
  },

  deleteProfile: (id: string) =>
    request<{ deleted: string }>(`/api/profiles/${id}`, { method: "DELETE" }),

  verify: (image: File) => {
    const form = new FormData();
    form.append("image", image);
    return request<VerifyResult>("/api/verify", {
      method: "POST",
      body: form,
    });
  },
};
