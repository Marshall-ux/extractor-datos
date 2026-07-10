import { useEffect, useState } from 'react'
import robot from '../assets/robot.png'
import FileUpload from '../components/FileUpload'
import DataTable from '../components/DataTable'
import ExportButton from '../components/ExportButton'
import ProgressBar from '../components/ProgressBar'
import {
  getExtractions, uploadFiles, updateExtraction, deleteExtraction, clearExtractions,
} from '../services/api'

export default function HomePage() {
  const [rows, setRows] = useState([])
  const [selected, setSelected] = useState(new Set())
  const [busy, setBusy] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState(null)

  async function load() {
    try {
      setRows(await getExtractions())
    } catch (err) {
      setError(err.message)
    }
  }

  useEffect(() => { load() }, [])

  async function handleUpload(files) {
    setBusy(true)
    setError(null)
    setProgress(20)
    try {
      const timer = setInterval(() => setProgress((p) => Math.min(p + 8, 90)), 300)
      await uploadFiles(files)
      clearInterval(timer)
      setProgress(100)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setTimeout(() => { setBusy(false); setProgress(0) }, 400)
    }
  }

  async function handleUpdate(id, field, value) {
    try {
      const updated = await updateExtraction(id, { [field]: value })
      setRows((rs) => rs.map((r) => (r.id === id ? updated : r)))
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(id) {
    if (!confirm('¿Eliminar esta extracción?')) return
    try {
      await deleteExtraction(id)
      setRows((rs) => rs.filter((r) => r.id !== id))
      setSelected((s) => { const n = new Set(s); n.delete(id); return n })
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleClearAll() {
    if (!confirm(
      `¿Limpiar todo el historial? Se eliminarán ${rows.length} factura(s) analizada(s). ` +
      'Esta acción no se puede deshacer.'
    )) return
    try {
      await clearExtractions()
      setRows([])
      setSelected(new Set())
    } catch (err) {
      setError(err.message)
    }
  }

  function toggle(id) {
    setSelected((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  }
  function toggleAll(checked) {
    setSelected(checked ? new Set(rows.map((r) => r.id)) : new Set())
  }

  const reviewCount = rows.filter((r) => r.status === 'review').length

  return (
    <>
      <section className="hero">
        <div className="hero__text">
          <span className="hero__eyebrow">🤖 Lector de Facturas I+D</span>
          <h1 className="hero__title">Extraé los datos de tus<br /><span>facturas de vehículos</span></h1>
          <p className="hero__subtitle">
            Subí las facturas PDF de las terminales y la app detecta la marca, extrae los datos
            y resuelve los códigos de color automáticamente. Revisá, editá y exportá a Excel.
          </p>
        </div>
        <img src={robot} alt="Asistente Neostar" className="hero__robot" />
      </section>

      {error && <div className="alert alert--error">{error}</div>}

      <div className="card">
        <FileUpload onUpload={handleUpload} busy={busy} />
        {busy && <ProgressBar value={progress} label="Procesando facturas…" />}
      </div>

      <div className="card">
        <div className="toolbar">
          <div>
            <div className="card__title">Facturas procesadas</div>
            <div className="toolbar__info">
              {rows.length} extracción(es)
              {reviewCount > 0 && <> · <span style={{ color: 'var(--warning)' }}>{reviewCount} para revisar</span></>}
            </div>
          </div>
          <div className="toolbar__actions">
            <button
              className="btn btn--ghost"
              onClick={handleClearAll}
              disabled={rows.length === 0}
              title="Eliminar todas las facturas del historial"
            >
              🗑 Limpiar historial
            </button>
            <ExportButton ids={[...selected]} disabled={rows.length === 0} />
          </div>
        </div>

        {rows.length === 0 ? (
          <div className="empty">
            <div className="empty__icon">📭</div>
            <p>Todavía no hay facturas. Subí tus PDFs para empezar.</p>
          </div>
        ) : (
          <DataTable
            rows={rows}
            selected={selected}
            onToggle={toggle}
            onToggleAll={toggleAll}
            onUpdate={handleUpdate}
            onDelete={handleDelete}
          />
        )}
      </div>
    </>
  )
}
