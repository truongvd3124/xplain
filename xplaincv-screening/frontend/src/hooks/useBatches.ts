import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '../api/batches'

const isActive = (status?: string) => status === 'pending' || status === 'processing'

/** Batch list; polls while any batch is still in flight. */
export const useBatches = () =>
  useQuery({
    queryKey: ['batches'],
    queryFn: api.listBatches,
    refetchInterval: (query) =>
      query.state.data?.some((b) => isActive(b.status)) ? 1500 : false,
  })

/** One batch with paginated results; polls while it is pending/processing. */
export const useBatch = (id: number, page: number) =>
  useQuery({
    queryKey: ['batches', id, page],
    queryFn: () => api.getBatch(id, page),
    refetchInterval: (query) =>
      isActive(query.state.data?.batch.status) ? 1500 : false,
  })

export const useResult = (id: number) =>
  useQuery({ queryKey: ['results', id], queryFn: () => api.getResult(id) })

export function useCreateBatch() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ profileId, files }: { profileId: number; files: File[] }) =>
      api.createBatch(profileId, files),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['batches'] }),
  })
}
