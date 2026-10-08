import { useEffect, useMemo, useRef, useState } from 'react'
import Icon from './Icon'

// Editor de una planilla de busqueda dentro de la app (panel modal): muestra
// todas las filas como una tabla editable (mismo orden que la planilla),
// permite buscar, agregar y borrar filas, y guarda la planilla completa de una
// vez. Marca las celdas modificadas y las filas nuevas hasta guardar.
//
// planilla.columns: titulos de las columnas A y B.
// planilla.codeCol: indice (0/1) de la columna del codigo, para marcar repetidos.
// planilla.load(): [[a, b], ...]   planilla.save(rows): guarda [[a, b], ...]
let nextId = 1
const norm = (v) => v.trim().toUpperCase()

export default function PlanillaEditor({ planilla, onClose, onSaved }) {
  const [rows, setRows] = useState(null)
  // Valores guardados por id de fila, para detectar celdas modificadas,
  // filas nuevas y filas borradas.
  const [original, setOriginal] = useState(new Map())
  const [filter, setFilter] = useState('')
  const [message, setMessage] = useState(null)
  const [saving, setSaving] = useState(false)
  const [confirmClose, setConfirmClose] = useState(false)
  const focusId = useRef(null)

  async function load() {
    try {
      const loaded = (await planilla.load()).map(([a, b]) => ({ id: nextId++, a: a ?? '', b: b ?? '' }))
      setOriginal(new Map(loaded.map((r) => [r.id, r])))
      setRows(loaded)
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    }
  }

  useEffect(() => { load() }, [planilla.key])

  // Resumen de cambios respecto de lo guardado.
  const changes = useMemo(() => {
    if (!rows) return { edited: 0, added: 0, removed: 0, total: 0 }
    let edited = 0
    let added = 0
    rows.forEach((r) => {
      const o = original.get(r.id)
      if (!o) added += (r.a.trim() || r.b.trim()) ? 1 : 0
      else if (o.a.trim() !== r.a.trim() || o.b.trim() !== r.b.trim()) edited += 1
    })
    const kept = rows.filter((r) => original.has(r.id)).length
    const removed = original.size - kept
    return { edited, added, removed, total: edited + added + removed }
  }, [rows, original])
  const dirty = changes.total > 0

  // Codigos repetidos (se marcan pero no impiden guardar: la planilla AUTOPAK
  // original ya trae alguno).
  const duplicates = useMemo(() => {
    if (!rows) return new Set()
    const seen = new Map()
    rows.forEach((r) => {
      const code = norm(planilla.codeCol === 0 ? r.a : r.b)
      if (code) seen.set(code, (seen.get(code) || 0) + 1)
    })
    return new Set([...seen].filter(([, n]) => n > 1).map(([c]) => c))
  }, [rows, planilla.codeCol])

  const incomplete = rows ? rows.filter((r) => !r.a.trim() !== !r.b.trim()).length : 0

  const visible = useMemo(() => {
    if (!rows) return []
    const q = norm(filter)
    const numbered = rows.map((r, i) => ({ ...r, n: i + 1 }))
    if (!q) return numbered
    return numbered.filter((r) => norm(r.a).includes(q) || norm(r.b).includes(q))
  }, [rows, filter])

  // Bloquea el scroll de la pagina mientras el panel esta abierto.
  useEffect(() => {
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = prev }
  }, [])

  useEffect(() => {
    function onKey(e) {
      if (e.key === 'Escape') requestClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  })

  useEffect(() => {
    if (focusId.current === null) return
    const el = document.getElementById(`planilla-cell-${focusId.current}`)
    if (el) {
      el.focus()
      el.scrollIntoView({ block: 'nearest' })
    }
    focusId.current = null
  }, [rows])

  function updateCell(id, field, value) {
    setRows((prev) => prev.map((r) => (r.id === id ? { ...r, [field]: value } : r)))
  }

  function removeRow(id) {
    setRows((prev) => prev.filter((r) => r.id !== id))
  }

  function addRow() {
    const row = { id: nextId++, a: '', b: '' }
    setFilter('')
    focusId.current = row.id
    setRows((prev) => [...prev, row])
  }

  async function handleSave() {
    if (incomplete) {
      setMessage({ type: 'error', text: `Hay ${incomplete} fila(s) con una sola columna completa. Completalas o borralas antes de guardar.` })
      return
    }
    setSaving(true)
    setMessage(null)
    setConfirmClose(false)
    try {
      const res = await planilla.save(rows.map((r) => [r.a.trim(), r.b.trim()]))
      setMessage({ type: 'ok', text: `Cambios guardados: la planilla quedó con ${res.loaded} ${planilla.unit}.` })
      await load()
      onSaved()
    } catch (err) {
      setMessage({ type: 'error', text: err.message })
    } finally {
      setSaving(false)
    }
  }

  function handleDiscard() {
    setMessage(null)
    setConfirmClose(false)
    load()
  }

  function requestClose() {
    if (saving) return
    if (dirty) setConfirmClose(true)
    else onClose()
  }

  function cellClass(row, field, isCode) {
    const value = row[field]
    const o = original.get(row.id)
    const classes = ['cell-input']
    if (!value.trim() && (row.a.trim() || row.b.trim())) classes.push('cell-input--missing')
    else if (isCode && value.trim() && duplicates.has(norm(value))) classes.push('cell-input--duplicate')
    else if (o && o[field].trim() !== value.trim()) classes.push('cell-input--edited')
    return classes.join(' ')
  }

  const summary = [
    changes.edited && `${changes.edited} modificada${changes.edited > 1 ? 's' : ''}`,
    changes.added && `${changes.added} nueva${changes.added > 1 ? 's' : ''}`,
    changes.removed && `${changes.removed} borrada${changes.removed > 1 ? 's' : ''}`,
  ].filter(Boolean).join(' · ')

  return (
    <div className="modal" onMouseDown={(e) => { if (e.target === e.currentTarget) requestClose() }}>
      <div className="modal__panel" role="dialog" aria-modal="true" aria-label={`Editar planilla ${planilla.label} ${planilla.title}`}>
        <header className="modal__header">
          <div className="planilla__head" style={{ margin: 0 }}>
            <div className="planilla__icon"><Icon name={planilla.icon} size={22} /></div>
            <div>
              <div className="planilla__label">{planilla.label}</div>
              <div className="planilla__title">
                {planilla.title}
                {rows && <span className="modal__count">{rows.length} filas</span>}
              </div>
            </div>
          </div>
          <div className="modal__tools">
            <label className="search-bar">
              <Icon name="search" size={16} />
              <input
                type="search"
                placeholder="Buscar código o descripción…"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                autoFocus
              />
            </label>
            <button className="btn btn--icon btn--icon-ghost" onClick={requestClose} title="Cerrar (Esc)" aria-label="Cerrar">
              <Icon name="close" />
            </button>
          </div>
        </header>

        {(message || confirmClose) && (
          <div className="modal__notices">
            {message && <div className={`alert alert--${message.type === 'ok' ? 'ok' : 'error'}`}>{message.text}</div>}
            {confirmClose && (
              <div className="alert alert--warning modal__confirm">
                <span><strong>Tenés cambios sin guardar</strong> ({summary}). ¿Qué querés hacer?</span>
                <span className="toolbar__actions">
                  <button className="btn btn--ghost btn--sm" onClick={() => setConfirmClose(false)}>Seguir editando</button>
                  <button className="btn btn--ghost btn--sm" onClick={onClose}>Salir sin guardar</button>
                  <button className="btn btn--primary btn--sm" onClick={handleSave} disabled={saving}>Guardar y salir</button>
                </span>
              </div>
            )}
          </div>
        )}

        <div className="modal__body">
          {rows === null ? (
            <div className="empty"><span className="spinner spinner--dark spinner--lg" /></div>
          ) : (
            <table className="data sheet">
              <thead>
                <tr>
                  <th className="sheet__n">#</th>
                  <th>{planilla.columns[0]}</th>
                  <th>{planilla.columns[1]}</th>
                  <th className="sheet__del" />
                </tr>
              </thead>
              <tbody>
                {visible.map((r) => (
                  <tr key={r.id} className={original.has(r.id) ? '' : 'sheet__row--new'}>
                    <td className="sheet__n">{original.has(r.id) ? r.n : 'nueva'}</td>
                    <td>
                      <input
                        id={`planilla-cell-${r.id}`}
                        className={cellClass(r, 'a', planilla.codeCol === 0)}
                        value={r.a}
                        onChange={(e) => updateCell(r.id, 'a', e.target.value)}
                      />
                    </td>
                    <td>
                      <input
                        className={cellClass(r, 'b', planilla.codeCol === 1)}
                        value={r.b}
                        onChange={(e) => updateCell(r.id, 'b', e.target.value)}
                      />
                    </td>
                    <td className="sheet__del">
                      <button className="sheet__del-btn" title="Borrar fila" aria-label="Borrar fila" onClick={() => removeRow(r.id)}>
                        <Icon name="trash" size={15} />
                      </button>
                    </td>
                  </tr>
                ))}
                {visible.length === 0 && (
                  <tr><td colSpan={4} className="empty" style={{ padding: '2.5rem 1rem' }}>Ninguna fila coincide con “{filter}”.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>

        <footer className="modal__footer">
          <div className="modal__status">
            <button className="btn btn--outline btn--sm" onClick={addRow} disabled={saving || rows === null}>
              <Icon name="plus" size={15} />
              Agregar fila
            </button>
            {filter && rows && <span className="modal__meta">{visible.length} de {rows.length} filas</span>}
            {dirty && <span className="chip chip--change">{summary}</span>}
            {duplicates.size > 0 && <span className="chip chip--warning">{duplicates.size} código{duplicates.size > 1 ? 's' : ''} repetido{duplicates.size > 1 ? 's' : ''}</span>}
            {incomplete > 0 && <span className="chip chip--danger">{incomplete} fila{incomplete > 1 ? 's' : ''} incompleta{incomplete > 1 ? 's' : ''}</span>}
          </div>
          <div className="toolbar__actions">
            <button className="btn btn--ghost" onClick={handleDiscard} disabled={!dirty || saving}>
              <Icon name="undo" size={16} />
              Descartar
            </button>
            <button className="btn btn--primary" onClick={handleSave} disabled={!dirty || saving}>
              {saving ? <span className="spinner" /> : <Icon name="save" size={16} />}
              Guardar cambios
            </button>
          </div>
        </footer>
      </div>
    </div>
  )
}
