import React, { useState, useEffect } from 'react'
import { MainLayout } from './components/MainLayout'
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
    <>
      <GlobalAgreementDialog />
      <MainLayout sidebar={<Sidebar activeTab={activeTab} onTabChange={setActiveTab} />}>
        {activeTab === 'vus' && <VusPage />}
        {activeTab === 'pdf' && <PdfParserPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </MainLayout>
    </>
  )
}

export default App
