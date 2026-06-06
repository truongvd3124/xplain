import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import * as api from '../api/profiles'
import type { ConceptIn } from '../api/types'

export const useProfiles = () =>
  useQuery({ queryKey: ['profiles'], queryFn: api.listProfiles })

export const useProfile = (id: number | null) =>
  useQuery({
    queryKey: ['profiles', id],
    queryFn: () => api.getProfile(id!),
    enabled: id != null,
  })

export function useExtractConcepts() {
  return useMutation({
    mutationFn: ({ name, description }: { name: string; description: string }) =>
      api.extractConcepts(name, description),
  })
}

export function useCreateProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      name,
      description,
      concepts,
    }: {
      name: string
      description: string
      concepts: ConceptIn[]
    }) => api.createProfile(name, description, concepts),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profiles'] }),
  })
}

export function useAddReferenceImages() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, files }: { id: number; files: File[] }) =>
      api.addReferenceImages(id, files),
    onSuccess: (_d, { id }) => qc.invalidateQueries({ queryKey: ['profiles', id] }),
  })
}

export function useBuildProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.buildProfile(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profiles'] }),
  })
}

export function useDeleteProfile() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api.deleteProfile(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['profiles'] }),
  })
}
