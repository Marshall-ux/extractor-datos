import { useEffect, useRef, useState } from 'react'
import { getModels, uploadModels } from '../services/api'

// Gestion de la planilla de modelos: muestra los codigos cargados y permite
// subir/actualizar el .xlsx. Se usa para resolver el codigo de modelo de marcas
// que no lo traen en la factura (Nissan, Honda) a partir del nombre del modelo.
export default function ModelManager() {
  const [models, setModels] = useState([])
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef(null)

  async function refresh() {
    try {
      setModels(await getModels())
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
      const res = await uploadModels(file)
      setMessage({ type: 'ok', text: `Planilla actualizada: ${res.loaded} modelos cargados.` })
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
      <div className="card__title">🚗 Planilla de modelos</div>
      <p className="card__hint">
        Códigos de modelo usados cuando la factura no lo trae explícito (Nissan, Honda).
        El sistema busca el nombre/descripción del modelo en esta planilla.
      </p>

      {message && <div className={`alert alert--${message.type === 'ok' ? 'ok' : 'error'}`}>{message.text}</div>}

      <div style={{ marginBottom: '1.2rem' }}>
        <span className="badge badge--success" style={{ fontSize: '0.85rem', padding: '0.5rem 1rem' }}>
          {models.length} modelos cargados
        </span>
      </div>

      {models.length > 0 && (
        <div className="table-wrap" style={{ marginBottom: '1.4rem', maxHeight: 280, overflowY: 'auto' }}>
          <table className="data">
            <thead>
              <tr>
                <th>Modelo (descripción)</th>
                <th style={{ width: 200 }}>Código</th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.id}>
                  <td>{m.model_name}</td>
                  <td>{m.model_code}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <input
        ref={fileRef}
        type="file"
        accept=".xlsx"
        style={{ display: 'none' }}
        onChange={(e) => handleUpload(e.target.files[0])}
      />
      <button className="btn btn--ghost" disabled={busy} onClick={() => fileRef.current?.click()}>
        {busy ? <span className="spinner" style={{ borderTopColor: 'var(--green)', borderColor: 'var(--green-soft)' }} /> : '⬆'}
        Subir planilla de modelos .xlsx
      </button>
    </div>
  )
}
