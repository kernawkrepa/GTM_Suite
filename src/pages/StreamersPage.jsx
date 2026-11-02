import React, { useState } from 'react'
import { useApp } from '../context/AppContext'

const STATUS_COLORS = {
  approved: 'text-green-400 border-green-600',
  pending: 'text-yellow-400 border-yellow-600',
  rejected: 'text-red-400 border-red-600',
  contacted: 'text-blue-400 border-blue-600',
  signed: 'text-purple border-purple',
  active: 'text-green-300 border-green-500',
  inactive: 'text-text-muted border-border',
  waitlist: 'text-orange-400 border-orange-500',
}

const ALL_STATUSES = ['pending', 'contacted', 'approved', 'signed', 'active', 'rejected', 'inactive', 'waitlist']

export default function StreamersPage() {
  const { api, streamers, fetchStreamers, showToast } = useApp()
  const [editing, setEditing] = useState(null)
  const [addForm, setAddForm] = useState(null)

  const updateStatus = async (id, status) => {
    try {
      await api(`/streamers/${id}`, { method: 'PATCH', body: JSON.stringify({ contract_status: status }) })
      await fetchStreamers()
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const deleteStreamer = async (id) => {
    if (!confirm('Delete this streamer and all their clips?')) return
    try {
      await api(`/streamers/${id}`, { method: 'DELETE' })
      await fetchStreamers()
      showToast('Deleted', 'info')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const scanStreamer = async (id) => {
    try {
      await api('/clips/scan', { method: 'POST', body: JSON.stringify([id]) })
      showToast('Scan started', 'info')
    } catch (e) {
      showToast(e.message, 'error')
    }
  }

  const exportCSV = () => {
    const rows = [['twitch_login', 'display_name', 'contract_status', 'notes', 'partnership_date']]
    streamers.forEach((s) => rows.push([s.twitch_login, s.display_name, s.contract_status, s.notes || '', s.partnership_date || '']))
    const csv = rows.map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = 'streamers.csv'; a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <h1 className="text-lg font-bold text-text-primary">Streamers</h1>
        <span className="text-text-muted text-sm">{streamers.length} total</span>
        <div className="ml-auto flex gap-2">
          <button onClick={exportCSV} className="text-sm text-text-secondary border border-border rounded px-3 py-1.5 hover:text-text-primary">Export CSV</button>
          <button onClick={() => setAddForm({})} className="text-sm bg-purple hover:bg-purple-hover text-white rounded px-3 py-1.5">+ Add</button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="bg-surface border-b border-border sticky top-0">
            <tr>
              <th className="text-left px-4 py-2.5 text-text-muted font-medium">Streamer</th>
              <th className="text-left px-4 py-2.5 text-text-muted font-medium">Status</th>
              <th className="text-left px-4 py-2.5 text-text-muted font-medium">Notes</th>
              <th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {streamers.map((s) => (
              <tr key={s.id} className="border-b border-border hover:bg-elevated/50 transition-colors">
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    {s.avatar_url && <img src={s.avatar_url} alt="" className="w-8 h-8 rounded-full object-cover" />}
                    <div>
                      <p className="text-text-primary font-medium">{s.display_name}</p>
                      <p className="text-text-muted text-xs">@{s.twitch_login}</p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <select
                    value={s.contract_status}
                    onChange={(e) => updateStatus(s.id, e.target.value)}
                    className={`bg-transparent border rounded px-2 py-0.5 text-xs ${STATUS_COLORS[s.contract_status] || 'text-text-muted border-border'}`}
                  >
                    {ALL_STATUSES.map((st) => <option key={st} value={st}>{st}</option>)}
                  </select>
                </td>
                <td className="px-4 py-3 text-text-muted text-xs max-w-xs truncate">{s.notes}</td>
                <td className="px-4 py-3">
                  <div className="flex gap-1 justify-end">
                    <button onClick={() => scanStreamer(s.id)} className="text-xs text-text-muted hover:text-text-primary px-2 py-1 rounded hover:bg-elevated">Scan</button>
                    <button onClick={() => setEditing(s)} className="text-xs text-text-muted hover:text-text-primary px-2 py-1 rounded hover:bg-elevated">Edit</button>
                    <button onClick={() => deleteStreamer(s.id)} className="text-xs text-text-muted hover:text-red-400 px-2 py-1 rounded hover:bg-elevated">Del</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {(editing || addForm) && (
        <StreamerEditModal
          streamer={editing}
          onClose={() => { setEditing(null); setAddForm(null) }}
          onSave={async (data) => {
            try {
              if (editing) {
                await api(`/streamers/${editing.id}`, { method: 'PATCH', body: JSON.stringify(data) })
              } else {
                await api('/streamers', { method: 'POST', body: JSON.stringify(data) })
              }
              await fetchStreamers()
              setEditing(null); setAddForm(null)
              showToast('Saved', 'success')
            } catch (e) { showToast(e.message, 'error') }
          }}
        />
      )}
    </div>
  )
}

function StreamerEditModal({ streamer, onClose, onSave }) {
  const [form, setForm] = useState({
    twitch_id: streamer?.twitch_id || '',
    twitch_login: streamer?.twitch_login || '',
    display_name: streamer?.display_name || '',
    contract_status: streamer?.contract_status || 'pending',
    notes: streamer?.notes || '',
    partnership_date: streamer?.partnership_date || '',
  })
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center">
      <div className="bg-elevated border border-border rounded-xl p-6 w-96 flex flex-col gap-4">
        <h2 className="text-text-primary font-bold">{streamer ? 'Edit Streamer' : 'Add Streamer'}</h2>
        {!streamer && (
          <>
            <input value={form.twitch_id} onChange={set('twitch_id')} placeholder="Twitch ID" className="bg-surface border border-border text-text-primary text-sm rounded px-3 py-2" />
            <input value={form.twitch_login} onChange={set('twitch_login')} placeholder="Twitch login" className="bg-surface border border-border text-text-primary text-sm rounded px-3 py-2" />
            <input value={form.display_name} onChange={set('display_name')} placeholder="Display name" className="bg-surface border border-border text-text-primary text-sm rounded px-3 py-2" />
          </>
        )}
        <textarea value={form.notes} onChange={set('notes')} placeholder="Notes…" rows={3} className="bg-surface border border-border text-text-primary text-sm rounded px-3 py-2 resize-none" />
        <input value={form.partnership_date} onChange={set('partnership_date')} placeholder="Partnership date (YYYY-MM-DD)" className="bg-surface border border-border text-text-primary text-sm rounded px-3 py-2" />
        <div className="flex gap-2 justify-end">
          <button onClick={onClose} className="text-sm text-text-secondary px-3 py-1.5 rounded hover:text-text-primary">Cancel</button>
          <button onClick={() => onSave(form)} className="bg-purple hover:bg-purple-hover text-white text-sm px-4 py-1.5 rounded">Save</button>
        </div>
      </div>
    </div>
  )
}
