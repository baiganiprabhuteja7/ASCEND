import { useCallback, useEffect, useState } from 'react'
import { PageHeading } from '../components/PageHeading.jsx'
import { ProgressRing } from '../components/ProgressRing.jsx'
import { TaskRow } from '../components/TaskRow.jsx'
import { Icon } from '../components/Icon.jsx'
import { getGoals, getProgress, getTasks, updateTask } from '../services/api.js'

async function fetchDashboardData() {
  const [goals, tasks, progress] = await Promise.all([getGoals(), getTasks(), getProgress()])
  return { goals, tasks, progress }
}

export function DashboardPage({ onNavigate }) {
  const [dashboard, setDashboard] = useState({ goals: [], tasks: [], progress: null })
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')
  const [updatingTaskId, setUpdatingTaskId] = useState(null)

  const loadDashboard = useCallback(async () => {
    setDashboard(await fetchDashboardData())
  }, [])

  useEffect(() => {
    let isCurrent = true
    fetchDashboardData()
      .then((result) => {
        if (isCurrent) {
          setDashboard(result)
          setError('')
        }
      })
      .catch((requestError) => {
        if (isCurrent) setError(requestError instanceof Error ? requestError.message : 'Could not load your dashboard.')
      })
      .finally(() => {
        if (isCurrent) setIsLoading(false)
      })
    return () => {
      isCurrent = false
    }
  }, [])

  async function retry() {
    setIsLoading(true)
    setError('')
    try {
      await loadDashboard()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not load your dashboard.')
    } finally {
      setIsLoading(false)
    }
  }

  async function toggleTask(taskId) {
    const task = dashboard.tasks.find((item) => item.id === taskId)
    if (!task || updatingTaskId) return
    setUpdatingTaskId(taskId)
    setError('')
    try {
      await updateTask(taskId, { completed: !task.completed })
      await loadDashboard()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not save this task update.')
    } finally {
      setUpdatingTaskId(null)
    }
  }

  const { goals, tasks, progress } = dashboard
  const totalTasks = progress?.total_tasks ?? tasks.length
  const completedTasks = progress?.completed_tasks ?? tasks.filter((task) => task.completed).length
  const pendingTasks = progress?.pending_tasks ?? Math.max(0, totalTasks - completedTasks)
  const completion = progress?.completion_percentage ?? 0
  const completedGoals = progress?.completed_goals ?? 0
  const inProgressGoals = progress?.in_progress_goals ?? 0
  const upcoming = tasks.filter((task) => !task.completed).slice(0, 4)

  return (
    <>
      <PageHeading eyebrow="TURN GOALS INTO GROWTH" title="Your growth, in motion." description="A focused view of the goals you set and the actions you have saved." />
      {error && <div className="api-feedback api-feedback-error" role="alert"><span>{error}</span><button className="text-link" onClick={retry}>Try again <Icon name="arrow" size={14} /></button></div>}
      <section className="welcome-banner">
        <div className="welcome-decoration welcome-decoration-a" /><div className="welcome-decoration welcome-decoration-b" />
        <div className="welcome-copy"><span className="banner-label">YOUR NEXT STEP</span><h2>Small actions. Real momentum.</h2><p>Choose one goal and give it a clear next move.</p><button className="button button-light" onClick={() => onNavigate('/goals')}>Create a goal <Icon name="arrow" size={16} /></button></div>
        <div className="banner-art" aria-hidden="true"><div className="banner-sun" /><div className="banner-plant plant-left" /><div className="banner-plant plant-right" /><div className="banner-ground" /></div>
      </section>
      {isLoading && !progress ? (
        <section className="panel plan-empty" role="status"><div className="empty-icon large-empty-icon"><Icon name="clock" size={24} /></div><h2>Loading your workspace…</h2><p>Retrieving your saved goals and task progress.</p></section>
      ) : (
        <>
          <div className="stat-grid">
            <article className="stat-card"><div className="stat-top"><span className="stat-label">GOALS SET</span><span className="stat-icon icon-purple"><Icon name="target" size={17} /></span></div><div className="stat-number">{goals.length.toString().padStart(2, '0')}</div><div className="stat-caption">Your saved directions</div></article>
            <article className="stat-card"><div className="stat-top"><span className="stat-label">GOALS COMPLETED</span><span className="stat-icon icon-green"><Icon name="check" size={17} /></span></div><div className="stat-number">{completedGoals.toString().padStart(2, '0')}</div><div className="stat-caption">Marked complete by you</div></article>
            <article className="stat-card"><div className="stat-top"><span className="stat-label">IN PROGRESS</span><span className="stat-icon icon-blue"><Icon name="bolt" size={17} /></span></div><div className="stat-number">{inProgressGoals.toString().padStart(2, '0')}</div><div className="stat-caption">Goals you are working on</div></article>
            <article className="stat-card"><div className="stat-top"><span className="stat-label">ACTIONS COMPLETED</span><span className="stat-icon icon-blue"><Icon name="check" size={17} /></span></div><div className="stat-number">{completedTasks.toString().padStart(2, '0')}<span className="stat-total"> / {totalTasks.toString().padStart(2, '0')}</span></div><div className="stat-caption">Small steps add up</div></article>
            <article className="stat-card"><div className="stat-top"><span className="stat-label">ACTIONS TO GO</span><span className="stat-icon icon-purple"><Icon name="clock" size={17} /></span></div><div className="stat-number">{pendingTasks.toString().padStart(2, '0')}</div><div className="stat-caption">Saved actions not completed</div></article>
            <article className="stat-card progress-stat"><div className="stat-top"><span className="stat-label">OVERALL PROGRESS</span><span className="stat-icon icon-green"><Icon name="bolt" size={17} /></span></div><div className="stat-progress-line"><div><div className="stat-number">{completion}<span className="stat-percent">%</span></div><div className="stat-caption">Across all your actions</div></div><ProgressRing value={completion} /></div></article>
          </div>
          <section className="dashboard-bottom">
            <div className="panel actions-panel"><div className="panel-heading"><div><span className="eyebrow">KEEP YOUR MOMENTUM</span><h2>Next actions</h2></div><button className="text-link" onClick={() => onNavigate('/action-plan')}>View action plan <Icon name="arrow" size={14} /></button></div>
              {upcoming.length ? <div className="task-list">{upcoming.map((task) => { const goal = goals.find((item) => item.id === task.goal_id); return <TaskRow key={task.id} task={{ ...task, done: task.completed }} goalTitle={goal?.title ?? 'Personal goal'} onToggle={toggleTask} disabled={updatingTaskId === task.id} /> })}</div> : <div className="empty-state"><span className="empty-icon"><Icon name="plan" size={20} /></span><strong>{isLoading ? 'Loading your next steps' : 'Your next step starts here'}</strong><span>{isLoading ? 'Fetching saved actions…' : 'Create a goal and generate an action plan to get started.'}</span><button className="text-link" onClick={() => onNavigate(goals.length ? '/action-plan' : '/goals')}>{goals.length ? 'Generate an action plan' : 'Create your first goal'} <Icon name="arrow" size={14} /></button></div>}
            </div>
            <aside className="panel goals-panel"><div className="panel-heading"><div><span className="eyebrow">YOUR DIRECTION</span><h2>Goals</h2></div><button className="icon-button" aria-label="Add a goal" onClick={() => onNavigate('/goals')}><Icon name="plus" size={17} /></button></div>
              {goals.length ? <div className="mini-goal-list">{goals.slice(0, 3).map((goal) => { const related = tasks.filter((task) => task.goal_id === goal.id); const done = related.filter((task) => task.completed).length; const percent = related.length ? Math.round(done / related.length * 100) : 0; return <button className="mini-goal" key={goal.id} onClick={() => onNavigate('/action-plan')}><span className="goal-color-mark" /><span className="mini-goal-copy"><span className="mini-goal-title">{goal.title}</span><span className="mini-goal-subtitle">{goal.skill_level} · {goal.weekly_available_hours} hrs/week</span></span><span className="mini-goal-value">{percent}%</span></button> })}</div> : <div className="goals-empty"><p>Give your skills a direction.</p><span>Your goals will show up here.</span><button className="button button-secondary button-full" onClick={() => onNavigate('/goals')}><Icon name="plus" size={15} /> Add a goal</button></div>}
              <button className="panel-footer-link" onClick={() => onNavigate('/goals')}>See all goals <Icon name="arrow" size={14} /></button>
            </aside>
          </section>
        </>
      )}
    </>
  )
}
