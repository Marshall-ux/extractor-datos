import LookupManager from '../components/LookupManager'
import ModelManager from '../components/ModelManager'

export default function SettingsPage() {
  return (
    <>
      <section className="hero" style={{ marginBottom: '1.5rem' }}>
        <div className="hero__text">
          <span className="hero__eyebrow">⚙️ Configuración</span>
          <h1 className="hero__title" style={{ fontSize: '2.2rem' }}>Planillas de búsqueda</h1>
          <p className="hero__subtitle">
            Mantené actualizados los códigos de color que usa la extracción automática.
          </p>
        </div>
      </section>

      <LookupManager />
      <ModelManager />
    </>
  )
}
