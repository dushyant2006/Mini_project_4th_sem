// ============================================================
// src/App.js
// PURPOSE: Main app with routing between dashboard pages
// ============================================================

import React from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import IncidentsPage   from './pages/IncidentsPage';
import AnomaliesPage   from './pages/AnomaliesPage';
import ServicesPage    from './pages/ServicesPage';
import OverviewPage    from './pages/OverviewPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">

        {/* ── Sidebar Navigation ── */}
        <nav className="sidebar">
          <div className="sidebar-header">
            <span className="logo">⚡</span>
            <div>
              <div className="logo-title">Project 71</div>
              <div className="logo-sub">AIOps Platform</div>
            </div>
          </div>

          <ul className="nav-links">
            <li>
              <NavLink to="/" end className={({isActive}) => isActive ? 'active' : ''}>
                📊 Overview
              </NavLink>
            </li>
            <li>
              <NavLink to="/incidents" className={({isActive}) => isActive ? 'active' : ''}>
                🚨 Incidents
              </NavLink>
            </li>
            <li>
              <NavLink to="/anomalies" className={({isActive}) => isActive ? 'active' : ''}>
                🔍 Anomalies
              </NavLink>
            </li>
            <li>
              <NavLink to="/services" className={({isActive}) => isActive ? 'active' : ''}>
                🕸️ Services
              </NavLink>
            </li>
          </ul>

          <div className="sidebar-footer">
            <a href="http://localhost:8000/docs"
               target="_blank" rel="noreferrer">
              📖 API Docs
            </a>
          </div>
        </nav>

        {/* ── Main Content ── */}
        <main className="main-content">
          <Routes>
            <Route path="/"          element={<OverviewPage />} />
            <Route path="/incidents" element={<IncidentsPage />} />
            <Route path="/anomalies" element={<AnomaliesPage />} />
            <Route path="/services"  element={<ServicesPage />} />
          </Routes>
        </main>

      </div>
    </Router>
  );
}

export default App;