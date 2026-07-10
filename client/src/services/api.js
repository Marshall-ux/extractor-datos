// Cliente de la API REST. En dev, Vite hace proxy de /api -> Flask:5000.
// En produccion, Nginx hace el proxy.

const BASE = '/api'

async function handle(res) {
  if (!res.ok) {
    let message = `Error ${res.status}`
    try {
      const data = await res.json()
      message = data.error || message
    } catch {
      // respuesta sin JSON
    }
    throw new Error(message)
  }
  return res.json()
}

export async function uploadFiles(files) {
  const form = new FormData()
  for (const file of files) {
    form.append('files', file)
  }
  const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form })
  return handle(res)
}

export async function getExtractions() {
  return handle(await fetch(`${BASE}/extractions`))
}

export async function updateExtraction(id, data) {
  const res = await fetch(`${BASE}/extractions/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return handle(res)
}

export async function deleteExtraction(id) {
  const res = await fetch(`${BASE}/extractions/${id}`, { method: 'DELETE' })
  return handle(res)
}

export async function clearExtractions() {
  const res = await fetch(`${BASE}/extractions`, { method: 'DELETE' })
  return handle(res)
}

export async function exportExcel(ids) {
  const res = await fetch(`${BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ids: ids || null }),
  })
  if (!res.ok) {
    throw new Error('No se pudo generar el Excel')
  }
  const blob = await res.blob()
  const disposition = res.headers.get('Content-Disposition') || ''
  const match = disposition.match(/filename="?([^"]+)"?/)
  const filename = match ? match[1] : 'facturas.xlsx'
  return { blob, filename }
}

export async function getColors(brand) {
  const url = brand ? `${BASE}/lookup-tables/colors?brand=${brand}` : `${BASE}/lookup-tables/colors`
  return handle(await fetch(url))
}

export async function uploadColors(file, brand) {
  const form = new FormData()
  form.append('file', file)
  if (brand) form.append('brand', brand)
  const res = await fetch(`${BASE}/lookup-tables/colors`, { method: 'POST', body: form })
  return handle(res)
}

export async function getModels(brand) {
  const url = brand ? `${BASE}/lookup-tables/models?brand=${brand}` : `${BASE}/lookup-tables/models`
  return handle(await fetch(url))
}

export async function uploadModels(file, brand) {
  const form = new FormData()
  form.append('file', file)
  if (brand) form.append('brand', brand)
  const res = await fetch(`${BASE}/lookup-tables/models`, { method: 'POST', body: form })
  return handle(res)
}
