import { NavLink } from 'react-router-dom'
import bannerNeostar from '../assets/header-neostar.png'

// Header a todo el ancho con el banner de marca Neostar (I+D).
export default function Header() {
  return (
    <header className="header">
      <div className="header__bar">
        <NavLink to="/">
          <img src={bannerNeostar} alt="Neostar I+D - Innovación y Desarrollo" className="header__banner" />
        </NavLink>
        <nav className="header__nav">
          <NavLink to="/" end className={({ isActive }) => (isActive ? 'navlink navlink--active' : 'navlink')}>
            Facturas
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => (isActive ? 'navlink navlink--active' : 'navlink')}>
            Planillas
          </NavLink>
        </nav>
      </div>
    </header>
  )
}
