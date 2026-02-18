/**
 * Settings layout: sidebar navigation and main content shell.
 * Holds activeTab state and renders the corresponding settings panel.
 */

import React, { useState } from 'react'
import {
  Settings,
  Cloud,
  ShieldCheck,
  Info,
  Database,
  Dna,
} from 'lucide-react'
import { GeneralSettings } from './components/GeneralSettings'
import { ModelProviderSettings } from './components/ModelProviderSettings'
import { VusApiSettings } from './components/VusApiSettings'
import { AgreementSection } from './components/AgreementSection'
import { AboutSection } from './components/AboutSection'

export type SettingsTab = 'general' | 'provider' | 'vus' | 'agreement' | 'about'

const menuItems: Array<{ id: SettingsTab; label: string; icon: React.ComponentType<{ className?: string }> }> = [
  { id: 'general', label: 'General Settings', icon: Settings },
  { id: 'provider', label: 'Model Provider', icon: Cloud },
  { id: 'vus', label: 'VUS Prediction', icon: Dna },
  { id: 'agreement', label: 'Data Usage Agreement', icon: ShieldCheck },
  { id: 'about', label: 'About & Feedback', icon: Info },
]

export const SettingsLayout: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')

  return (
    <div className="flex h-full bg-white text-slate-900 overflow-hidden relative font-sans">
      {/* SETTINGS SIDEBAR */}
      <div className="w-64 border-r border-slate-100 flex flex-col bg-[#f9fafb]">
        <div className="p-6 border-b border-slate-100 mb-4">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Settings</h2>
        </div>

        <nav className="flex-1 px-3 space-y-1">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-semibold transition-all ${
                activeTab === item.id
                  ? 'bg-slate-200/60 text-slate-900 shadow-sm'
                  : 'text-slate-500 hover:bg-slate-100 hover:text-slate-700'
              }`}
            >
              <item.icon className={`w-4 h-4 ${activeTab === item.id ? 'text-blue-600' : 'text-slate-400'}`} />
              {item.label}
            </button>
          ))}
        </nav>

        <div className="p-4 mt-auto">
          <div className="bg-white border border-slate-100 rounded-xl p-3 shadow-sm">
            <p className="text-[10px] font-bold text-slate-400 uppercase mb-1">Version</p>
            <p className="text-xs font-semibold text-slate-600">v1.2.4-stable</p>
          </div>
        </div>
      </div>

      {/* SETTINGS CONTENT */}
      <div className="flex-1 overflow-y-auto bg-white">
        <div className="max-w-4xl p-10">
          {activeTab === 'general' && (
            <div className="space-y-10 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <GeneralSettings />
            </div>
          )}
          {activeTab === 'provider' && (
            <div className="h-full flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300">
              <ModelProviderSettings />
            </div>
          )}
          {activeTab === 'vus' && (
            <div className="space-y-10 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <VusApiSettings />
            </div>
          )}
          {activeTab === 'agreement' && (
            <div className="space-y-8 animate-in fade-in slide-in-from-bottom-2 duration-300">
              <AgreementSection />
            </div>
          )}
          {activeTab === 'about' && (
            <div className="space-y-12 animate-in fade-in slide-in-from-bottom-2 duration-300 text-center py-10">
              <AboutSection />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
