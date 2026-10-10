import { useEffect, useState } from 'react'
import { AppShell } from './components/AppShell.jsx'
import { LandingPage } from './pages/LandingPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { GoalsPage } from './pages/GoalsPage.jsx'
import { ActionPlanPage } from './pages/ActionPlanPage.jsx'
import { ChallengesPage } from './pages/ChallengesPage.jsx'
import { ContributionsPage } from './pages/ContributionsPage.jsx'
import { ProgressPage } from './pages/ProgressPage.jsx'
import './App.css'

const pages = {
  '/dashboard': ['Overview', DashboardPage],
  '/goals': ['My goals', GoalsPage],
  '/action-plan': ['Action plan', ActionPlanPage],
  '/challenges': ['Challenges', ChallengesPage],
  '/contributions': ['Contributions', ContributionsPage],
  '/progress': ['Progress', ProgressPage],
}

function App() {
  const [pathname, setPathname] = useState(window.location.pathname)

  useEffect(() => {
    const handlePopState = () => setPathname(window.location.pathname)
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  function navigate(path) {
    if (path === pathname) return
    window.history.pushState({}, '', path)
    setPathname(path)
    window.scrollTo(0, 0)
  }

  if (pathname === '/') {
    return <LandingPage onNavigate={navigate} />
  }

  const [title, Page] = pages[pathname] ?? pages['/dashboard']

  return (
    <AppShell activePath={pathname in pages ? pathname : '/dashboard'} title={title} onNavigate={navigate}>
      <Page onNavigate={navigate} />
    </AppShell>
  )
}

export default App
