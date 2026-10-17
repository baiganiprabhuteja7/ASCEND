import { useCallback, useEffect, useState } from 'react'
import { PageHeading } from '../components/PageHeading.jsx'
import { ProgressRing } from '../components/ProgressRing.jsx'
import { Icon } from '../components/Icon.jsx'
import { getProgress } from '../services/api.js'

export function ProgressPage({ onNavigate }) {
  const [progress, setProgress] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState('')

  const loadProgress = useCallback(async () => {
    setProgress(await getProgress())
  }, [])

  useEffect(() => {
    let isCurrent = true
    getProgress()
      .then((result) => {
        if (isCurrent) {
          setProgress(result)
          setError('')
        }
      })
      .catch((requestError) => {
        if (isCurrent) setError(requestError instanceof Error ? requestError.message : 'Could not load your progress.')
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
      await loadProgress()
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Could not load your progress.')
    } finally {
      setIsLoading(false)
    }
  }

  const total = progress?.total_tasks ?? 0
  const completed = progress?.completed_tasks ?? 0
  const percent = progress?.completion_percentage ?? 0
  const goals = progress?.goals ?? []

  return (
    <>
      <PageHeading eyebrow="NOTICE HOW FAR YOU'VE COME" title="Your progress" description="A clear-eyed look at the goals you set and the actions you have completed." />
      {error && <div className="api-feedback api-feedback-error" role="alert"><span>{error}</span><button className="text-link" onClick={retry}>Try again <Icon name="arrow" size={14} /></button></div>}
      {isLoading && !progress ? (
        <section className="panel plan-empty" role="status"><div className="empty-icon large-empty-icon"><Icon name="clock" size={24} /></div><h2>Loading your progress…</h2><p>Calculating progress from your saved backend goals and tasks.</p></section>
      ) : error && !progress ? (
        <section className="panel plan-empty"><div className="empty-icon large-empty-icon"><Icon name="chart" size={24} /></div><h2>Your progress couldn’t be loaded.</h2><p>Check that the API is running, then try again.</p><button className="button button-primary" onClick={retry}>Retry <Icon name="arrow" size={16} /></button></section>
      ) : (
        <>
          <section className="progress-overview panel"><div className="progress-overview-copy"><span className="eyebrow">ALL YOUR ACTIONS</span><h2>Progress is built<br />one step at a time.</h2><p>{total ? `${completed} of ${total} actions completed across ${progress.total_goals} ${progress.total_goals === 1 ? 'goal' : 'goals'}.` : 'When you start a goal and complete actions, your real progress will show up here.'}</p></div><div className="progress-overview-ring"><ProgressRing value={percent} size={128} /><span>OVERALL</span></div><div className="progress-overview-decoration" /></section>
          <div className="progress-stat-grid">
            <article className="panel progress-stat-card"><span className="stat-icon icon-purple"><Icon name="target" size={17} /></span><span className="stat-label">GOALS CREATED</span><strong>{progress.total_goals}</strong><span className="stat-caption">Your intentions, in one place</span></article>
            <article className="panel progress-stat-card"><span className="stat-icon icon-green"><Icon name="check" size={17} /></span><span className="stat-label">GOALS COMPLETED</span><strong>{progress.completed_goals}</strong><span className="stat-caption">Marked complete by you</span></article>
            <article className="panel progress-stat-card"><span className="stat-icon icon-blue"><Icon name="bolt" size={17} /></span><span className="stat-label">IN PROGRESS</span><strong>{progress.in_progress_goals}</strong><span className="stat-caption">Goals being worked on</span></article>
            <article className="panel progress-stat-card"><span className="stat-icon icon-purple"><Icon name="clock" size={17} /></span><span className="stat-label">NOT STARTED</span><strong>{progress.pending_goals}</strong><span className="stat-caption">Goals waiting for a first step</span></article>
            <article className="panel progress-stat-card"><span className="stat-icon icon-blue"><Icon name="check" size={17} /></span><span className="stat-label">ACTIONS COMPLETED</span><strong>{completed}<small> / {total}</small></strong><span className="stat-caption">Progress you have made</span></article>
            <article className="panel progress-stat-card"><span className="stat-icon icon-green"><Icon name="bolt" size={17} /></span><span className="stat-label">ACTIONS TO GO</span><strong>{progress.pending_tasks}</strong><span className="stat-caption">At your own pace</span></article>
          </div>
          <section className="panel progress-goals"><div className="panel-heading"><div><span className="eyebrow">GOAL BY GOAL</span><h2>Your momentum</h2></div><button className="text-link" onClick={() => onNavigate('/goals')}>Manage goals <Icon name="arrow" size={14} /></button></div>
            {goals.length ? <div className="progress-goal-list">{goals.map((goal) => <article className="progress-goal-row" key={goal.goal_id}><div className="progress-goal-label"><span className="goal-color-mark" /><div><h3>{goal.title}</h3><span>{goal.completed_tasks} of {goal.total_tasks} actions complete</span></div><span className={`goal-status-badge status-${goal.status}`}>{goal.status.replace('_', ' ')}</span><strong>{goal.completion_percentage}%</strong></div><div className="progress-bar"><span style={{ width: `${goal.completion_percentage}%` }} /></div></article>)}</div> : <div className="progress-no-goals"><div className="empty-icon"><Icon name="chart" size={20} /></div><strong>Your progress starts when you do.</strong><span>Create your first goal to see real activity here.</span><button className="text-link" onClick={() => onNavigate('/goals')}>Create a goal <Icon name="arrow" size={14} /></button></div>}
          </section>
          <p className="progress-disclaimer"><Icon name="check" size={14} /> All progress shown is calculated from goals and task changes saved in the backend database.</p>
        </>
      )}
    </>
  )
}
