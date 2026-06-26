export default function ProgressBar({ value, label }) {
  return (
    <div className="progress">
      {label && <span className="progress__label">{label}</span>}
      <div className="progress__track">
        <div className="progress__fill" style={{ width: `${Math.min(100, value)}%` }} />
      </div>
    </div>
  )
}
