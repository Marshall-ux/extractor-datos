// Muestra el estado/confianza de una extraccion con color.
const LABELS = {
  high: { text: 'Alta', cls: 'badge--success' },
  medium: { text: 'Media', cls: 'badge--warning' },
  low: { text: 'Baja', cls: 'badge--danger' },
}

export default function StatusBadge({ confidence }) {
  const info = LABELS[confidence] || { text: confidence || '—', cls: 'badge--muted' }
  return <span className={`badge ${info.cls}`}>{info.text}</span>
}
