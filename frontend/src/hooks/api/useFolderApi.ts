import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FoldersService, type FolderCreate, type FolderUpdate } from '@/client'

export const folderKeys = {
  all: ['folders'] as const,
  list: () => [...folderKeys.all, 'list'] as const,
  summary: () => [...folderKeys.all, 'summary'] as const,
}

export function useFolderListQuery() {
  return useQuery({
    queryKey: folderKeys.list(),
    queryFn: () => FoldersService.listFoldersApiV1FoldersGet(),
  })
}

/** Per-folder thumbnail count + cover image, for the album grid. */
export function useFolderSummaryQuery() {
  return useQuery({
    queryKey: folderKeys.summary(),
    queryFn: () => FoldersService.folderSummariesApiV1FoldersSummaryGet(),
  })
}

export function useCreateFolderMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: FolderCreate) => FoldersService.createFolderApiV1FoldersPost(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: folderKeys.list() })
    },
  })
}

export function useUpdateFolderMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ folderId, body }: { folderId: string; body: FolderUpdate }) =>
      FoldersService.updateFolderApiV1FoldersFolderIdPatch(folderId, body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: folderKeys.list() })
    },
  })
}
