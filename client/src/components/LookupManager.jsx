import { useEffect, useRef, useState } from 'react'
import { getColors, uploadColors } from '../services/api'

// Gestion de planillas de colores: muestra cuantos colores hay cargados por
// "marca" (BYD / AUTOPAK) y permite subir/actualizar una planilla .xlsx.
export default function LookupManager() {
  const [counts, setCounts] = useState({})
  const [brand, setBrand] = useState('AUTOPAK')
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef(null)

  async function refresh() {
    try {
      const all = await getColors()
      const grouped = all.reduce((acc, c) => {
        const b = c.brand || 'SIN MARCA'
        acc[b] = (acc[b] || 0) + 1
        return acc
      }, {})
      setCounts(grouped)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  useEffect(() => { refresh() }, [])

  async function handleUpload(file) {
    if (!file) return
    setBusy(true)
    setMessage(null)
    try {
      const res = await uploadColors(file, brand)
      setMessage({ type: 'ok', text: `Planilla "${brand}" actualizada: ${res.loaded} colores cargados.` })
      await refresh()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setBusy(false)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div className="card">
      <div className="card__title">🎨 Planillas de colores</div>
      <p className="card__hint">
        Códigos usados para resolver el color de cada factura. BYD usa su propia planilla;
        el resto de las marcas usan la planilla AUTOPAK.
      </p>

      {message && <div className={`alert alert--${message.type === 'ok' ? 'ok' : 'error'}`}>{message.text}</div>}

      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1.4rem' }}>
        {Object.entries(counts).map(([b, n]) => (
          <div key={b} className="badge badge--success" style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}>
            {b}: {n} colores
          </div>
        ))}
        {Object.keys(counts).length === 0 && <span className="card__hint">No hay planillas cargadas.</span>}
      </div>

      <div className="field">
        <label>Actualizar planilla de</label>
        <select value={brand} onChange={(e) => setBrand(e.target.value)}>
          <option value="AUTOPAK">AUTOPAK (Nissan, Subaru, Suzuki, KIA, Honda)</option>
          <option value="BYD">BYD</option>
        </select>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".xlsx"
        style={{ display: 'none' }}
        onChange={(e) => handleUpload(e.target.files[0])}
      />
      <button className="btn btn--ghost" disabled={busy} onClick={() => fileRef.current?.click()}>
        {busy ? <span className="spinner" style={{ borderTopColor: 'var(--green)', borderColor: 'var(--green-soft)' }} /> : '⬆'}
        Subir planilla .xlsx
      </button>
    </div>
  )
}
