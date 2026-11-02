import React from 'react'

export default function TitleBar() {
  const minimize = () => window.electron?.windowMinimize()
  const maximize = () => window.electron?.windowMaximize()
  const close = () => window.electron?.windowClose()

  return (
    <div
      className="flex items-center justify-between h-9 px-3 bg-surface border-b border-border select-none"
      style={{ WebkitAppRegion: 'drag' }}
    >
      <span className="text-xs font-semibold text-text-secondary tracking-wide">GTM Suite</span>
      <div className="flex gap-1" style={{ WebkitAppRegion: 'no-drag' }}>
        <button onClick={minimize} className="w-7 h-5 rounded text-text-muted hover:text-text-primary hover:bg-elevated text-sm flex items-center justify-center">─</button>
        <button onClick={maximize} className="w-7 h-5 rounded text-text-muted hover:text-text-primary hover:bg-elevated text-sm flex items-center justify-center">□</button>
        <button onClick={close} className="w-7 h-5 rounded text-text-muted hover:text-white hover:bg-red-600 text-sm flex items-center justify-center">✕</button>
      </div>
    </div>
  )
}
