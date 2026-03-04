/**
 * TanStack Query hooks for settings management.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getSettings, updateSettings, verifyProvider } from '../../api/endpoints'
import type { ProviderVerifyRequest } from '../../api/endpoints'
import type { SettingsUpdateRequest } from '../../types/settings'

const SETTINGS_QUERY_KEY = ['settings'] as const

/**
 * Hook to fetch current application settings.
 */
export const useSettings = () => {
  return useQuery({
    queryKey: SETTINGS_QUERY_KEY,
    queryFn: getSettings,
    staleTime: 30000, // Consider data fresh for 30 seconds
    gcTime: 5 * 60 * 1000, // Keep in cache for 5 minutes
  })
}

/**
 * Hook to update application settings.
 */
export const useUpdateSettings = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (updates: SettingsUpdateRequest) => updateSettings(updates),
    onSuccess: () => {
      // Invalidate and refetch settings after successful update
      queryClient.invalidateQueries({ queryKey: SETTINGS_QUERY_KEY })
    },
  })
}

/**
 * Hook to verify provider connection
 */
export const useVerifyProvider = () => {
  return useMutation({
    mutationFn: (payload: ProviderVerifyRequest) => verifyProvider(payload),
  })
}
