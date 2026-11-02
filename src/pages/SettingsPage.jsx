import React, { useEffect, useState } from 'react'
import { useApp } from '../context/AppContext'

export default function SettingsPage() {
  const { api, settings, fetchSettings, showToast } = useApp()
  const [form, setForm] = useState(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (settings) setForm({ ...settings })
  }, [settings])

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const save = async () => {
    setSaving(true)
    try {
      await api('/settings', { method: 'POST', body: JSON.stringify(form) })
      await fetchSettings()
      showToast('Settings saved', 'success')
    } catch (e) {
      showToast(e.message, 'error')
    } finally {
      setSaving(false)
    }
  }

  const pickFolder = async () => {
    if (window.electron) {
      const res = await window.electron.showOpenDialog({ properties: ['openDirectory'] })
      if (!res.canceled && res.filePaths[0]) setForm((f) => ({ ...f, DEFAULT_DOWNLOAD_PATH: res.filePaths[0] }))
    }
  }

  if (!form) return <div className="p-6 text-text-muted text-sm">Loading settings…</div>

  return (
    <div className="h-full overflow-y-auto p-6">
      <h1 className="text-lg font-bold text-text-primary mb-6">Settings</h1>
      <div className="max-w-lg flex flex-col gap-5">
        <Field label="Twitch Client ID">
          <input value={form.TWITCH_CLIENT_ID || ''} onChange={set('TWITCH_CLIENT_ID')} type="password" className="input-field" />
        </Field>
        <Field label="Twitch Client Secret">
          <input value={form.TWITCH_CLIENT_SECRET || ''} onChange={set('TWITCH_CLIENT_SECRET')} type="password" className="input-field" />
        </Field>
        <Field label="Default Download Path">
          <div className="flex gap-2">
            <input value={form.DEFAULT_DOWNLOAD_PATH || ''} onChange={set('DEFAULT_DOWNLOAD_PATH')} className="input-field flex-1" />
            <button onClick={pickFolder} className="bg-surface border border-border text-text-secondary text-sm px-3 py-2 rounded hover:text-text-primary">Browse</button>
          </div>
        </Field>
        <Field label="Default Language (Discovery)">
          <select value={form.HOME_DEFAULT_LANGUAGE || 'en'} onChange={set('HOME_DEFAULT_LANGUAGE')} className="input-field">
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
            <option value="pt">Portuguese</option>
            <option value="ko">Korean</option>
            <option value="">All</option>
          </select>
        </Field>
        <Field label="Max Concurrent Downloads">
          <input value={form.MAX_CONCURRENT_DOWNLOADS || 5} onChange={set('MAX_CONCURRENT_DOWNLOADS')} type="number" min={1} max={10} className="input-field w-24" />
        </Field>
        <Field label="Max Clips Per Streamer Scan">
          <input value={form.SCAN_MAX_CLIPS_PER_STREAMER || 500} onChange={set('SCAN_MAX_CLIPS_PER_STREAMER')} type="number" min={50} max={2000} className="input-field w-24" />
        </Field>
        <button onClick={save} disabled={saving} className="self-start bg-purple hover:bg-purple-hover text-white text-sm px-5 py-2 rounded disabled:opacity-50">
          {saving ? 'Saving…' : 'Save Settings'}
        </button>
      </div>

      <style>{`.input-field { background: #18181b; border: 1px solid #2d2d35; color: #efeff1; font-size: 0.875rem; border-radius: 0.375rem; padding: 0.5rem 0.75rem; width: 100%; }`}</style>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-sm text-text-secondary font-medium">{label}</label>
      {children}
    </div>
  )
}
