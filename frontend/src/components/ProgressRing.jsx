export function ProgressRing({ value, size = 62 }) {
  const safeValue = Math.min(100, Math.max(0, value))
  const radius = 25
  const circumference = 2 * Math.PI * radius
  return (
    <div className="progress-ring" style={{ width: size, height: size }}>
      <svg viewBox="0 0 60 60" aria-label={`${safeValue}% complete`}>
        <circle className="ring-track" cx="30" cy="30" r={radius} />
        <circle className="ring-value" cx="30" cy="30" r={radius} strokeDasharray={circumference} strokeDashoffset={circumference * (1 - safeValue / 100)} />
      </svg>
      <span>{safeValue}%</span>
    </div>
  )
}
