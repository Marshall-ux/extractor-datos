import { useState } from 'react'
import { exportExcel } from '../services/api'

// Descarga el Excel con las extracciones seleccionadas (o todas si no hay seleccion).
export default function ExportButton({ ids, disabled }) {
  const [busy, setBusy] = useState(false)

  async function handleExport() {
    setBusy(true)
    try {
      const { blob, filename } = await exportExcel(ids && ids.length ? ids : null)
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      alert(err.message)
    } finally {
      setBusy(false)
    }
  }

  const count = ids ? ids.length : 0
  return (
    <button className="btn btn--primary" onClick={handleExport} disabled={disabled || busy}>
      {busy ? <span className="spinner" /> : '⬇'}
      {count > 0 ? `Exportar ${count} a Excel` : 'Exportar todo a Excel'}
    </button>
  )
}
