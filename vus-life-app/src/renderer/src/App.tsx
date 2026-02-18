import React, { useState, useEffect } from 'react'
import { Sidebar } from './components/Siderbar'
import { GlobalAgreementDialog } from './components/GlobalAgreementDialog'
import { VusPage } from './features/vus/VusPage'
import { PdfParserPage } from './features/pdf/PdfParserPage'
import { SettingsPage } from './features/settings/SettingsPage'
import { useVusStore } from './features/vus/stores/useVusStore'
import type { AppTab } from './components/Siderbar'

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AppTab>('vus')
  const fetchVusConfig = useVusStore((state) => state.fetchConfig)

  useEffect(() => {
    fetchVusConfig()
  }, [fetchVusConfig])

  return (
    <div className="flex h-screen w-screen bg-base-100 text-base-content overflow-hidden">
      <GlobalAgreementDialog />
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />
      <main className="flex-1 overflow-hidden relative bg-base-100">
        {activeTab === 'vus' && <VusPage />}
        {activeTab === 'pdf' && <PdfParserPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>
    </div>
  )
}

export default App
