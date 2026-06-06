import { getJson, postForm } from './client'
import type { BatchCreateResponse, BatchDetail, BatchSummary, ResultDetail } from './types'

export const createBatch = (profileId: number, files: File[]) => {
  const form = new FormData()
  form.append('profile_id', String(profileId))
  files.forEach((f) => form.append('files', f))
  return postForm<BatchCreateResponse>('/api/batches', form)
}

export const listBatches = () => getJson<BatchSummary[]>('/api/batches')

export const getBatch = (id: number, page = 1, pageSize = 24) =>
  getJson<BatchDetail>(`/api/batches/${id}?page=${page}&page_size=${pageSize}`)

export const getResult = (id: number) => getJson<ResultDetail>(`/api/results/${id}`)
