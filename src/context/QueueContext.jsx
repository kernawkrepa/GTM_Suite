import React, { createContext, useContext, useEffect, useRef, useState } from 'react'
import { useApp } from './AppContext'

const QueueContext = createContext(null)

export function QueueProvider({ children }) {
  const { port } = useApp()
  const [jobs, setJobs] = useState([])
  const esRef = useRef(null)

  useEffect(() => {
    if (!port) return
    const es = new EventSource(`http://127.0.0.1:${port}/queue/stream`)
    esRef.current = es

    es.onmessage = (e) => {
      try {
        const event = JSON.parse(e.data)
        if (event.type === 'job_update') {
          setJobs((prev) => {
            const idx = prev.findIndex((j) => j.id === event.job.id)
            if (idx === -1) return [...prev, event.job]
            const next = [...prev]
            next[idx] = event.job
            return next
          })
        }
      } catch {}
    }

    fetch(`http://127.0.0.1:${port}/queue`)
      .then((r) => r.json())
      .then(setJobs)
      .catch(() => {})

    return () => es.close()
  }, [port])

  const enqueue = async (clipIds, savePath, opts = {}) => {
    const res = await fetch(`http://127.0.0.1:${port}/queue/enqueue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ clip_ids: clipIds, save_path: savePath, ...opts }),
    })
    if (!res.ok) throw new Error(await res.text())
    const newJobs = await res.json()
    setJobs((prev) => {
      const ids = new Set(newJobs.map((j) => j.id))
      return [...prev.filter((j) => !ids.has(j.id)), ...newJobs]
    })
    return newJobs
  }

  const clearDone = async () => {
    await fetch(`http://127.0.0.1:${port}/queue/done`, { method: 'DELETE' })
    setJobs((prev) => prev.filter((j) => j.status !== 'done'))
  }

  const retryJob = async (jobId) => {
    const res = await fetch(`http://127.0.0.1:${port}/queue/${jobId}/retry`, { method: 'POST' })
    if (!res.ok) throw new Error(await res.text())
    const job = await res.json()
    setJobs((prev) => prev.map((j) => (j.id === jobId ? job : j)))
  }

  return (
    <QueueContext.Provider value={{ jobs, enqueue, clearDone, retryJob }}>
      {children}
    </QueueContext.Provider>
  )
}

export function useQueue() {
  return useContext(QueueContext)
}
