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

export function AppShell({ activePath, title, onNavigate, children }) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)

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
          <div className="avatar">Y</div>
          <div><div className="profile-name">Your workspace</div><div className="profile-caption">Personal account</div></div>
          <span className="online-dot" aria-label="Active" />
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
          <div className="topbar-right"><span className="today-label">YOUR GROWTH WORKSPACE</span><span className="avatar avatar-small">Y</span></div>
        </header>
        <div className="page-content">{children}</div>
        <footer className="app-footer"><span>Turn Goals Into Growth.</span><span>ASCEND <span className="footer-dot">·</span> Goals, plans, and progress are saved in your backend database</span></footer>
      </main>
    </div>
  )
}
