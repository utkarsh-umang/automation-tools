import { useQuery } from '@tanstack/react-query'
import { HealthService } from '@/client'

export function useHealthQuery() {
  return useQuery({
    queryKey: ['health'] as const,
    queryFn: () => HealthService.healthHealthGet(),
  })
}
