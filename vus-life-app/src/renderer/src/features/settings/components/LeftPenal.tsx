/**
 * Settings left panel: nav sidebar (SidePanel + Header, Nav, Version footer).
 */

import React from 'react'
import { Settings, Cloud, ShieldCheck, Info, Dna } from 'lucide-react'
import {
  SidePanel,
  SidePanelHeader,
  SidePanelNav,
  SidePanelFooter
} from '../../../components/SidePanel'

export type SettingsTab = 'general' | 'provider' | 'vus' | 'agreement' | 'about'

const menuItems: Array<{
  id: SettingsTab
  label: string
  icon: React.ComponentType<{ className?: string }>
}> = [
  { id: 'general', label: 'General Settings', icon: Settings },
  { id: 'provider', label: 'Model Provider', icon: Cloud },
  { id: 'vus', label: 'VUS Prediction', icon: Dna },
  { id: 'agreement', label: 'Data Usage Agreement', icon: ShieldCheck },
  { id: 'about', label: 'About & Feedback', icon: Info }
]

export interface LeftPenalProps {
  activeTab: SettingsTab
  onSelect: (id: SettingsTab) => void
}

export const LeftPenal: React.FC<LeftPenalProps> = ({ activeTab, onSelect }) => (
  <SidePanel variant="narrow" className="bg-[#f9fafb] border-slate-100">
    <SidePanelHeader title="Settings" className="mb-4" />
    <SidePanelNav
      items={menuItems}
      activeId={activeTab}
      onSelect={(id) => onSelect(id as SettingsTab)}
    />
    <SidePanelFooter className="border-slate-100">
      <div className="bg-white border border-slate-100 rounded-xl p-3 shadow-sm">
        <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Version</p>
        <p className="text-xs font-semibold text-slate-600">v1.2.4-stable</p>
      </div>
    </SidePanelFooter>
  </SidePanel>
)
