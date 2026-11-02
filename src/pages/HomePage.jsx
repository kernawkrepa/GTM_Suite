import React, { useCallback, useEffect, useState } from 'react'
import { useApp } from '../context/AppContext'

export default function HomePage() {
  const { api, streamers: managedStreamers, fetchStreamers, showToast } = useApp()
  const [streams, setStreams] = useState([])
  const [loading, setLoading] = useState(false)
  const [language, setLanguage] = useState('en')
  const managedIds = new Set(managedStreamers.map((s) => s.twitch_id))

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const data = await api(`/discovery/top-streamers?language=${language}&limit=30`)
      setStreams(data)
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }, [api, language])

  useEffect(() => { load() }, [load])

  const addStreamer = async (s) => {
    try {
      await api('/streamers/from-discovery', {
        method: 'POST',
        body: JSON.stringify({ user_id: s.user_id, user_login: s.user_login, display_name: s.display_name, avatar_url: s.avatar_url }),
      })
      await fetchStreamers()
      showToast(`${s.display_name} added`, 'success')
      setStreams((prev) => prev.map((x) => x.user_id === s.user_id ? { ...x, already_added: true } : x))
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <h1 className="text-lg font-bold text-text-primary">Discovery</h1>
        <select value={language} onChange={(e) => setLanguage(e.target.value)} className="ml-auto bg-elevated border border-border text-text-primary text-sm rounded px-2 py-1">
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="fr">French</option>
          <option value="de">German</option>
          <option value="pt">Portuguese</option>
          <option value="ko">Korean</option>
          <option value="ja">Japanese</option>
          <option value="zh">Chinese</option>
          <option value="">All</option>
        </select>
        <button onClick={load} disabled={loading} className="bg-purple hover:bg-purple-hover text-white text-sm px-3 py-1.5 rounded disabled:opacity-50">
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        {loading && streams.length === 0 ? (
          <p className="text-text-muted text-sm">Loading live streamers…</p>
        ) : (
          <div className="grid grid-cols-2 xl:grid-cols-3 gap-4">
            {streams.map((s) => (
              <div key={s.user_id} className="bg-elevated border border-border rounded-lg p-4 flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  {s.avatar_url && <img src={s.avatar_url} alt="" className="w-10 h-10 rounded-full object-cover shrink-0" />}
                  <div className="min-w-0">
                    <p className="text-text-primary font-semibold text-sm truncate">{s.display_name}</p>
                    <p className="text-text-muted text-xs truncate">{s.game_name}</p>
                  </div>
                  <span className="ml-auto text-xs bg-red-700 text-white px-1.5 py-0.5 rounded font-mono shrink-0">{(s.viewer_count || 0).toLocaleString()}</span>
                </div>
                <div className="flex gap-2 mt-auto">
                  <button onClick={() => window.electron?.openExternal(`https://twitch.tv/${s.user_login}`)} className="flex-1 text-xs text-text-secondary border border-border rounded px-2 py-1 hover:bg-surface">View</button>
                  <button onClick={() => addStreamer(s)} disabled={s.already_added || managedIds.has(s.user_id)} className="flex-1 text-xs bg-purple hover:bg-purple-hover text-white rounded px-2 py-1 disabled:opacity-40 disabled:cursor-not-allowed">
                    {s.already_added || managedIds.has(s.user_id) ? 'Added' : '+ Add'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
