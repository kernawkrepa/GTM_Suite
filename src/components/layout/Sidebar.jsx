import React from 'react'
import { useQueue } from '../../context/QueueContext'

const NAV = [
  { id: 'home', label: 'Home', icon: '⌂' },
  { id: 'clips', label: 'Clips', icon: '🎬' },
  { id: 'streamers', label: 'Streamers', icon: '👤' },
  { id: 'queue', label: 'Queue', icon: '⬇' },
  { id: 'settings', label: 'Settings', icon: '⚙' },
  { id: 'logs', label: 'Debug Logs', icon: '📋' },
]

export default function Sidebar({ activePage, onNavigate }) {
  const { jobs } = useQueue()
  const activeJobs = jobs.filter((j) => j.status === 'downloading' || j.status === 'pending').length

  return (
    <aside className="w-48 bg-surface border-r border-border flex flex-col py-3 gap-0.5 shrink-0">
      {NAV.map((item) => (
        <button
          key={item.id}
          onClick={() => onNavigate(item.id)}
          className={`flex items-center gap-3 px-4 py-2.5 text-sm transition-colors rounded-none text-left ${
            activePage === item.id
              ? 'bg-purple/20 text-purple border-r-2 border-purple'
              : 'text-text-secondary hover:text-text-primary hover:bg-elevated'
          }`}
        >
          <span className="w-5 text-center">{item.icon}</span>
          <span>{item.label}</span>
          {item.id === 'queue' && activeJobs > 0 && (
            <span className="ml-auto text-xs bg-purple text-white rounded-full w-5 h-5 flex items-center justify-center">
              {activeJobs}
            </span>
          )}
        </button>
      ))}
    </aside>
  )
}
