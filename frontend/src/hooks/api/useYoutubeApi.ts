import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, YoutubeBatchesService, YoutubeCreditsService, YoutubeLeadsService } from '@/client'

export type BatchStatus = 'queued' | 'running' | 'paused' | 'completed' | 'finalized' | 'failed'
export type TermStatus = 'pending' | 'running' | 'done' | 'failed'

export interface SearchTermItem {
  _id: string
  term: string
  status: TermStatus
  creditsUsed?: number
  emailsFound?: number
  errorMessage?: string | null
}

export interface BatchItem {
  _id: string
  name: string
  keyword: string
  totalTerms: number
  processedTerms: number
  status: BatchStatus
  createdAt: string
}

export interface BatchDetail extends BatchItem {
  terms: SearchTermItem[]
}

export interface CreditsToday {
  used: number
  remaining: number
  limit: number
  activeBatchId: string | null
  resetAt: string
}

export interface LeadItem {
  _id: string
  channelName?: string
  channelUrl?: string
  subscribers?: number
  email?: string | null
  score?: number
  emailStatus?: string
}

export interface LeadsPage {
  leads: LeadItem[]
  total: number
  page: number
  pageSize: number
}

export interface CreateBatchInput {
  name: string
  keyword: string
  terms: string
  filters: {
    minSubs: number
    maxSubs: number
    minUploadsLast30d: number
    minAvgViews: number
    excludeCountries: string[]
    region: string
  }
}

export const youtubeKeys = {
  all: ['youtube'] as const,
  batches: () => [...youtubeKeys.all, 'batches'] as const,
  batch: (batchId: string) => [...youtubeKeys.batches(), batchId] as const,
  leads: (batchId: string, page: number, pageSize: number) =>
    [...youtubeKeys.batch(batchId), 'leads', page, pageSize] as const,
  credits: () => [...youtubeKeys.all, 'credits', 'today'] as const,
}

export function getApiErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'Unable to reach server. Please try again.'
  }
  const body = error.body as { detail?: string; message?: string } | undefined
  return body?.detail ?? body?.message ?? `Request failed (${error.status})`
}

export function useBatchesQuery() {
  return useQuery({
    queryKey: youtubeKeys.batches(),
    queryFn: async () => (await YoutubeBatchesService.listBatchesApiV1YoutubeBatchesGet()) as BatchItem[],
  })
}

export function useBatchDetailQuery(batchId?: string, pollMs = 0) {
  return useQuery({
    queryKey: youtubeKeys.batch(batchId ?? ''),
    queryFn: async () =>
      (await YoutubeBatchesService.getBatchApiV1YoutubeBatchesBatchIdGet(batchId ?? '')) as BatchDetail,
    enabled: Boolean(batchId),
    refetchInterval: pollMs > 0 ? pollMs : false,
  })
}

export function useBatchLeadsQuery(batchId?: string, page = 1, pageSize = 50, pollMs = 0) {
  return useQuery({
    queryKey: youtubeKeys.leads(batchId ?? '', page, pageSize),
    queryFn: async () =>
      (await YoutubeLeadsService.listLeadsApiV1YoutubeBatchesBatchIdLeadsGet(
        batchId ?? '',
        page,
        pageSize,
      )) as LeadsPage,
    enabled: Boolean(batchId),
    refetchInterval: pollMs > 0 ? pollMs : false,
  })
}

export function useCreditsTodayQuery(pollMs = 0) {
  return useQuery({
    queryKey: youtubeKeys.credits(),
    queryFn: async () =>
      (await YoutubeCreditsService.getCreditsTodayApiV1YoutubeCreditsTodayGet()) as CreditsToday,
    refetchInterval: pollMs > 0 ? pollMs : false,
  })
}

export function useCreateBatchMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: CreateBatchInput) =>
      YoutubeBatchesService.createBatchApiV1YoutubeBatchesPost(input).then((data) => data as BatchItem),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: youtubeKeys.batches() })
      void qc.invalidateQueries({ queryKey: youtubeKeys.credits() })
    },
  })
}

export function useTriggerBatchMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (batchId: string) =>
      YoutubeBatchesService.triggerBatchApiV1YoutubeBatchesBatchIdTriggerPost(batchId),
    onMutate: (batchId) => {
      qc.setQueryData<CreditsToday | undefined>(youtubeKeys.credits(), (prev) =>
        prev ? { ...prev, activeBatchId: batchId } : prev,
      )
      qc.setQueryData<BatchItem[] | undefined>(youtubeKeys.batches(), (prev) =>
        prev?.map((b) => (b._id === batchId ? { ...b, status: 'running' } : b)),
      )
      qc.setQueryData<BatchDetail | undefined>(youtubeKeys.batch(batchId), (prev) =>
        prev ? { ...prev, status: 'running' } : prev,
      )
    },
    onSuccess: (_, batchId) => {
      void qc.invalidateQueries({ queryKey: youtubeKeys.batch(batchId) })
      void qc.invalidateQueries({ queryKey: youtubeKeys.batches() })
      void qc.invalidateQueries({ queryKey: youtubeKeys.credits() })
    },
  })
}

export function useDeleteBatchMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (batchId: string) => YoutubeBatchesService.deleteBatchApiV1YoutubeBatchesBatchIdDelete(batchId),
    onSuccess: (_, batchId) => {
      void qc.invalidateQueries({ queryKey: youtubeKeys.batches() })
      void qc.invalidateQueries({ queryKey: youtubeKeys.credits() })
      void qc.removeQueries({ queryKey: youtubeKeys.batch(batchId) })
    },
  })
}

export function useFinalizeBatchMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (batchId: string) => {
      const response = await fetch(`/api/v1/youtube/batches/${batchId}/finalize`, { method: 'POST' })
      if (!response.ok) {
        const body = await response.json().catch(() => ({}))
        throw new Error(body?.detail ?? `Finalize failed (${response.status})`)
      }
      return response.json() as Promise<{ message: string; duplicatesRemoved: number }>
    },
    onSuccess: (_, batchId) => {
      void qc.invalidateQueries({ queryKey: youtubeKeys.batch(batchId) })
      void qc.invalidateQueries({ queryKey: youtubeKeys.batches() })
      void qc.invalidateQueries({ queryKey: youtubeKeys.leads(batchId, 1, 50) })
    },
  })
}

export function useExportBatchMutation() {
  return useMutation({
    mutationFn: async (batchId: string) => {
      const response = await fetch(`/api/v1/youtube/batches/${batchId}/export`)
      if (!response.ok) throw new Error('Export failed')
      const blob = await response.blob()
      const disposition = response.headers.get('Content-Disposition') ?? ''
      const match = disposition.match(/filename="([^"]+)"/)
      const filename = match ? match[1] : `leads_${batchId}.csv`
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      URL.revokeObjectURL(url)
    },
  })
}
