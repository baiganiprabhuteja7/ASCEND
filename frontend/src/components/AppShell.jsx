import { useEffect, useState } from 'react'
import { Icon } from './Icon.jsx'
import { Brand } from './Brand.jsx'

const navigation = [
  { label: 'Overview', path: '/dashboard', icon: 'home' },
  { label: 'My goals', path: '/goals', icon: 'target' },
  { label: 'Action plan', path: '/action-plan', icon: 'plan' },
  { label: 'Challenges', path: '/challenges', icon: 'sparkles' },
  { label: 'Contributions', path: '/contributions', icon: 'heart' },
  { label: 'Progress', path: '/progress', icon: 'chart' },
]

export function AppShell({ activePath, title, onNavigate, user, onLogout, children }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const [logoutError, setLogoutError] = useState('')

  useEffect(() => {
    if (!isMenuOpen) return undefined
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setIsMenuOpen(false)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [isMenuOpen])

  function navigate(path) {
    setIsMenuOpen(false)
    onNavigate(path)
  }

  async function logout() {
    setLogoutError('')
    try {
      await onLogout()
    } catch (error) {
      setLogoutError(error instanceof Error ? error.message : 'Could not log out. Please try again.')
    }
  }

  const initials = user.full_name.trim().charAt(0).toUpperCase()

  return (
    <div className="app-layout">
      {isMenuOpen && <button className="mobile-nav-backdrop" aria-label="Close navigation menu" onClick={() => setIsMenuOpen(false)} />}
      <aside className={`sidebar${isMenuOpen ? ' sidebar-open' : ''}`}>
        <Brand onNavigate={navigate} />
        <div className="workspace-label">WORKSPACE</div>
        <nav className="side-nav" aria-label="Main navigation">
          {navigation.map((item) => (
            <a
              key={item.path}
              href={item.path}
              className={`nav-link${activePath === item.path ? ' active' : ''}`}
              aria-current={activePath === item.path ? 'page' : undefined}
              onClick={(event) => { event.preventDefault(); navigate(item.path) }}
            >
              <Icon name={item.icon} size={18} />
              <span>{item.label}</span>
              {item.path === '/challenges' && <span className="nav-pill">NEW</span>}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="side-note-icon"><Icon name="sparkles" size={18} /></div>
          <p className="side-note-title">Small steps, lasting change.</p>
          <p className="side-note-copy">Build skills that make a difference.</p>
          <button className="text-link" onClick={() => navigate('/')}>About the platform <Icon name="arrow" size={14} /></button>
        </div>
        <div className="profile">
          <div className="avatar">{initials}</div>
          <div className="profile-details"><div className="profile-name">{user.full_name}</div><div className="profile-caption">{user.email}</div></div>
          <button className="text-link logout-button" onClick={logout}>Log out</button>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <div className="topbar-leading">
            <button
              className="icon-button mobile-menu-button"
              aria-label={isMenuOpen ? 'Close navigation menu' : 'Open navigation menu'}
              aria-expanded={isMenuOpen}
              onClick={() => setIsMenuOpen((open) => !open)}
            >
              <Icon name="menu" size={18} />
            </button>
            <div className="breadcrumb"><span>ASCEND</span><span className="breadcrumb-slash">/</span><strong>{title}</strong></div>
          </div>
          <div className="topbar-right"><span className="today-label">YOUR GROWTH WORKSPACE</span><span className="avatar avatar-small">{initials}</span></div>
        </header>
        <div className="page-content">{children}</div>
        {logoutError && <div className="api-feedback api-feedback-error logout-feedback" role="alert">{logoutError}</div>}
        <footer className="app-footer"><span>Turn Goals Into Growth.</span><span>ASCEND <span className="footer-dot">·</span> Goals, plans, and progress are saved in your backend database</span></footer>
      </main>
    </div>
  )
}
