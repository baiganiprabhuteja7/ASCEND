import { useEffect, useState } from 'react'
import { PageHeading } from '../components/PageHeading.jsx'
import { ProgressRing } from '../components/ProgressRing.jsx'
import { Icon } from '../components/Icon.jsx'
import { createGoal, deleteGoal, getGoals, getTasks, updateGoal } from '../services/api.js'

const today = new Date().toISOString().slice(0, 10)

function dateLabel(value) {
  if (!value) return 'No deadline'
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

async function fetchGoalsWithTasks() {
  const goals = await getGoals()
  const taskLists = await Promise.all(goals.map((goal) => getTasks(goal.id)))
  return {
    goals,
    tasksByGoal: Object.fromEntries(
      goals.map((goal, index) => [goal.id, taskLists[index]]),
    ),
  }
}

export function GoalsPage({ onNavigate }) {
  const [goals, setGoals] = useState([])
  const [tasksByGoal, setTasksByGoal] = useState({})
  const [isLoading, setIsLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [deletingGoalId, setDeletingGoalId] = useState(null)
  const [editingGoal, setEditingGoal] = useState(null)
  const [createdGoal, setCreatedGoal] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let isCurrent = true
    fetchGoalsWithTasks()
      .then((result) => {
        if (!isCurrent) return
        setGoals(result.goals)
        setTasksByGoal(result.tasksByGoal)
        setIsAdding(result.goals.length === 0)
      })
      .catch((requestError) => {
        if (!isCurrent) return
        setError(requestError instanceof Error ? requestError.message : 'Could not load your goals.')
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false)
      })
    return () => {
      isCurrent = false
    }
  }, [])

  async function addGoal(event) {
    event.preventDefault()
    const form = event.currentTarget
    if (!form.reportValidity()) return
    const formData = new FormData(form)

    setIsSaving(true)
    setError('')
    setCreatedGoal(null)
    let wasCreated = false
    try {
      const savedGoal = await createGoal({
        title: String(formData.get('title')).trim(),
        description: String(formData.get('description')).trim(),
        deadline: String(formData.get('deadline')) || null,
        skill_level: String(formData.get('skillLevel')),
        weekly_available_hours: Number(formData.get('weeklyHours')),
        learning_style: String(formData.get('learningStyle')),
        learning_constraints: String(formData.get('learningConstraints')).trim(),
      })
      wasCreated = true
      setCreatedGoal(savedGoal)
      const result = await fetchGoalsWithTasks()
      setGoals(result.goals)
      setTasksByGoal(result.tasksByGoal)
      setIsAdding(false)
      form.reset()
    } catch (requestError) {
      const detail = requestError instanceof Error ? requestError.message : 'Please reload the page.'
      setError(wasCreated
        ? `The goal was created, but refreshing the goal list failed: ${detail}`
        : detail)
    } finally {
      setIsSaving(false)
    }
  }

  async function saveGoal(event) {
    event.preventDefault()
    const form = event.currentTarget
    if (!form.reportValidity() || !editingGoal) return
    const formData = new FormData(form)

    setIsSaving(true)
    setError('')
    let wasUpdated = false
    try {
      await updateGoal(editingGoal.id, {
        title: String(formData.get('title')).trim(),
        description: String(formData.get('description')).trim(),
        status: String(formData.get('status')),
        deadline: String(formData.get('deadline')) || null,
        skill_level: String(formData.get('skillLevel')),
        weekly_available_hours: Number(formData.get('weeklyHours')),
        learning_style: String(formData.get('learningStyle')),
        learning_constraints: String(formData.get('learningConstraints')).trim(),
      })
      wasUpdated = true
      const result = await fetchGoalsWithTasks()
      setGoals(result.goals)
      setTasksByGoal(result.tasksByGoal)
      setIsAdding(false)
      setEditingGoal(null)
    } catch (requestError) {
      const detail = requestError instanceof Error ? requestError.message : 'Please reload the page.'
      setError(wasUpdated
        ? `The goal was updated, but refreshing the goal list failed: ${detail}`
        : detail)
    } finally {
      setIsSaving(false)
    }
  }

  async function removeGoal(goal) {
    if (!window.confirm(`Delete “${goal.title}” and all of its tasks? This cannot be undone.`)) return
    setDeletingGoalId(goal.id)
    setError('')
    let wasDeleted = false
    try {
      await deleteGoal(goal.id)
      wasDeleted = true
      const result = await fetchGoalsWithTasks()
      setGoals(result.goals)
      setTasksByGoal(result.tasksByGoal)
      if (editingGoal?.id === goal.id) {
        setEditingGoal(null)
        setIsAdding(false)
      }
    } catch (requestError) {
      const detail = requestError instanceof Error ? requestError.message : 'Please reload the page.'
      setError(wasDeleted
        ? `The goal was deleted, but refreshing the goal list failed: ${detail}`
        : detail)
    } finally {
      setDeletingGoalId(null)
    }
  }

  async function changeGoalStatus(goalId, status) {
    setError('')
    try {
      const updatedGoal = await updateGoal(goalId, { status })
      setGoals((currentGoals) => currentGoals.map((goal) => goal.id === goalId ? updatedGoal : goal))
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not update this goal’s status.')
    }
  }

  async function retryLoad() {
    setIsLoading(true)
    setError('')
    try {
      const result = await fetchGoalsWithTasks()
      setGoals(result.goals)
      setTasksByGoal(result.tasksByGoal)
      setIsAdding(result.goals.length === 0)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not load your goals.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      <PageHeading
        eyebrow="AIM WITH INTENTION"
        title="Your goals"
        description="Give your learning a direction that feels meaningful to you."
        action={!isLoading && !isAdding && <button className="button button-primary" onClick={() => { setEditingGoal(null); setIsAdding(true) }}><Icon name="plus" size={16} /> Add a goal</button>}
      />
      {error && (
        <div className="api-feedback api-feedback-error" role="alert">
          <span>{error}</span>
          {!isSaving && <button className="text-link" onClick={retryLoad}>Try again <Icon name="arrow" size={14} /></button>}
        </div>
      )}
      {createdGoal && (
        <div className="goal-created-banner" role="status">
          <div><strong>“{createdGoal.title}” is saved.</strong><span>Next, generate a scheduled action plan for this goal.</span></div>
          <button className="button button-primary" onClick={() => onNavigate('/action-plan')}>Generate my action plan <Icon name="arrow" size={15} /></button>
        </div>
      )}
      {isLoading ? (
        <section className="panel plan-empty" role="status">
          <div className="empty-icon large-empty-icon"><Icon name="clock" size={24} /></div>
          <h2>Loading your goals…</h2>
          <p>Getting your saved goals from the ASCEND API.</p>
        </section>
      ) : (
        <>
          {isAdding && <section className="panel goal-form-panel">
            <div className="form-heading">
              <div><span className="eyebrow">{editingGoal ? 'REFINE YOUR DIRECTION' : 'START SOMEWHERE GOOD'}</span><h2>{editingGoal ? 'Edit goal' : 'Create a goal'}</h2><p>Keep it personal, practical, and yours.</p></div>
              {goals.length > 0 && <button className="icon-button" aria-label="Close form" onClick={() => { setIsAdding(false); setEditingGoal(null) }}>×</button>}
            </div>
            <form className="goal-form" key={editingGoal?.id ?? 'new-goal'} onSubmit={editingGoal ? saveGoal : addGoal}>
              <label className="field field-wide"><span>What would you like to work toward? <b>*</b></span><input name="title" type="text" placeholder="e.g. Learn the basics of community gardening" defaultValue={editingGoal?.title ?? ''} required maxLength="120" minLength="3" /></label>
              <label className="field field-wide"><span>A little more about it <small>Optional</small></span><textarea name="description" placeholder="Why does this goal matter to you?" rows="3" defaultValue={editingGoal?.description ?? ''} maxLength="2000" /></label>
              {editingGoal && <label className="field"><span>Goal status</span><select name="status" defaultValue={editingGoal.status}><option value="not_started">Not started</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select></label>}
              <label className="field"><span>Target date <b>*</b></span><input name="deadline" type="date" defaultValue={editingGoal?.deadline ?? ''} required min={editingGoal?.deadline && editingGoal.deadline < today ? editingGoal.deadline : today} /></label>
              <label className="field"><span>Current skill level <b>*</b></span><select name="skillLevel" defaultValue={editingGoal?.skill_level ?? ''} required><option value="" disabled>Select your starting point</option><option>Just getting started</option><option>Some experience</option><option>Comfortable</option><option>Ready to deepen</option></select></label>
              <label className="field"><span>Hours available each week <b>*</b></span><div className="input-suffix"><input name="weeklyHours" type="number" min="1" max="168" step="1" placeholder="3" defaultValue={editingGoal?.weekly_available_hours ?? ''} required /><span>hours / week</span></div></label>
              <label className="field"><span>How do you like to learn? <small>Optional</small></span><select name="learningStyle" defaultValue={editingGoal?.learning_style ?? ''}><option value="">A mix of approaches</option><option>Hands-on practice</option><option>Reading and written notes</option><option>Videos and demonstrations</option><option>Short guided sessions</option><option>Learning with other people</option></select></label>
              <label className="field field-wide"><span>Anything to plan around? <small>Optional</small></span><textarea name="learningConstraints" placeholder="For example: short weekday sessions, limited equipment, or accessibility needs." rows="2" defaultValue={editingGoal?.learning_constraints ?? ''} maxLength="2000" /></label>
              <div className="form-actions"><span>Saved to the backend. Your plan will be generated from this goal and your availability.</span><button className="button button-primary" type="submit" disabled={isSaving}>{isSaving ? 'Saving…' : editingGoal ? 'Save changes' : 'Create goal'} {!isSaving && <Icon name="arrow" size={16} />}</button></div>
            </form>
          </section>}
          {goals.length === 0 ? (
            !isAdding && <section className="panel goals-page-empty"><div className="empty-icon large-empty-icon"><Icon name="target" size={25} /></div><h2>Your first goal begins with a thought.</h2><p>Pick something you'd like to learn or do, and we’ll help break it into small actions.</p><button className="button button-primary" onClick={() => setIsAdding(true)}><Icon name="plus" size={16} /> Create your first goal</button></section>
          ) : (
            <section className="goals-card-grid">{goals.map((goal, index) => {
              const tasks = tasksByGoal[goal.id] ?? []
              const done = tasks.filter((task) => task.completed).length
              const percent = tasks.length ? Math.round(done / tasks.length * 100) : 0
              return (
                <article className="panel goal-card" key={goal.id}>
                  <div className={`goal-card-accent accent-${index % 3}`} />
                  <div className="goal-card-top"><span className="goal-category"><Icon name={index % 2 ? 'leaf' : 'sparkles'} size={14} /> PERSONAL GROWTH</span><ProgressRing value={percent} size={56} /></div>
                  <h2>{goal.title}</h2>
                  <p className="goal-description">{goal.description || 'A goal you are working toward, one step at a time.'}</p>
                  <div className="goal-detail-row"><span><Icon name="calendar" size={14} /> {dateLabel(goal.deadline)}</span><span><Icon name="clock" size={14} /> {goal.weekly_available_hours}h / week</span></div>
                  <div className="goal-skill">{goal.skill_level}</div>
                  <div className="goal-card-bottom"><span>{done} of {tasks.length} actions complete</span><button className="text-link" onClick={() => onNavigate('/action-plan')}>{goal.plan_generated_at ? 'View plan' : 'Generate plan'} <Icon name="arrow" size={13} /></button></div>
                  <label className="goal-status-control"><span>Status</span><select aria-label={`Status for ${goal.title}`} value={goal.status} disabled={Boolean(deletingGoalId)} onChange={(event) => changeGoalStatus(goal.id, event.target.value)}><option value="not_started">Not started</option><option value="in_progress">In progress</option><option value="completed">Completed</option></select></label>
                  <div className="goal-card-actions">
                    <button className="button button-secondary" disabled={Boolean(deletingGoalId)} onClick={() => { setEditingGoal(goal); setIsAdding(true); setCreatedGoal(null) }}>Edit goal</button>
                    <button className="text-link" disabled={deletingGoalId === goal.id} onClick={() => removeGoal(goal)}>{deletingGoalId === goal.id ? 'Deleting…' : 'Delete goal'}</button>
                  </div>
                </article>
              )
            })}</section>
          )}
        </>
      )}
    </>
  )
}
