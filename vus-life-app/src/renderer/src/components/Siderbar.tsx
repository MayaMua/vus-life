/**
 * L1 Sidebar: 64px width, Gray 100 bg. Icons default Gray 500; active = white container, shadow-sm, Primary Green icon, rounded-xl. Hover = Gray 200 bg.
 * Uses Lucide-react; transitions duration-200.
 */

import React from 'react'
import { Dna, FileText, Settings } from 'lucide-react'

export type AppTab = 'vus' | 'pdf' | 'settings'

interface SidebarProps {
  activeTab: AppTab
  onTabChange: (tab: AppTab) => void
}

const iconClass = 'h-5 w-5'

function NavItem({
  tab,
  activeTab,
  onTabChange,
  icon: Icon,
  label,
}: {
  tab: AppTab
  activeTab: AppTab
  onTabChange: (tab: AppTab) => void
  icon: React.ComponentType<{ className?: string }>
  label: string
}) {
  const isActive = activeTab === tab
  return (
    <li>
      <a
        href="#"
        role="button"
        className={`tooltip tooltip-right flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-200 ${
          isActive
            ? 'bg-white text-[#00B96B] shadow-sm'
            : 'bg-transparent text-[#6B7280] hover:bg-[#E5E7EB]'
        }`}
        data-tip={label}
        onClick={(e) => {
          e.preventDefault()
          onTabChange(tab)
        }}
      >
        <Icon className={iconClass} />
      </a>
    </li>
  )
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, onTabChange }) => {
  return (
    <nav className="w-16 h-full shrink-0 flex flex-col py-4 border-r border-[#E5E7EB] bg-[#F3F4F6]">
      <ul className="flex flex-col items-center gap-4 p-2 flex-1 min-h-0 w-full">
        <NavItem tab="vus" activeTab={activeTab} onTabChange={onTabChange} icon={Dna} label="VUS Prediction" />
        <NavItem tab="pdf" activeTab={activeTab} onTabChange={onTabChange} icon={FileText} label="PDF Parser" />
        <li className="mt-auto pt-2 border-t border-[#E5E7EB] w-full flex justify-center">
          <NavItem tab="settings" activeTab={activeTab} onTabChange={onTabChange} icon={Settings} label="Settings" />
        </li>
      </ul>
    </nav>
  )
}
