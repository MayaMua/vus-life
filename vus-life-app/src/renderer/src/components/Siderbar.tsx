/**
 * App sidebar: DaisyUI menu with icon-only nav (VUS, PDF at top; Settings at bottom).
 */

import React from 'react'
import { Dna, FileText, Settings } from 'lucide-react';

export type AppTab = 'vus' | 'pdf' | 'settings'

interface SidebarProps {
  activeTab: AppTab
  onTabChange: (tab: AppTab) => void
}

const iconClass = 'h-5 w-5'

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <nav className="w-14 shrink-0 z-50 flex flex-col py-4 border-r border-base-300 bg-base-200">
      <ul className="menu menu-vertical bg-base-200 rounded-none gap-4 p-2 flex-1 flex flex-col min-h-0 w-full">
        <li>
          <a
            href="#"
            role="button"
            className={`tooltip tooltip-right ${activeTab === 'vus' ? 'active' : ''}`}
            data-tip="VUS Prediction"
            onClick={(e) => {
              e.preventDefault()
              onTabChange('vus')
            }}
          >
            <Dna className={iconClass} />
          </a>
        </li>
        <li>
          <a
            href="#"
            role="button"
            className={`tooltip tooltip-right ${activeTab === 'pdf' ? 'active' : ''}`}
            data-tip="PDF Parser"
            onClick={(e) => {
              e.preventDefault()
              onTabChange('pdf')
            }}
          >
            <FileText className={iconClass} />
          </a>
        </li>
        <li className="mt-auto pt-2 border-t border-base-300">
          <a
            href="#"
            role="button"
            className={`tooltip tooltip-right ${activeTab === 'settings' ? 'active' : ''}`}
            data-tip="Settings"
            onClick={(e) => {
              e.preventDefault()
              onTabChange('settings')
            }}
          >
            <Settings className={iconClass} />
          </a>
        </li>
      </ul>
    </nav>
  )
}
