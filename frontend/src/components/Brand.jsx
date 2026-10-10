export function Brand({ onNavigate }) {
  return (
    <a
      className="brand"
      href="/dashboard"
      onClick={(event) => {
        event.preventDefault()
        onNavigate?.('/dashboard')
      }}
      aria-label="ASCEND — Turn Goals Into Growth"
    >
      <span className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none">
          <path d="M4 17.5 10 11.5l3.5 3.5L20 8.5" />
          <path d="M14.5 8.5H20v5.5" />
        </svg>
      </span>
      <span className="brand-copy">
        <span className="brand-name">ASCEND</span>
        <span className="brand-tagline">Turn Goals Into Growth.</span>
      </span>
    </a>
  )
}
