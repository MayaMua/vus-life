import React, { useState } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { MainLayout } from './components/MainLayout'
import { Sidebar } from './components/Siderbar'
import { VusPage } from './features/vus/VusPage'
import { PdfParserPage } from './features/pdf/PdfParserPage'
import { SettingsPage } from './features/settings/SettingsPage'
import type { AppTab } from './components/Siderbar'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AppTab>('vus')

  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="bottom-right" />
      <MainLayout sidebar={<Sidebar activeTab={activeTab} onTabChange={setActiveTab} />}>
        {activeTab === 'vus' && <VusPage />}
        {activeTab === 'pdf' && <PdfParserPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </MainLayout>
    </QueryClientProvider>
  )
}

export default App
