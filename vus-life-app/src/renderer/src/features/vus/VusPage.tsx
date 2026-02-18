/**
 * VUS Prediction page: split-view layout with left config/input panel and right results dashboard.
 * Agreement dialog is shown globally from App on first launch.
 */

import React, { useEffect } from 'react'
import { useVusStore } from './stores/useVusStore'
import { LeftPanel } from './components/LeftPanel'
import { RightPanel } from './components/RightPanel'

export const VusPage: React.FC = () => {
  const fetchVusConfig = useVusStore((s) => s.fetchConfig)

  useEffect(() => {
    fetchVusConfig()
  }, [fetchVusConfig])

  return (
    <div className="flex h-full w-full overflow-hidden bg-base-100">
      {/* Left: config and input panel */}
      <aside className="shrink-0 overflow-hidden bg-base-200/50 border-r border-base-300">
        <LeftPanel />
      </aside>

      {/* Right: results dashboard */}
      <section className="flex-1 min-w-0 flex flex-col overflow-hidden bg-base-100">
        <RightPanel />
      </section>
    </div>
  )
}
