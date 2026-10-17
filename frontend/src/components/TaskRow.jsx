import { useState } from 'react'
import { Icon } from './Icon.jsx'

export function TaskRow({ task, goalTitle, onToggle, onEdit, onDelete, disabled = false }) {
  const [isEditing, setIsEditing] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [deadline, setDeadline] = useState(task.scheduled_date ?? task.deadline ?? '')
  const scheduled = task.scheduled_date ?? task.deadline
  const scheduledLabel = scheduled
    ? new Date(`${scheduled}T12:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    : task.deadlineLabel ?? 'Unscheduled'
  const durationLabel = task.estimated_minutes
    ? task.estimated_minutes < 60
      ? `${task.estimated_minutes} min`
      : `${Math.floor(task.estimated_minutes / 60)}h${task.estimated_minutes % 60 ? ` ${task.estimated_minutes % 60}m` : ''}`
    : ''

  async function saveTask(event) {
    event.preventDefault()
    setIsSaving(true)
    try {
      const saved = await onEdit(task.id, {
        title: title.trim(),
        deadline: deadline || null,
        scheduled_date: deadline || null,
      })
      if (saved) setIsEditing(false)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className={`task-row${task.done ? ' task-done' : ''}${disabled ? ' task-updating' : ''}`}>
      {isEditing ? (
        <form className="task-edit-form" onSubmit={saveTask}>
          <label className="field">
            <span>Task title</span>
            <input value={title} onChange={(event) => setTitle(event.target.value)} minLength="3" maxLength="160" required />
          </label>
          <label className="field">
            <span>Task date</span>
            <input type="date" value={deadline} onChange={(event) => setDeadline(event.target.value)} />
          </label>
          <div className="task-action-buttons">
            <button className="text-link" type="button" disabled={isSaving} onClick={() => { setTitle(task.title); setDeadline(task.scheduled_date ?? task.deadline ?? ''); setIsEditing(false) }}>Cancel</button>
            <button className="button button-secondary" type="submit" disabled={isSaving}>{isSaving ? 'Saving…' : 'Save'}</button>
          </div>
        </form>
      ) : (
        <>
          <label className="task-toggle">
            <input type="checkbox" checked={task.done} disabled={disabled} onChange={() => onToggle(task.id)} aria-label={`${task.done ? 'Mark incomplete' : 'Complete'}: ${task.title}`} />
            <span className="task-checkbox"><Icon name="check" size={13} /></span>
          </label>
          <span className="task-copy">
            <span className="task-title">{task.title}</span>
            <span className="task-meta">{goalTitle}{task.milestone ? ` · ${task.milestone}` : ''}{durationLabel ? ` · ${durationLabel}` : ''}</span>
            {task.completion_criteria && <span className="task-criteria">Done when: {task.completion_criteria}</span>}
          </span>
          <span className="task-date"><Icon name="calendar" size={13} /> {scheduledLabel}</span>
          {(onEdit || onDelete) && (
            <div className="task-action-buttons">
              {onEdit && <button className="text-link" type="button" disabled={disabled} onClick={() => { setTitle(task.title); setDeadline(task.scheduled_date ?? task.deadline ?? ''); setIsEditing(true) }}>Edit</button>}
              {onDelete && <button className="text-link" type="button" disabled={disabled} onClick={() => onDelete(task.id, task.title)}>Delete</button>}
            </div>
          )}
        </>
      )}
    </div>
  )
}
