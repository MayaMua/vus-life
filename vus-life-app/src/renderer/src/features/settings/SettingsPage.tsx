/**
 * Settings page: left nav panel + main content. Holds activeTab state and renders the corresponding panel.
 */

import React, { useState } from 'react'
import { LeftPenal } from './components/LeftPenal'
import type { SettingsTab } from './components/LeftPenal'
import { GeneralSettings } from './components/GeneralSettings'
import { ModelProviderSettings } from './components/ModelProviderSettings'
import { VusApiSettings } from './components/VusApiSettings'
import { AgreementSection } from './components/AgreementSection'
import { AboutSection } from './components/AboutSection'

const panelAnimation = 'animate-in fade-in slide-in-from-bottom-2 duration-300'

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<SettingsTab>('general')

  return (
    <div className="flex h-full bg-white text-slate-900 overflow-hidden relative font-sans">
      <LeftPenal activeTab={activeTab} onSelect={setActiveTab} />

      <div className="flex-1 bg-[#F3F4F6] flex flex-col overflow-hidden">
        {activeTab === 'provider' ? (
          <div className={`${panelAnimation} flex-1 overflow-hidden flex flex-col`}>
            <ModelProviderSettings />
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto">
            <div className="max-w-5xl mx-auto p-10 flex flex-col gap-8">
              {activeTab === 'general' && (
                <div className={panelAnimation}>
                  <GeneralSettings />
                </div>
              )}
              {activeTab === 'vus' && (
                <div className={panelAnimation}>
                  <VusApiSettings />
                </div>
              )}
              {activeTab === 'agreement' && (
                <div className={panelAnimation}>
                  <AgreementSection />
                </div>
              )}
              {activeTab === 'about' && (
                <div className={`${panelAnimation} text-center py-10`}>
                  <AboutSection />
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
