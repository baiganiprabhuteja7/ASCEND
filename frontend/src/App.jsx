import { useCallback, useEffect, useState } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { AppShell } from './components/AppShell.jsx'
import { AuthPage } from './pages/AuthPage.jsx'
import { LandingPage } from './pages/LandingPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { GoalsPage } from './pages/GoalsPage.jsx'
import { ActionPlanPage } from './pages/ActionPlanPage.jsx'
import { ChallengesPage } from './pages/ChallengesPage.jsx'
import { ContributionsPage } from './pages/ContributionsPage.jsx'
import { ProgressPage } from './pages/ProgressPage.jsx'
import { ApiError, getCurrentUser, logout as logoutRequest } from './services/api.js'
import './App.css'

const pages = {
  '/dashboard': ['Overview', DashboardPage],
  '/goals': ['My goals', GoalsPage],
  '/action-plan': ['Action plan', ActionPlanPage],
  '/challenges': ['Challenges', ChallengesPage],
  '/contributions': ['Contributions', ContributionsPage],
  '/progress': ['Progress', ProgressPage],
}

function AuthenticatedApp({ user, authLoading, authError, onRetry, onLogout }) {
  const pathname = useLocation().pathname
  const navigate = useNavigate()

  if (authLoading) {
    return <main className="auth-loading" role="status">Loading your secure workspace…</main>
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (authError) {
    return (
      <main className="auth-loading">
        <div className="api-feedback api-feedback-error" role="alert">{authError}</div>
        <button className="button button-secondary" onClick={onRetry}>Try again</button>
      </main>
    )
  }

  const [title] = pages[pathname] ?? pages['/dashboard']

  return (
    <AppShell
      activePath={pathname in pages ? pathname : '/dashboard'}
      title={title}
      onNavigate={(path) => navigate(path)}
      user={user}
      onLogout={onLogout}
    >
      <Outlet />
    </AppShell>
  )
}

function App() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [authLoading, setAuthLoading] = useState(true)
  const [authError, setAuthError] = useState('')
  const [authAttempt, setAuthAttempt] = useState(0)

  useEffect(() => {
    let isCurrent = true
    getCurrentUser()
      .then((currentUser) => {
        if (isCurrent) setUser(currentUser)
      })
      .catch((requestError) => {
        if (!isCurrent) return
        if (!(requestError instanceof ApiError && requestError.status === 401)) {
          setAuthError(requestError instanceof Error ? requestError.message : 'Could not connect to ASCEND.')
        }
      })
      .finally(() => {
        if (isCurrent) setAuthLoading(false)
      })
    return () => {
      isCurrent = false
    }
  }, [authAttempt])

  const retryAuth = useCallback(() => {
    setAuthError('')
    setAuthLoading(true)
    setAuthAttempt((attempt) => attempt + 1)
  }, [])

  async function handleLogout() {
    try {
      await logoutRequest()
      setUser(null)
      navigate('/login')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setUser(null)
        navigate('/login')
        return
      }
      throw error
    }
  }

  function authPage(mode) {
    return user
      ? <Navigate to="/dashboard" replace />
      : (
        <AuthPage
          mode={mode}
          onNavigate={navigate}
          onAuthenticated={(authenticatedUser) => {
            setUser(authenticatedUser)
            setAuthError('')
            navigate('/dashboard')
          }}
          initializationError={authError}
          onRetry={retryAuth}
        />
      )
  }

  const authenticatedApp = (
    <AuthenticatedApp
      user={user}
      authLoading={authLoading}
      authError={authError}
      onRetry={retryAuth}
      onLogout={handleLogout}
    />
  )

  return (
    <Routes>
      <Route path="/" element={<LandingPage onNavigate={navigate} isAuthenticated={Boolean(user)} />} />
      <Route path="/login" element={authPage('login')} />
      <Route path="/signup" element={authPage('signup')} />
      <Route element={authenticatedApp}>
        <Route path="/dashboard" element={<DashboardPage onNavigate={navigate} />} />
        <Route path="/goals" element={<GoalsPage onNavigate={navigate} />} />
        <Route path="/action-plan" element={<ActionPlanPage onNavigate={navigate} />} />
        <Route path="/challenges" element={<ChallengesPage />} />
        <Route path="/contributions" element={<ContributionsPage />} />
        <Route path="/progress" element={<ProgressPage onNavigate={navigate} />} />
      </Route>
      <Route path="*" element={<Navigate to={user ? '/dashboard' : '/'} replace />} />
    </Routes>
  )
}

export default App
