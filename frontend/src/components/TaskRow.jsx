import { Icon } from './Icon.jsx'

export function TaskRow({ task, goalTitle, onToggle, disabled = false }) {
  const scheduled = task.scheduled_date ?? task.deadline
  const scheduledLabel = scheduled
    ? new Date(`${scheduled}T12:00:00`).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
    : task.deadlineLabel ?? 'Unscheduled'
  const durationLabel = task.estimated_minutes
    ? task.estimated_minutes < 60
      ? `${task.estimated_minutes} min`
      : `${Math.floor(task.estimated_minutes / 60)}h${task.estimated_minutes % 60 ? ` ${task.estimated_minutes % 60}m` : ''}`
    : ''

  return (
    <label className={`task-row${task.done ? ' task-done' : ''}${disabled ? ' task-updating' : ''}`}>
      <input type="checkbox" checked={task.done} disabled={disabled} onChange={() => onToggle(task.id)} aria-label={`${task.done ? 'Mark incomplete' : 'Complete'}: ${task.title}`} />
      <span className="task-checkbox"><Icon name="check" size={13} /></span>
      <span className="task-copy">
        <span className="task-title">{task.title}</span>
        <span className="task-meta">{goalTitle}{task.milestone ? ` · ${task.milestone}` : ''}{durationLabel ? ` · ${durationLabel}` : ''}</span>
        {task.completion_criteria && <span className="task-criteria">Done when: {task.completion_criteria}</span>}
      </span>
      <span className="task-date"><Icon name="calendar" size={13} /> {scheduledLabel}</span>
    </label>
  )
}
