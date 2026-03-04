/**
 * Hook to check VUS API connection (ping health endpoint).
 * Does not load config; use useVusConfig for that.
 */

import { useState, useCallback, useEffect } from 'react'
import { getSettings } from '../../api/endpoints'

export function useVusApiConnected(): {
  isApiConnected: boolean | undefined
  refetch: () => Promise<void>
} {
  const [isApiConnected, setIsApiConnected] = useState<boolean | undefined>(undefined)

  const refetch = useCallback(async () => {
    setIsApiConnected(undefined)
    try {
      const settings = await getSettings()
      const apiUrl = settings?.vus_api_settings?.api_url?.trim()?.replace(/\/$/, '') ?? ''
      if (!apiUrl) {
        setIsApiConnected(false)
        return
      }
      const ctrl = new AbortController()
      const t = setTimeout(() => ctrl.abort(), 5000)
      const r = await fetch(`${apiUrl}/api/health`, {
        signal: ctrl.signal,
        headers: { Accept: 'application/json', 'ngrok-skip-browser-warning': 'true' },
      })
      clearTimeout(t)
      setIsApiConnected(r.ok)
    } catch {
      setIsApiConnected(false)
    }
  }, [])

  useEffect(() => {
    refetch()
  }, [refetch])

  return { isApiConnected, refetch }
}
