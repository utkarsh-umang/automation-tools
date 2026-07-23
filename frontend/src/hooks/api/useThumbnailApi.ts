import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import {
  ThumbnailCreatorService,
  type Body_create_thumbnail_api_v1_thumbnails_thumbnail_post,
  type ThumbnailFeedbackRequest,
  type ThumbnailListResponse,
  type ThumbnailSelectCandidateRequest,
} from '@/client'
import { getApiErrorMessage } from '@/hooks/api/useYoutubeApi'

export { getApiErrorMessage }

/**
 * Thumbnail list pagination: `useInfiniteQuery` + `getNextPageParam` from API `next_cursor`
 * (cursor-based; append pages until `next_cursor` is null).
 */
export const thumbnailKeys = {
  all: ['thumbnails'] as const,
  list: () => [...thumbnailKeys.all, 'list'] as const,
  job: (id: string) => [...thumbnailKeys.all, 'job', id] as const,
  history: (id: string) => [...thumbnailKeys.all, 'history', id] as const,
  usage: () => [...thumbnailKeys.all, 'usage'] as const,
}

/**
 * Terminal job statuses from the thumbnail pipeline (see backend `thumbnail_jobs.status`):
 * no further automatic transition happens without a human action (retry / select-candidate).
 */
export function isThumbnailJobTerminal(status: string): boolean {
  return status === 'completed' || status === 'failed' || status === 'awaiting_selection'
}

export function isThumbnailJobAwaitingSelection(status: string): boolean {
  return status === 'awaiting_selection'
}

const LIST_POLL_MS = 3000
const JOB_POLL_MS = 3000

export type ThumbnailListParams = {
  /** Restrict to one folder (server-side). */
  folderId?: string | null
  /** Collapse iteration chains to one row per lineage (latest version). */
  rootsOnly?: boolean
  /** With `folderId`, also include unfiled thumbnails — used for Testing. */
  includeUnfoldered?: boolean
  /** Skip the query until true (e.g. no folder open yet). */
  enabled?: boolean
}

export function useThumbnailListInfiniteQuery(
  limit = 20,
  params: ThumbnailListParams = {},
) {
  const {
    folderId = null,
    rootsOnly = false,
    includeUnfoldered = false,
    enabled = true,
  } = params
  return useInfiniteQuery({
    // Folder/mode are part of the key so each view caches independently; the
    // shared `list()` prefix keeps create/select invalidations matching them all.
    queryKey: [...thumbnailKeys.list(), { folderId, rootsOnly, includeUnfoldered, limit }],
    enabled,
    queryFn: ({ pageParam }: { pageParam: string | null | undefined }) =>
      ThumbnailCreatorService.listThumbnailsApiV1ThumbnailsThumbnailGet(
        pageParam ?? undefined,
        limit,
        folderId ?? undefined,
        rootsOnly,
        includeUnfoldered,
      ),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    // Poll while any job on loaded pages is still in progress (pending / running).
    refetchInterval: (query) => {
      const pages = query.state.data?.pages
      if (!pages?.length) return false
      const jobs = pages.flatMap((p: ThumbnailListResponse) => p.jobs)
      const anyActive = jobs.some((j) => !isThumbnailJobTerminal(j.status))
      return anyActive ? LIST_POLL_MS : false
    },
  })
}

export function useThumbnailJobQuery(jobId: string | undefined) {
  return useQuery({
    queryKey: thumbnailKeys.job(jobId ?? ''),
    queryFn: () => ThumbnailCreatorService.getThumbnailApiV1ThumbnailsThumbnailJobIdGet(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (!status) return false
      return isThumbnailJobTerminal(status) ? false : JOB_POLL_MS
    },
  })
}

export function useThumbnailUsageQuery() {
  return useQuery({
    queryKey: thumbnailKeys.usage(),
    queryFn: () => ThumbnailCreatorService.getThumbnailUsageApiV1ThumbnailsThumbnailUsageGet(),
  })
}

export function useThumbnailHistoryQuery(jobId: string | undefined) {
  return useQuery({
    queryKey: thumbnailKeys.history(jobId ?? ''),
    queryFn: () => ThumbnailCreatorService.historyThumbnailApiV1ThumbnailsThumbnailJobIdHistoryGet(jobId!),
    enabled: Boolean(jobId),
  })
}

export function useCreateThumbnailMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (input: Body_create_thumbnail_api_v1_thumbnails_thumbnail_post) =>
      ThumbnailCreatorService.createThumbnailApiV1ThumbnailsThumbnailPost(input),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: thumbnailKeys.list() })
      void qc.invalidateQueries({ queryKey: thumbnailKeys.usage() })
    },
  })
}

export function useSelectThumbnailCandidateMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      jobId,
      body,
    }: {
      jobId: string
      body: ThumbnailSelectCandidateRequest
    }) =>
      ThumbnailCreatorService.selectThumbnailCandidateApiV1ThumbnailsThumbnailJobIdSelectPost(
        jobId,
        body,
      ),
    onSuccess: (_, { jobId }) => {
      void qc.invalidateQueries({ queryKey: thumbnailKeys.list() })
      void qc.invalidateQueries({ queryKey: thumbnailKeys.job(jobId) })
    },
  })
}

export function useThumbnailFeedbackMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      jobId,
      body,
    }: {
      jobId: string
      body: ThumbnailFeedbackRequest
    }) => ThumbnailCreatorService.feedbackThumbnailApiV1ThumbnailsThumbnailJobIdFeedbackPost(jobId, body),
    onSuccess: (_, { jobId }) => {
      void qc.invalidateQueries({ queryKey: thumbnailKeys.list() })
      void qc.invalidateQueries({ queryKey: thumbnailKeys.job(jobId) })
      void qc.invalidateQueries({ queryKey: thumbnailKeys.history(jobId) })
      void qc.invalidateQueries({ queryKey: thumbnailKeys.usage() })
    },
  })
}
