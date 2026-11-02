import React, { useEffect, useState } from 'react'
import { AppProvider } from './context/AppContext'
import { QueueProvider } from './context/QueueContext'
import Sidebar from './components/layout/Sidebar'
import TitleBar from './components/layout/TitleBar'
import HomePage from './pages/HomePage'
import ClipsPage from './pages/ClipsPage'
import StreamersPage from './pages/StreamersPage'
import QueuePage from './pages/QueuePage'
import SettingsPage from './pages/SettingsPage'
import DebugLogsPage from './pages/DebugLogsPage'

export default function App() {
  const [page, setPage] = useState('home')

  return (
    <AppProvider>
      <QueueProvider>
        <div className="flex flex-col h-screen bg-bg overflow-hidden">
          <TitleBar />
          <div className="flex flex-1 overflow-hidden">
            <Sidebar activePage={page} onNavigate={setPage} />
            <main className="flex-1 overflow-hidden">
              {page === 'home' && <HomePage />}
              {page === 'clips' && <ClipsPage />}
              {page === 'streamers' && <StreamersPage />}
              {page === 'queue' && <QueuePage />}
              {page === 'settings' && <SettingsPage />}
              {page === 'logs' && <DebugLogsPage />}
            </main>
          </div>
        </div>
      </QueueProvider>
    </AppProvider>
  )
}
