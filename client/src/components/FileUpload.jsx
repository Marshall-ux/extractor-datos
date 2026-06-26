import { useRef, useState } from 'react'

// Drag & drop o selector de PDFs. Llama onUpload(FileList) al backend.
export default function FileUpload({ onUpload, busy }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  function handleFiles(fileList) {
    const pdfs = Array.from(fileList).filter((f) => f.name.toLowerCase().endsWith('.pdf'))
    if (pdfs.length) onUpload(pdfs)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    if (busy) return
    handleFiles(e.dataTransfer.files)
  }

  return (
    <div
      className={`dropzone ${dragging ? 'dropzone--active' : ''}`}
      onClick={() => !busy && inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      role="button"
      tabIndex={0}
    >
      <div className="dropzone__icon">{busy ? '⏳' : '📄'}</div>
      <div className="dropzone__title">
        {busy ? 'Procesando facturas…' : 'Arrastrá tus facturas PDF acá'}
      </div>
      <div className="dropzone__hint">
        {busy ? 'Esperá un momento' : 'o hacé clic para seleccionar (podés subir varias a la vez)'}
      </div>
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        multiple
        onChange={(e) => handleFiles(e.target.files)}
      />
    </div>
  )
}
