import React from 'react'
import { useQueue } from '../context/QueueContext'

const STATUS_LABEL = { pending: 'Pending', downloading: 'Downloading', done: 'Done', error: 'Error' }
const STATUS_COLOR = { pending: 'text-yellow-400', downloading: 'text-blue-400', done: 'text-green-400', error: 'text-red-400' }

export default function QueuePage() {
  const { jobs, clearDone, retryJob } = useQueue()

  const active = jobs.filter((j) => j.status !== 'done' && j.status !== 'error')
  const done = jobs.filter((j) => j.status === 'done')
  const errors = jobs.filter((j) => j.status === 'error')

  return (
    <div className="h-full flex flex-col overflow-hidden">
      <div className="flex items-center gap-3 px-6 py-4 border-b border-border shrink-0">
        <h1 className="text-lg font-bold text-text-primary">Download Queue</h1>
        <span className="text-text-muted text-sm">{jobs.length} jobs</span>
        {done.length > 0 && (
          <button onClick={clearDone} className="ml-auto text-sm text-text-secondary border border-border rounded px-3 py-1.5 hover:text-text-primary">
            Clear Done ({done.length})
          </button>
        )}
      </div>

      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-2">
        {jobs.length === 0 && (
          <p className="text-text-muted text-sm p-2">No jobs in queue.</p>
        )}
        {[...active, ...errors, ...done].map((job) => (
          <div key={job.id} className="bg-elevated border border-border rounded-lg p-3 flex items-center gap-3">
            <div className="flex-1 min-w-0">
              <p className="text-text-primary text-sm font-medium truncate">{job.clip_title || `Clip #${job.clip_id}`}</p>
              <p className="text-text-muted text-xs">{job.streamer_name}</p>
              {job.error_msg && <p className="text-red-400 text-xs mt-0.5 truncate">{job.error_msg}</p>}
            </div>
            <div className="flex flex-col items-end gap-1 shrink-0">
              <span className={`text-xs font-medium ${STATUS_COLOR[job.status] || 'text-text-muted'}`}>
                {STATUS_LABEL[job.status] || job.status}
              </span>
              {job.status === 'downloading' && (
                <div className="w-32 h-1.5 bg-surface rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple rounded-full transition-all"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              )}
              {job.status === 'done' && job.local_path && (
                <button
                  onClick={() => window.electron?.openFolder(job.local_path.replace(/[/\\][^/\\]+$/, ''))}
                  className="text-xs text-text-muted hover:text-text-primary"
                >
                  Open folder
                </button>
              )}
              {job.status === 'error' && (
                <button onClick={() => retryJob(job.id)} className="text-xs text-purple hover:text-purple-hover">Retry</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
