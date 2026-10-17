import { useCallback, useEffect, useState } from 'react'
import { PageHeading } from '../components/PageHeading.jsx'
import { TaskRow } from '../components/TaskRow.jsx'
import { Icon } from '../components/Icon.jsx'
import { createTask, deleteTask, generateGoalPlan, getGoalPlan, getGoals, updateTask } from '../services/api.js'

function dateLabel(value) {
  if (!value) return 'No date'
  return new Date(`${value}T12:00:00`).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function allGoalTasks(plan) {
  return [
    ...(plan?.milestones ?? []).flatMap((milestone) => milestone.tasks),
    ...(plan?.unassigned_tasks ?? []),
  ]
}

async function fetchPlanData() {
  const goals = await getGoals()
  const plans = await Promise.all(goals.map((goal) => getGoalPlan(goal.id)))
  return {
    goals,
    plansByGoal: Object.fromEntries(goals.map((goal, index) => [goal.id, plans[index]])),
  }
}

export function ActionPlanPage({ onNavigate }) {
  const [goals, setGoals] = useState([])
  const [plansByGoal, setPlansByGoal] = useState({})
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [generationError, setGenerationError] = useState('')
  const [failedGenerationGoalId, setFailedGenerationGoalId] = useState(null)
  const [updatingTaskId, setUpdatingTaskId] = useState(null)
  const [deletingTaskId, setDeletingTaskId] = useState(null)
  const [generatingGoalId, setGeneratingGoalId] = useState(null)
  const [addingTaskGoalId, setAddingTaskGoalId] = useState(null)
  const [savingTaskGoalId, setSavingTaskGoalId] = useState(null)

  const loadPlan = useCallback(async () => {
    const plan = await fetchPlanData()
    setGoals(plan.goals)
    setPlansByGoal(plan.plansByGoal)
  }, [])

  useEffect(() => {
    let isCurrent = true
    fetchPlanData()
      .then((plan) => {
        if (!isCurrent) return
        setGoals(plan.goals)
        setPlansByGoal(plan.plansByGoal)
        setError('')
      })
      .catch((requestError) => {
        if (isCurrent) setError(requestError instanceof Error ? requestError.message : 'Could not load your action plan.')
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false)
      })
    return () => {
      isCurrent = false
    }
  }, [])

  async function retryPlan() {
    setIsLoading(true)
    setError('')
    try {
      await loadPlan()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not load your action plan.')
    } finally {
      setIsLoading(false)
    }
  }

  async function generatePlan(goalId) {
    if (generatingGoalId || updatingTaskId || deletingTaskId || savingTaskGoalId) return
    const plan = plansByGoal[goalId]
    const hasExistingActions = allGoalTasks(plan).length > 0
    const hasExistingPlan = Boolean(plan?.source || plan?.milestones?.length)
    const replacing = hasExistingActions || hasExistingPlan
    if (replacing && !window.confirm('Update this plan? Unfinished generated tasks will be archived. Completed tasks and manually added tasks will be kept.')) return

    setGeneratingGoalId(goalId)
    setGenerationError('')
    setFailedGenerationGoalId(null)
    setError('')
    try {
      await generateGoalPlan(goalId, replacing)
      await loadPlan()
    } catch (requestError) {
      setGenerationError(requestError instanceof Error ? requestError.message : 'Could not generate this plan.')
      setFailedGenerationGoalId(goalId)
    } finally {
      setGeneratingGoalId(null)
    }
  }

  async function toggleTask(taskId) {
    const task = Object.values(plansByGoal).flatMap(allGoalTasks).find((item) => item.id === taskId)
    if (!task || updatingTaskId || deletingTaskId || generatingGoalId) return

    setUpdatingTaskId(taskId)
    setError('')
    let wasUpdated = false
    try {
      await updateTask(taskId, { completed: !task.completed })
      wasUpdated = true
      await loadPlan()
    } catch (requestError) {
      const detail = requestError instanceof Error ? requestError.message : 'Please reload the action plan.'
      setError(wasUpdated
        ? `The task was updated, but refreshing the action plan failed: ${detail}`
        : detail)
    } finally {
      setUpdatingTaskId(null)
    }
  }

  async function editTask(taskId, changes) {
    setError('')
    let wasUpdated = false
    try {
      await updateTask(taskId, changes)
      wasUpdated = true
      await loadPlan()
      return true
    } catch (requestError) {
      const detail = requestError instanceof Error ? requestError.message : 'Please reload the action plan.'
      setError(wasUpdated
        ? `The task was updated, but refreshing the action plan failed: ${detail}`
        : detail)
      return false
    }
  }

  async function removeTask(taskId, title) {
    if (deletingTaskId || updatingTaskId || generatingGoalId) return
    if (!window.confirm(`Delete “${title}”? This cannot be undone.`)) return
    setError('')
    setDeletingTaskId(taskId)
    let wasDeleted = false
    try {
      await deleteTask(taskId)
      wasDeleted = true
      await loadPlan()
    } catch (requestError) {
      const detail = requestError instanceof Error ? requestError.message : 'Please reload the action plan.'
      setError(wasDeleted
        ? `The task was deleted, but refreshing the action plan failed: ${detail}`
        : detail)
    } finally {
      setDeletingTaskId(null)
    }
  }

  async function addTask(event, goalId) {
    event.preventDefault()
    if (generatingGoalId || deletingTaskId) return
    const form = event.currentTarget
    if (!form.reportValidity()) return
    const formData = new FormData(form)
    const title = String(formData.get('title')).trim()
    const milestone = String(formData.get('milestone')).trim()
    const deadline = String(formData.get('deadline'))

    setSavingTaskGoalId(goalId)
    setError('')
    try {
      await createTask({
        goal_id: goalId,
        title,
        milestone: milestone || null,
        deadline: deadline || null,
      })
      await loadPlan()
      setAddingTaskGoalId(null)
      form.reset()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not create this task.')
    } finally {
      setSavingTaskGoalId(null)
    }
  }

  return (
    <>
      <PageHeading eyebrow="FROM INTENTION TO ACTION" title="Your action plan" description="Generate a personal, scheduled path from each goal to its next meaningful step." />
      {error && (
        <div className="api-feedback api-feedback-error" role="alert">
          <span>{error}</span>
          <button className="text-link" onClick={retryPlan}>Try again <Icon name="arrow" size={14} /></button>
        </div>
      )}
      {generationError && (
        <div className="api-feedback api-feedback-error" role="alert">
          <span>{generationError}</span>
          <button className="text-link" onClick={() => generatePlan(failedGenerationGoalId)}>Retry generation <Icon name="arrow" size={14} /></button>
        </div>
      )}
      {isLoading ? (
        <section className="panel plan-empty" role="status">
          <div className="empty-icon large-empty-icon"><Icon name="clock" size={24} /></div>
          <h2>Loading your action plan…</h2>
          <p>Getting your saved goals, milestones, and tasks from the ASCEND API.</p>
        </section>
      ) : error && goals.length === 0 ? (
        <section className="panel plan-empty">
          <div className="empty-icon large-empty-icon"><Icon name="plan" size={25} /></div>
          <h2>Your action plan couldn’t be loaded.</h2>
          <p>Check that the API is running, then try loading your plan again.</p>
          <button className="button button-primary" onClick={retryPlan}>Retry <Icon name="arrow" size={16} /></button>
        </section>
      ) : goals.length === 0 ? (
        <section className="panel plan-empty">
          <div className="empty-icon large-empty-icon"><Icon name="plan" size={25} /></div>
          <h2>Your plan will take shape here.</h2>
          <p>No goals have been saved to the backend yet. Create a goal to get started.</p>
          <button className="button button-primary" onClick={() => onNavigate('/goals')}>Create a goal <Icon name="arrow" size={16} /></button>
        </section>
      ) : (
        <div className="plan-goals">
          {goals.map((goal, goalIndex) => {
            const plan = plansByGoal[goal.id]
            const goalTasks = allGoalTasks(plan)
            const completed = goalTasks.filter((task) => task.completed).length
            const milestones = plan?.milestones ?? []
            const isGenerating = generatingGoalId === goal.id
            const nextAction = plan?.next_action
            return (
              <section className="panel plan-goal" key={goal.id}>
                <div className="plan-goal-heading">
                  <div>
                    <span className="eyebrow">GOAL {String(goalIndex + 1).padStart(2, '0')}</span>
                    <h2>{goal.title}</h2>
                    <p>{completed} of {goalTasks.length} actions complete <span>·</span> Target {dateLabel(goal.deadline)}</p>
                    {plan?.source && (
                      <span className={`plan-source plan-source-${plan.source}`}>
                        {plan.source === 'ai' ? 'AI-assisted plan' : 'Deterministic fallback plan'}
                      </span>
                    )}
                  </div>
                  <div className="plan-summary">
                    <strong>{goal.weekly_available_hours}h</strong>
                    <span>per week</span>
                    {(goalTasks.length > 0 || plan?.source) && (
                      <button className="text-link plan-generate-link" disabled={Boolean(generatingGoalId || updatingTaskId || savingTaskGoalId)} onClick={() => generatePlan(goal.id)}>
                        {isGenerating ? 'Generating…' : plan?.source ? 'Regenerate plan' : 'Generate my action plan'}
                      </button>
                    )}
                  </div>
                </div>
                {plan?.source === 'fallback' && (
                  <div className="plan-provenance">This plan was created with the built-in fallback planner because an AI provider was not available.</div>
                )}
                {nextAction && (
                  <div className="plan-next-action"><Icon name="arrow" size={14} /><span><strong>Next action</strong>{nextAction.title}</span></div>
                )}
                {milestones.map((milestone, index) => {
                  const milestoneTasks = milestone.tasks.map((task) => ({ ...task, done: task.completed }))
                  const milestoneDone = milestoneTasks.filter((task) => task.completed).length
                  return (
                    <div className="milestone" key={milestone.id}>
                      <div className={`milestone-number${milestoneDone === milestoneTasks.length && milestoneTasks.length ? ' milestone-complete' : ''}`}>
                        {milestoneDone === milestoneTasks.length && milestoneTasks.length ? <Icon name="check" size={15} /> : String(index + 1).padStart(2, '0')}
                      </div>
                      <div className="milestone-content">
                        <div className="milestone-title-row">
                          <h3>{milestone.title}</h3>
                          <span>{milestoneDone}/{milestoneTasks.length} · by {dateLabel(milestone.target_date)}</span>
                        </div>
                        {milestone.description && <p className="milestone-description">{milestone.description}</p>}
                        {milestoneTasks.map((task) => (
                          <TaskRow
                            key={task.id}
                            task={task}
                            goalTitle={goal.title}
                            onToggle={toggleTask}
                            onEdit={editTask}
                            onDelete={removeTask}
                            disabled={Boolean(updatingTaskId || generatingGoalId || deletingTaskId)}
                          />
                        ))}
                      </div>
                    </div>
                  )
                })}
                {plan?.unassigned_tasks?.length > 0 && (
                  <div className="milestone">
                    <div className="milestone-number">+</div>
                    <div className="milestone-content">
                      <div className="milestone-title-row"><h3>Other actions</h3><span>{plan.unassigned_tasks.filter((task) => task.completed).length}/{plan.unassigned_tasks.length}</span></div>
                      {plan.unassigned_tasks.map((task) => (
                        <TaskRow key={task.id} task={{ ...task, done: task.completed }} goalTitle={goal.title} onToggle={toggleTask} onEdit={editTask} onDelete={removeTask} disabled={Boolean(updatingTaskId || generatingGoalId || deletingTaskId)} />
                      ))}
                    </div>
                  </div>
                )}
                {goalTasks.length === 0 && (
                  <div className="milestone-empty plan-no-tasks">
                    <span className="empty-icon"><Icon name="plan" size={18} /></span>
                    <span>No plan has been generated for this goal yet.</span>
                    <button className="button button-primary" disabled={Boolean(generatingGoalId)} onClick={() => generatePlan(goal.id)}>
                      {isGenerating ? 'Generating your plan…' : 'Generate my action plan'} {!isGenerating && <Icon name="arrow" size={15} />}
                    </button>
                    <small>Your goal, skill level, available time, deadline, and preferences shape the plan.</small>
                  </div>
                )}
                {addingTaskGoalId === goal.id ? (
                  <form className="action-task-form" onSubmit={(event) => addTask(event, goal.id)}>
                    <label className="field">
                      <span>Task <b>*</b></span>
                      <input name="title" type="text" placeholder="What action will you take?" minLength="3" maxLength="160" required />
                    </label>
                    <div className="action-task-form-row">
                      <label className="field">
                        <span>Milestone <small>Optional</small></span>
                        <input name="milestone" type="text" placeholder="e.g. Build your foundation" maxLength="120" />
                      </label>
                      <label className="field">
                        <span>Deadline <small>Optional</small></span>
                        <input name="deadline" type="date" />
                      </label>
                    </div>
                    <div className="action-task-form-actions">
                      <button type="button" className="text-link" onClick={() => setAddingTaskGoalId(null)}>Cancel</button>
                      <button type="submit" className="button button-primary" disabled={savingTaskGoalId === goal.id}>
                        {savingTaskGoalId === goal.id ? 'Saving…' : 'Save task'}
                        {savingTaskGoalId !== goal.id && <Icon name="check" size={15} />}
                      </button>
                    </div>
                  </form>
                ) : (
                  <button className="add-action-link" onClick={() => setAddingTaskGoalId(goal.id)}>
                    <Icon name="plus" size={15} /> Add a task
                  </button>
                )}
              </section>
            )
          })}
        </div>
      )}
    </>
  )
}
