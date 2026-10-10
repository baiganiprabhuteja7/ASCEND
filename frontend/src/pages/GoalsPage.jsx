import { useEffect, useState } from 'react'
import { PageHeading } from '../components/PageHeading.jsx'
import { ProgressRing } from '../components/ProgressRing.jsx'
import { Icon } from '../components/Icon.jsx'
import { createGoal, getGoals, getTasks } from '../services/api.js'

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
      setCreatedGoal(savedGoal)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not save this goal.')
      setIsSaving(false)
      return
    }

    try {
      const result = await fetchGoalsWithTasks()
      setGoals(result.goals)
      setTasksByGoal(result.tasksByGoal)
      setIsAdding(false)
      form.reset()
    } catch (requestError) {
      setError(`The goal was created by the API, but refreshing the goal list failed: ${requestError instanceof Error ? requestError.message : 'Please reload the page.'}`)
    } finally {
      setIsSaving(false)
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
        action={!isLoading && !isAdding && <button className="button button-primary" onClick={() => setIsAdding(true)}><Icon name="plus" size={16} /> Add a goal</button>}
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
              <div><span className="eyebrow">START SOMEWHERE GOOD</span><h2>Create a goal</h2><p>Keep it personal, practical, and yours.</p></div>
              {goals.length > 0 && <button className="icon-button" aria-label="Close form" onClick={() => setIsAdding(false)}>×</button>}
            </div>
            <form className="goal-form" onSubmit={addGoal}>
              <label className="field field-wide"><span>What would you like to work toward? <b>*</b></span><input name="title" type="text" placeholder="e.g. Learn the basics of community gardening" required maxLength="120" minLength="3" /></label>
              <label className="field field-wide"><span>A little more about it <small>Optional</small></span><textarea name="description" placeholder="Why does this goal matter to you?" rows="3" maxLength="2000" /></label>
              <label className="field"><span>Target date <b>*</b></span><input name="deadline" type="date" required min={today} /></label>
              <label className="field"><span>Current skill level <b>*</b></span><select name="skillLevel" defaultValue="" required><option value="" disabled>Select your starting point</option><option>Just getting started</option><option>Some experience</option><option>Comfortable</option><option>Ready to deepen</option></select></label>
              <label className="field"><span>Hours available each week <b>*</b></span><div className="input-suffix"><input name="weeklyHours" type="number" min="1" max="168" step="1" placeholder="3" required /><span>hours / week</span></div></label>
              <label className="field"><span>How do you like to learn? <small>Optional</small></span><select name="learningStyle" defaultValue=""><option value="">A mix of approaches</option><option>Hands-on practice</option><option>Reading and written notes</option><option>Videos and demonstrations</option><option>Short guided sessions</option><option>Learning with other people</option></select></label>
              <label className="field field-wide"><span>Anything to plan around? <small>Optional</small></span><textarea name="learningConstraints" placeholder="For example: short weekday sessions, limited equipment, or accessibility needs." rows="2" maxLength="2000" /></label>
              <div className="form-actions"><span>Saved to the backend. Your plan will be generated from this goal and your availability.</span><button className="button button-primary" type="submit" disabled={isSaving}>{isSaving ? 'Saving…' : 'Create goal'} {!isSaving && <Icon name="arrow" size={16} />}</button></div>
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
                </article>
              )
            })}</section>
          )}
        </>
      )}
    </>
  )
}
