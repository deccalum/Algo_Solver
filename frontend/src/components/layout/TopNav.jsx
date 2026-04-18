import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Icon } from '../shared/Icon';
import '../../styles/top-nav.css';

export function TopNav() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
      <header className="top-nav">
        <div className="top-nav__left">
          <NavLink to="/" className="top-nav__logo">
            GRIP Solve
          </NavLink>
          <nav className="top-nav__desktop-nav">
            <NavLink to="/generation" className={({ isActive }) => `top-nav__link${isActive ? ' top-nav__link--active' : ''}`}>
              GENERATION
            </NavLink>
            <NavLink to="/solver" className={({ isActive }) => `top-nav__link${isActive ? ' top-nav__link--active' : ''}`}>
              SOLVER
            </NavLink>
            <NavLink to="/database" className={({ isActive }) => `top-nav__link${isActive ? ' top-nav__link--active' : ''}`}>
              DATABASE
            </NavLink>
            <NavLink to="/simulation" className={({ isActive }) => `top-nav__link${isActive ? ' top-nav__link--active' : ''}`}>
              SIMULATION
            </NavLink>
          </nav>
        </div>
        <div className="top-nav__right">
          <button className="top-nav__icon-btn">
            <Icon name="settings" />
          </button>
          <button className="top-nav__icon-btn">
            <Icon name="person" />
          </button>
          <button
            className="top-nav__menu-btn"
            onClick={() => setMenuOpen(v => !v)}
            aria-label="Toggle navigation"
          >
            <Icon name={menuOpen ? 'close' : 'menu'} />
          </button>
        </div>
      </header>
      {menuOpen && (
        <div className="top-nav__mobile-menu">
          <nav className="top-nav__mobile-nav">
            <NavLink to="/generation" className={({ isActive }) => `top-nav__mobile-link${isActive ? ' top-nav__mobile-link--active' : ''}`} onClick={() => setMenuOpen(false)}>
              GENERATION
            </NavLink>
            <NavLink to="/solver" className={({ isActive }) => `top-nav__mobile-link${isActive ? ' top-nav__mobile-link--active' : ''}`} onClick={() => setMenuOpen(false)}>
              SOLVER
            </NavLink>
            <NavLink to="/database" className={({ isActive }) => `top-nav__mobile-link${isActive ? ' top-nav__mobile-link--active' : ''}`} onClick={() => setMenuOpen(false)}>
              DATABASE
            </NavLink>
            <NavLink to="/simulation" className={({ isActive }) => `top-nav__mobile-link${isActive ? ' top-nav__mobile-link--active' : ''}`} onClick={() => setMenuOpen(false)}>
              SIMULATION
            </NavLink>
          </nav>
        </div>
      )}
    </>
  );
}
