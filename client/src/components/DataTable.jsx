import StatusBadge from './StatusBadge'

// Columnas editables de la tabla (clave -> etiqueta).
const COLUMNS = [
  { key: 'brand', label: 'Marca', editable: false, width: 90 },
  { key: 'model_code', label: 'Cód. modelo', editable: true },
  { key: 'model_name', label: 'Modelo', editable: true },
  { key: 'vin', label: 'Nº VIN', editable: true },
  { key: 'interno', label: 'Interno', editable: false, width: 100 },
  { key: 'engine_number', label: 'Nº motor', editable: true },
  { key: 'year', label: 'Año', editable: true, width: 80 },
  { key: 'color_name', label: 'Color', editable: true },
  { key: 'color_code', label: 'Cód. color', editable: true, width: 100 },
  { key: 'certificate', label: 'Nº certificado', editable: true },
]

// Campos cuyo vacio se resalta (datos clave que deberian existir).
const CRITICAL = new Set(['vin', 'engine_number', 'color_code'])

export default function DataTable({ rows, selected, onToggle, onToggleAll, onUpdate, onDelete }) {
  const allSelected = rows.length > 0 && rows.every((r) => selected.has(r.id))

  function commit(row, key, value) {
    if (value === (row[key] ?? '')) return
    onUpdate(row.id, key, value)
  }

  return (
    <div className="table-wrap">
      <table className="data">
        <thead>
          <tr>
            <th style={{ width: 38 }}>
              <input type="checkbox" checked={allSelected} onChange={(e) => onToggleAll(e.target.checked)} />
            </th>
            <th>Archivo</th>
            {COLUMNS.map((c) => (
              <th key={c.key} style={c.width ? { width: c.width } : undefined}>{c.label}</th>
            ))}
            <th>Confianza</th>
            <th style={{ width: 50 }}></th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className={row.status === 'review' ? 'row--review' : ''}>
              <td>
                <input type="checkbox" checked={selected.has(row.id)} onChange={() => onToggle(row.id)} />
              </td>
              <td title={row.filename} style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {row.filename}
              </td>
              {COLUMNS.map((c) => (
                <td key={c.key}>
                  {c.editable ? (
                    <input
                      className={`cell-input ${CRITICAL.has(c.key) && !row[c.key] ? 'cell-input--missing' : ''}`}
                      defaultValue={row[c.key] ?? ''}
                      onBlur={(e) => commit(row, c.key, e.target.value)}
                      placeholder={CRITICAL.has(c.key) ? '⚠ falta' : ''}
                    />
                  ) : (
                    <span>{row[c.key] || '—'}</span>
                  )}
                </td>
              ))}
              <td><StatusBadge confidence={row.confidence} /></td>
              <td>
                <button className="btn btn--danger" title="Eliminar" onClick={() => onDelete(row.id)}>✕</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
