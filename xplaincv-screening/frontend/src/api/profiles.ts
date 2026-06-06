import { del, getJson, postForm, postJson } from './client'
import type {
  ConceptIn,
  ExtractResponse,
  ProfileDetail,
  ProfileSummary,
} from './types'

export const extractConcepts = (name: string, description: string) =>
  postJson<ExtractResponse>('/api/profiles/extract-concepts', { name, description })

export const listProfiles = () => getJson<ProfileSummary[]>('/api/profiles')

export const getProfile = (id: number) => getJson<ProfileDetail>(`/api/profiles/${id}`)

export const createProfile = (name: string, description: string, concepts: ConceptIn[]) =>
  postJson<ProfileDetail>('/api/profiles', { name, description, concepts })

export const deleteProfile = (id: number) => del(`/api/profiles/${id}`)

export const addReferenceImages = (id: number, files: File[]) => {
  const form = new FormData()
  files.forEach((f) => form.append('files', f))
  return postForm<ProfileDetail>(`/api/profiles/${id}/reference-images`, form)
}

export const buildProfile = (id: number) =>
  postJson<ProfileDetail>(`/api/profiles/${id}/build`, {})
