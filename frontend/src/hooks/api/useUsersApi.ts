import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { UsersService, type UserCreate } from '@/client'
import { getApiErrorMessage } from '@/hooks/api/useYoutubeApi'

export { getApiErrorMessage }

export const usersKeys = {
  all: ['users'] as const,
  list: () => [...usersKeys.all, 'list'] as const,
}

export function useUserListQuery() {
  return useQuery({
    queryKey: usersKeys.list(),
    queryFn: () => UsersService.listAllUsersApiV1UsersGet(),
  })
}

export function useCreateUserMutation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: UserCreate) => UsersService.createNewUserApiV1UsersPost(body),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: usersKeys.list() })
    },
  })
}
