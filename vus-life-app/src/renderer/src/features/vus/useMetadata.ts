/**
 * TanStack Query hooks for metadata fetching and downloading.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMetadata, downloadMetadata } from '../../api/endpoints'
import type { MetadataResponse } from '../../api/endpoints'

export const METADATA_QUERY_KEY = (geneSymbol: string) => ['vus', 'metadata', geneSymbol] as const

/**
 * Fetch metadata for a gene symbol.
 * Returns 404 error if metadata not found locally.
 */
export const useMetadata = (geneSymbol: string | null) => {
  return useQuery<MetadataResponse, Error & { status?: number }>({
    queryKey: METADATA_QUERY_KEY(geneSymbol || ''),
    queryFn: () => getMetadata(geneSymbol!),
    enabled: !!geneSymbol,
    retry: false, // Don't retry on 404
  })
}

/**
 * Mutation to download metadata from AWS.
 * On success, invalidates the metadata query to trigger refetch.
 */
export const useDownloadMetadata = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (geneSymbol: string) => downloadMetadata(geneSymbol),
    onSuccess: (_, geneSymbol) => {
      // Invalidate metadata query to trigger refetch
      queryClient.invalidateQueries({ queryKey: METADATA_QUERY_KEY(geneSymbol) })
    },
  })
}
