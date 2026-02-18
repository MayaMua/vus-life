/**
 * 3-column layout: L1 Sidebar, optional L2 List, L3 Content.
 * Backgrounds: L1 = #F3F4F6, L3 = #FFFFFF. Dividers: 1px #E5E7EB.
 */

import React from 'react'

interface MainLayoutProps {
  /** L1: Navigation sidebar (e.g. icon sidebar) */
  sidebar: React.ReactNode
  /** L2: Optional list pane (e.g. item list) */
  list?: React.ReactNode
  /** L3: Main content area */
  children: React.ReactNode
}

const dividerClass = 'border-[#E5E7EB]'

export const MainLayout: React.FC<MainLayoutProps> = ({ sidebar, list, children }) => {
  return (
    <div className="flex h-screen w-screen overflow-hidden font-sans text-base-content" style={{ fontFamily: 'Inter, system-ui, sans-serif' }}>
      {/* L1 Sidebar */}
      <aside className="shrink-0" aria-label="Navigation">
        {sidebar}
      </aside>
      {/* L2 List (optional) */}
      {list != null && (
        <section className={`shrink-0 border-r ${dividerClass} bg-white overflow-hidden`} aria-label="List">
          {list}
        </section>
      )}
      {/* L3 Content */}
      <main className="flex-1 min-w-0 overflow-hidden bg-white">
        {children}
      </main>
    </div>
  )
}
