import React, { useCallback, useEffect, useState } from 'react'
import { useApp } from '../context/AppContext'

const LEVEL_COLOR = { ERROR: 'text-red-400', WARNING: 'text-yellow-400', INFO: 'text-blue-400', DEBUG: 'text-text-muted' }

export default function DebugLogsPage() {
  const { api, showToast } = useApp()
  const [logs, setLogs] = useState([])
  const [filter, setFilter] = useState('')

  const fetchLogs = useCallback(async () => {
    try {
      const data = await api('/logs')
      setLogs(data)
    } catch (e) {
      showToast(e.message, 'error')
    }
  }, [api])

  useEffect(() => { fetchLogs() }, [fetchLogs])

  const clearLogs = async () => {
    try {
      await api('/logs', { method: 'DELETE' })
      setLogs([])
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const filtered = filter
    ? logs.filter((l) => l.message?.toLowerCase().includes(filter.toLowerCase()) || l.level?.includes(filter.toUpperCase()))
    : logs

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <h1 className="text-lg font-bold text-text-primary">Debug Logs</h1>
        <span className="text-text-muted text-sm">{logs.length} entries</span>
        <input
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          placeholder="Filter…"
          className="ml-auto bg-elevated border border-border text-text-primary text-sm rounded px-3 py-1.5 w-48"
        />
        <button onClick={fetchLogs} className="text-sm text-text-secondary border border-border rounded px-3 py-1.5 hover:text-text-primary">Refresh</button>
        <button onClick={clearLogs} className="text-sm text-red-400 border border-red-700 rounded px-3 py-1.5 hover:text-red-300">Clear</button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs flex flex-col gap-0.5">
        {filtered.length === 0 && <p className="text-text-muted">No log entries.</p>}
        {filtered.slice().reverse().map((log, i) => (
          <div key={i} className="flex gap-3 hover:bg-elevated/50 rounded px-2 py-0.5">
            <span className={`shrink-0 w-16 ${LEVEL_COLOR[log.level] || 'text-text-muted'}`}>{log.level}</span>
            <span className="text-text-muted shrink-0">{log.time ? new Date(log.time * 1000).toLocaleTimeString() : ''}</span>
            <span className="text-text-secondary break-all">{log.message}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
