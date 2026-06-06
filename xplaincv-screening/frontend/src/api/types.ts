// Mirrors backend/app/schemas/*

export interface ConceptIn {
  concept: string
  importance: number
}

export interface ExtractResponse {
  source: string
  concepts: ConceptIn[]
  dropped: string[]
}

export interface ConceptOut {
  id: number
  concept: string
  importance: number
  has_embedding: boolean
}

export interface ReferenceImageOut {
  id: number
  image_url: string
  has_embedding: boolean
}

export interface ProfileSummary {
  id: number
  name: string
  description: string
  threshold_score: number
  num_concepts: number
  num_references: number
  is_built: boolean
  created_at: string
}

export interface ProfileDetail extends ProfileSummary {
  concepts: ConceptOut[]
  reference_images: ReferenceImageOut[]
  calibration: {
    method: string
    proto_lo: number
    proto_hi: number
    ref_scores: number[]
  } | null
}

export interface BatchCreateResponse {
  batch_id: number
  status: string
  total_images: number
}

export interface BatchSummary {
  id: number
  profile_id: number
  profile_name: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  total_images: number
  processed: number
  accepted: number
  rejected: number
  error: string | null
  created_at: string
}

export interface ResultSummary {
  id: number
  batch_id: number
  image_url: string
  final_decision: 'ACCEPTED' | 'REJECTED'
  confidence_score: number
  reject_reason: string | null
}

export interface BatchDetail {
  batch: BatchSummary
  threshold_score: number
  results: ResultSummary[]
  page: number
  page_size: number
  total_results: number
}

export interface ConceptScoreRow {
  concept: string
  weight: number
  probability: number
  present: boolean
}

export interface ResultDetail extends ResultSummary {
  profile_id: number
  profile_name: string
  threshold_score: number
  presence_threshold: number
  concept_score: number
  prototype_score: number | null
  coverage: number
  concepts: ConceptScoreRow[]
}

export interface CandidateScore {
  profile_id: number
  profile_name: string
  score: number
  concept_score: number
  prototype_score: number | null
  coverage: number
  num_present: number
  num_concepts: number
  passes_gate: boolean
  concepts: ConceptScoreRow[]
}

export interface VerifyResponse {
  match: CandidateScore | null
  candidates: CandidateScore[]
  presence_threshold: number
  match_threshold: number
}
