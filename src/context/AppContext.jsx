import React, { createContext, useContext, useEffect, useState, useCallback } from 'react'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  const [port, setPort] = useState(null)
  const [streamers, setStreamers] = useState([])
  const [settings, setSettings] = useState(null)
  const [toast, setToast] = useState(null)

  useEffect(() => {
    if (window.electron) {
      window.electron.getBackendPort().then((p) => setPort(p))
      window.electron.onBackendPort((p) => setPort(p))
    } else {
      setPort(8741)
    }
  }, [])

  const api = useCallback(
    async (path, opts = {}) => {
      if (!port) throw new Error('Backend not ready')
      const res = await fetch(`http://127.0.0.1:${port}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...opts,
      })
      if (!res.ok) {
        const msg = await res.text().catch(() => res.statusText)
        throw new Error(msg)
      }
      if (res.status === 204) return null
      return res.json()
    },
    [port]
  )

  const showToast = useCallback((message, type = 'info') => {
    setToast({ message, type, id: Date.now() })
    setTimeout(() => setToast(null), 3500)
  }, [])

  const fetchStreamers = useCallback(async () => {
    if (!port) return
    try {
      const data = await api('/streamers')
      setStreamers(data)
    } catch (e) {
      console.error('fetchStreamers:', e)
    }
  }, [api, port])

  const fetchSettings = useCallback(async () => {
    if (!port) return
    try {
      const data = await api('/settings')
      setSettings(data)
    } catch (e) {
      console.error('fetchSettings:', e)
    }
  }, [api, port])

  useEffect(() => {
    if (port) {
      fetchStreamers()
      fetchSettings()
    }
  }, [port])

  return (
    <AppContext.Provider value={{ port, api, streamers, fetchStreamers, settings, fetchSettings, toast, showToast }}>
      {children}
      {toast && <Toast toast={toast} />}
    </AppContext.Provider>
  )
}

function Toast({ toast }) {
  const colors = {
    info: 'bg-elevated border-border',
    success: 'bg-elevated border-green-600',
    error: 'bg-elevated border-red-600',
  }
  return (
    <div className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-lg border text-sm text-text-primary shadow-lg ${colors[toast.type] || colors.info}`}>
      {toast.message}
    </div>
  )
}

export function useApp() {
  return useContext(AppContext)
}
