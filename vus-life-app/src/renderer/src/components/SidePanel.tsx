/**
 * Reusable SidePanel layout component (Feature Sidebar in 3-pane model).
 * Use for Settings nav sidebar, VUS config panel, or any left-side content.
 * Compound components: SidePanel.Header, .Nav, .Body, .Footer.
 */

import React from 'react'

export type SidePanelVariant = 'narrow' | 'wide'

const variantClasses: Record<SidePanelVariant, string> = {
  narrow: 'w-64',
  wide: 'w-full max-w-md',
}

export interface SidePanelProps {
  children: React.ReactNode
  className?: string
  variant?: SidePanelVariant
  /** Optional inline width (e.g. for resizable panels); overrides variant width */
  style?: React.CSSProperties
}

const rootBaseClasses =
  'flex flex-col border-r border-base-300 bg-base-200/40 overflow-hidden shrink-0'

export const SidePanel: React.FC<SidePanelProps> = ({
  children,
  className = '',
  variant = 'wide',
  style,
}) => (
  <div
    className={`${rootBaseClasses} ${variantClasses[variant]} ${className}`.trim()}
    style={style}
  >
    {children}
  </div>
)

// --- Header: title / branding block ---
export interface SidePanelHeaderProps {
  title: string
  className?: string
}

export const SidePanelHeader: React.FC<SidePanelHeaderProps> = ({
  title,
  className = '',
}) => (
  <div
    className={`p-6 border-b border-slate-100 shrink-0 ${className}`.trim()}
  >
    <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
      {title}
    </h2>
  </div>
)

// --- Nav: list of items with icon, active state ---
export interface SidePanelNavItem {
  id: string
  label: string
  icon: React.ComponentType<{ className?: string }>
}

export interface SidePanelNavProps {
  items: SidePanelNavItem[]
  activeId: string
  onSelect: (id: string) => void
  className?: string
}

export const SidePanelNav: React.FC<SidePanelNavProps> = ({
  items,
  activeId,
  onSelect,
  className = '',
}) => (
  <nav className={`flex-1 px-3 space-y-1 overflow-y-auto min-h-0 ${className}`.trim()}>
    {items.map((item) => {
      const isActive = activeId === item.id
      return (
        <button
          key={item.id}
          type="button"
          onClick={() => onSelect(item.id)}
          className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
            isActive
              ? 'bg-slate-200/60 text-slate-900 shadow-sm'
              : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
          }`}
        >
          <item.icon
            className={`w-4 h-4 ${isActive ? 'text-[#00B96B]' : 'text-slate-400'}`}
          />
          {item.label}
        </button>
      )
    })}
  </nav>
)

// --- Body: scrollable content area ---
export interface SidePanelBodyProps {
  children: React.ReactNode
  className?: string
}

export const SidePanelBody: React.FC<SidePanelBodyProps> = ({
  children,
  className = '',
}) => (
  <div
    className={`flex-1 overflow-y-auto min-h-0 ${className}`.trim()}
  >
    {children}
  </div>
)

// --- Footer: pinned bottom block (e.g. version, primary action) ---
export interface SidePanelFooterProps {
  children: React.ReactNode
  className?: string
}

export const SidePanelFooter: React.FC<SidePanelFooterProps> = ({
  children,
  className = '',
}) => (
  <div className={`p-4 mt-auto shrink-0 border-t border-slate-100 ${className}`.trim()}>
    {children}
  </div>
)
