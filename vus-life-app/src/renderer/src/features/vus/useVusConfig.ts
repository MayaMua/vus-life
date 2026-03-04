/**
 * TanStack Query hook for VUS dashboard config (gene names, embedding models, annotation methods).
 * Backend uses network-first with local persistence; from_cache indicates when data came from local.
 */

import { useQuery } from '@tanstack/react-query'
import { getVusConfig } from '../../api/endpoints'

export const VUS_CONFIG_QUERY_KEY = ['vus', 'config'] as const

export const useVusConfig = () => {
  return useQuery({
    queryKey: VUS_CONFIG_QUERY_KEY,
    queryFn: getVusConfig,
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  })
}
