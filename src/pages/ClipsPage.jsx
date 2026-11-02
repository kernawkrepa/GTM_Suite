import React, { useCallback, useEffect, useState } from 'react'
import { useApp } from '../context/AppContext'
import { useQueue } from '../context/QueueContext'

export default function ClipsPage() {
  const { api, streamers, showToast } = useApp()
  const { enqueue } = useQueue()
  const [clips, setClips] = useState([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState(new Set())
  const [filters, setFilters] = useState({
    streamer_id: '',
    date_from: '',
    date_to: '',
    max_duration: '',
    favorites_only: false,
    sort: 'performance_score',
    sort_dir: 'desc',
  })
  const [modal, setModal] = useState(null)
  const [dlModal, setDlModal] = useState(false)
  const [dlPath, setDlPath] = useState('')

  const fetchClips = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      Object.entries(filters).forEach(([k, v]) => { if (v !== '' && v !== false) params.set(k, v) })
      const data = await api(`/clips?${params}`)
      setClips(data)
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [api, filters])

  useEffect(() => { fetchClips() }, [fetchClips])

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id); else next.add(id)
      return next
    })
  }

  const patchClip = async (id, update) => {
    await api(`/clips/${id}`, { method: 'PATCH', body: JSON.stringify(update) })
    setClips((prev) => prev.map((c) => c.id === id ? { ...c, ...update } : c))
  }

  const pickFolder = async () => {
    if (window.electron) {
      const res = await window.electron.showOpenDialog({ properties: ['openDirectory'] })
      if (!res.canceled && res.filePaths[0]) setDlPath(res.filePaths[0])
    }
  }

  const startDownload = async () => {
    if (!dlPath) return showToast('Select a download folder first', 'error')
    try {
      await enqueue(Array.from(selected), dlPath)
      setDlModal(false)
      setSelected(new Set())
      showToast(`Queued ${selected.size} clip(s)`, 'success')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const approvedStreamers = streamers.filter((s) => s.contract_status === 'approved')

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-border shrink-0 flex-wrap gap-y-2">
        <select
          value={filters.streamer_id}
          onChange={(e) => setFilters((f) => ({ ...f, streamer_id: e.target.value }))}
          className="bg-elevated border border-border text-text-primary text-sm rounded px-2 py-1"
        >
          <option value="">All Streamers</option>
          {approvedStreamers.map((s) => (
            <option key={s.id} value={s.id}>{s.display_name}</option>
          ))}
        </select>
        <select
          value={filters.sort}
          onChange={(e) => setFilters((f) => ({ ...f, sort: e.target.value }))}
          className="bg-elevated border border-border text-text-primary text-sm rounded px-2 py-1"
        >
          <option value="performance_score">Performance Score</option>
          <option value="view_count">View Count</option>
          <option value="created_at">Date</option>
          <option value="duration">Duration</option>
        </select>
        <label className="flex items-center gap-1.5 text-sm text-text-secondary cursor-pointer">
          <input
            type="checkbox"
            checked={filters.favorites_only}
            onChange={(e) => setFilters((f) => ({ ...f, favorites_only: e.target.checked }))}
          />
          Favorites
        </label>
        {selected.size > 0 && (
          <button
            onClick={() => setDlModal(true)}
            className="ml-auto bg-purple hover:bg-purple-hover text-white text-sm px-3 py-1.5 rounded"
          >
            Download {selected.size}
          </button>
        )}
        <button onClick={fetchClips} className="bg-elevated border border-border text-text-secondary text-sm px-3 py-1.5 rounded hover:text-text-primary">
          ↺
        </button>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto p-4">
        {loading ? (
          <p className="text-text-muted text-sm p-2">Loading…</p>
        ) : clips.length === 0 ? (
          <p className="text-text-muted text-sm p-2">No clips found. Add approved streamers and scan their clips.</p>
        ) : (
          <div className="grid grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-3">
            {clips.map((clip) => (
              <ClipCard
                key={clip.id}
                clip={clip}
                selected={selected.has(clip.id)}
                onSelect={() => toggleSelect(clip.id)}
                onOpen={() => setModal(clip)}
                onPatch={(u) => patchClip(clip.id, u)}
              />
            ))}
          </div>
        )}
      </div>

      {/* Clip modal */}
      {modal && (
        <ClipModal clip={modal} onClose={() => setModal(null)} onPatch={(u) => patchClip(modal.id, u)} />
      )}

      {/* Download modal */}
      {dlModal && (
        <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center">
          <div className="bg-elevated border border-border rounded-xl p-6 w-96 flex flex-col gap-4">
            <h2 className="text-text-primary font-bold">Download {selected.size} Clip(s)</h2>
            <div className="flex gap-2">
              <input
                type="text"
                value={dlPath}
                onChange={(e) => setDlPath(e.target.value)}
                placeholder="Select folder…"
                className="flex-1 bg-surface border border-border text-text-primary text-sm rounded px-3 py-2"
              />
              <button onClick={pickFolder} className="bg-surface border border-border text-text-secondary text-sm px-3 py-2 rounded hover:text-text-primary">
                Browse
              </button>
            </div>
            <div className="flex gap-2 justify-end">
              <button onClick={() => setDlModal(false)} className="text-sm text-text-secondary px-3 py-1.5 rounded hover:text-text-primary">Cancel</button>
              <button onClick={startDownload} className="bg-purple hover:bg-purple-hover text-white text-sm px-4 py-1.5 rounded">Download</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ClipCard({ clip, selected, onSelect, onOpen, onPatch }) {
  const score = clip.performance_score?.toFixed(1) ?? '—'
  const mins = Math.floor(clip.duration / 60)
  const secs = Math.round(clip.duration % 60)

  return (
    <div
      className={`relative bg-elevated border rounded-lg overflow-hidden cursor-pointer transition-all ${selected ? 'border-purple ring-1 ring-purple' : 'border-border hover:border-purple/50'}`}
      style={{ contentVisibility: 'auto' }}
    >
      <div className="relative" onClick={onOpen}>
        {clip.thumbnail_url && (
          <img src={clip.thumbnail_url} alt="" className="w-full aspect-video object-cover" loading="lazy" />
        )}
        <span className="absolute bottom-1 right-1 text-xs bg-black/70 text-white px-1 rounded">
          {mins}:{String(secs).padStart(2, '0')}
        </span>
      </div>
      <div className="p-2.5">
        <p className="text-text-primary text-xs font-medium line-clamp-2 mb-1">{clip.title}</p>
        <div className="flex items-center gap-2 text-xs text-text-muted">
          <span>{clip.view_count?.toLocaleString()} views</span>
          <span className="ml-auto font-mono text-purple-hover">{score}</span>
        </div>
        <div className="flex items-center gap-2 mt-1.5">
          <input type="checkbox" checked={selected} onChange={onSelect} className="accent-purple" />
          <button
            onClick={() => onPatch({ is_favorite: !clip.is_favorite })}
            className={`text-sm ${clip.is_favorite ? 'text-yellow-400' : 'text-text-muted hover:text-yellow-400'}`}
          >
            ★
          </button>
          {clip.downloaded && <span className="text-xs text-green-500">✓</span>}
        </div>
      </div>
    </div>
  )
}

function ClipModal({ clip, onClose, onPatch }) {
  const embedUrl = `https://clips.twitch.tv/embed?clip=${clip.twitch_clip_id}&parent=localhost&autoplay=false`

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-6">
      <div className="bg-elevated border border-border rounded-xl w-full max-w-3xl flex flex-col gap-4 overflow-hidden">
        <div className="flex items-center justify-between px-5 pt-4">
          <p className="text-text-primary font-bold text-sm line-clamp-1">{clip.title}</p>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary text-xl">✕</button>
        </div>
        <div className="aspect-video bg-black mx-5">
          <iframe src={embedUrl} allowFullScreen className="w-full h-full" />
        </div>
        <div className="flex items-center gap-3 px-5 pb-4">
          <button
            onClick={() => onPatch({ is_favorite: !clip.is_favorite })}
            className={`text-sm px-3 py-1.5 rounded border ${clip.is_favorite ? 'border-yellow-500 text-yellow-400' : 'border-border text-text-muted hover:text-yellow-400'}`}
          >
            {clip.is_favorite ? '★ Favorited' : '☆ Favorite'}
          </button>
          <button
            onClick={() => onPatch({ is_outro: !clip.is_outro })}
            className={`text-sm px-3 py-1.5 rounded border ${clip.is_outro ? 'border-purple text-purple' : 'border-border text-text-muted hover:text-purple'}`}
          >
            {clip.is_outro ? 'Outro ✓' : 'Mark Outro'}
          </button>
          <div className="ml-auto text-xs text-text-muted">
            {clip.view_count?.toLocaleString()} views · {clip.performance_score?.toFixed(2)} score
          </div>
        </div>
      </div>
    </div>
  )
}
