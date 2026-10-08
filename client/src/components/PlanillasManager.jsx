import { useEffect, useRef, useState } from 'react'
import {
  downloadLookupTable, getColors, getModels, saveColors, saveModels,
  uploadColors, uploadModels,
} from '../services/api'
import Icon from './Icon'
import PlanillaEditor from './PlanillaEditor'

// Las tres planillas de busqueda que usa la extraccion. Cada una se puede
// editar directamente en la app, o descargar tal como esta cargada, editar en
// Excel y volver a subir.
const PLANILLAS = [
  {
    key: 'autopak',
    icon: 'palette',
    label: 'Colores',
    title: 'AUTOPAK',
    hint: 'Nissan, Subaru, Suzuki, KIA y Honda.',
    unit: 'colores',
    columns: ['Código', 'Descripción'],
    codeCol: 0,
    download: 'colors/download?brand=AUTOPAK',
    load: async () => (await getColors('AUTOPAK')).map((c) => [c.color_code, c.color_name]),
    save: (rows) => saveColors('AUTOPAK', rows),
    upload: (file) => uploadColors(file, 'AUTOPAK'),
  },
  {
    key: 'byd',
    icon: 'palette',
    label: 'Colores',
    title: 'BYD',
    hint: 'Combinaciones exterior / interior de BYD.',
    unit: 'colores',
    columns: ['Código', 'Descripción'],
    codeCol: 0,
    download: 'colors/download?brand=BYD',
    load: async () => (await getColors('BYD')).map((c) => [c.color_code, c.color_name]),
    save: (rows) => saveColors('BYD', rows),
    upload: (file) => uploadColors(file, 'BYD'),
  },
  {
    key: 'nissan',
    icon: 'car',
    label: 'Modelos',
    title: 'Nissan',
    hint: 'Código de modelo cuando la factura no lo trae.',
    unit: 'modelos',
    columns: ['Modelo', 'Código'],
    codeCol: 1,
    download: 'models/download',
    load: async () => (await getModels()).map((m) => [m.model_name, m.model_code]),
    save: (rows) => saveModels(rows),
    upload: (file) => uploadModels(file),
  },
]

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  a.remove()
  URL.revokeObjectURL(url)
}

function Planilla({ planilla, version, onEdit, onUploaded }) {
  const [count, setCount] = useState(null)
  const [message, setMessage] = useState(null)
  const [busy, setBusy] = useState(null) // 'download' | 'upload' | null
  const fileRef = useRef(null)

  async function refresh() {
    try {
      setCount((await planilla.load()).length)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  useEffect(() => { refresh() }, [version])

  async function handleDownload() {
    setBusy('download')
    setMessage(null)
    try {
      const { blob, filename } = await downloadLookupTable(planilla.download)
      saveBlob(blob, filename)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setBusy(null)
    }
  }

  async function handleUpload(file) {
    if (!file) return
    setBusy('upload')
    setMessage(null)
    try {
      const res = await planilla.upload(file)
      setMessage({ type: 'ok', text: `Planilla actualizada: ${res.loaded} ${planilla.unit}.` })
      await refresh()
      onUploaded()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setBusy(null)
      if (fileRef.current) fileRef.current.value = ''
    }
  }

  return (
    <div className="planilla">
      <div className="planilla__head">
        <div className="planilla__icon"><Icon name={planilla.icon} size={22} /></div>
        <div>
          <div className="planilla__label">{planilla.label}</div>
          <div className="planilla__title">{planilla.title}</div>
        </div>
      </div>
      <p className="planilla__hint">{planilla.hint}</p>

      <div className="planilla__stat">
        <span className="planilla__count">{count === null ? '–' : count.toLocaleString('es-AR')}</span>
        <span className="planilla__unit">{planilla.unit} cargados</span>
      </div>

      {message && (
        <div className={`planilla__msg planilla__msg--${message.type}`}>{message.text}</div>
      )}

      <div className="planilla__actions">
        <button className="btn btn--primary planilla__edit" disabled={busy !== null || count === null} onClick={onEdit}>
          <Icon name="edit" size={16} />
          Ver y editar
        </button>
        <button
          className="btn btn--icon"
          title="Descargar planilla (.xlsx)"
          aria-label="Descargar planilla"
          disabled={busy !== null || !count}
          onClick={handleDownload}
        >
          {busy === 'download' ? <span className="spinner spinner--dark" /> : <Icon name="download" />}
        </button>
        <button
          className="btn btn--icon"
          title="Reemplazar con un archivo .xlsx"
          aria-label="Subir planilla"
          disabled={busy !== null}
          onClick={() => fileRef.current?.click()}
        >
          {busy === 'upload' ? <span className="spinner spinner--dark" /> : <Icon name="upload" />}
        </button>
      </div>

      <input
        ref={fileRef}
        type="file"
        accept=".xlsx"
        style={{ display: 'none' }}
        onChange={(e) => handleUpload(e.target.files[0])}
      />
    </div>
  )
}

export default function PlanillasManager() {
  const [editingKey, setEditingKey] = useState(null)
  // Se incrementa al guardar/subir para que las tarjetas refresquen su conteo.
  const [version, setVersion] = useState(0)
  const bump = () => setVersion((v) => v + 1)

  const editing = PLANILLAS.find((p) => p.key === editingKey)

  return (
    <>
      <div className="planillas">
        {PLANILLAS.map((p) => (
          <Planilla
            key={p.key}
            planilla={p}
            version={version}
            onEdit={() => setEditingKey(p.key)}
            onUploaded={bump}
          />
        ))}
      </div>

      <p className="planillas__note">
        Los cambios que guardes reemplazan a la planilla anterior y se aplican en la próxima extracción.
        Con <Icon name="download" size={14} /> la descargás en Excel y con <Icon name="upload" size={14} /> subís
        una planilla completa.
      </p>

      {editing && (
        <PlanillaEditor
          key={editing.key}
          planilla={editing}
          onClose={() => setEditingKey(null)}
          onSaved={bump}
        />
      )}
    </>
  )
}
