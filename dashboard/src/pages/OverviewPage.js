import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function OverviewPage() {
  const [stats,  setStats]  = useState(null);
  const [health, setHealth] = useState(null);
  const [kb,     setKb]     = useState(null);
  const [recent, setRecent] = useState([]);

  useEffect(() => {
    api.getIncidentStats().then(setStats).catch(() => {});
    api.getHealth().then(setHealth).catch(() => {});
    api.getKnowledgeBase().then(setKb).catch(() => {});
    api.getRecentIncidents().then(d => setRecent(d.incidents || [])).catch(() => {});
  }, []);

  const sevLabel = { 1:'SEV-1', 2:'SEV-2', 3:'SEV-3', 4:'SEV-4' };

  return (
    <div>
      <div className="page-header">
        <h1>📊 Platform Overview</h1>
        <p>Real-time AIOps monitoring dashboard</p>
      </div>

      {/* Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total Incidents</div>
          <div className="stat-value">{stats?.total_incidents ?? '—'}</div>
          <div className="stat-sub">all time</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">SEV-1 Critical</div>
          <div className="stat-value" style={{color:'#fc8181'}}>
            {stats?.by_severity?.['SEV-1 (Critical)'] ?? '—'}
          </div>
          <div className="stat-sub">requires immediate action</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">API Status</div>
          <div className="stat-value" style={{color:'#68d391', fontSize:22}}>
            {health?.status === 'healthy' ? '✅ Healthy' : '❌ Down'}
          </div>
          <div className="stat-sub">FastAPI backend</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">KB Incidents</div>
          <div className="stat-value" style={{color:'#63b3ed'}}>
            {kb?.total_incidents ?? '—'}
          </div>
          <div className="stat-sub">{kb?.learned_incidents ?? 0} auto-learned</div>
        </div>
      </div>

      {/* Recent Incidents */}
      <div className="table-card">
        <div className="table-card-header">🚨 Recent Incidents</div>
        {recent.length === 0 ? (
          <div className="empty">No incidents yet — run the pipeline to generate some!</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th><th>Service</th><th>Severity</th>
                <th>Root Cause</th><th>Team</th>
              </tr>
            </thead>
            <tbody>
              {recent.slice(0,8).map(inc => (
                <tr key={inc.incident_id}>
                  <td style={{fontFamily:'monospace', color:'#63b3ed'}}>
                    {inc.incident_id}
                  </td>
                  <td>{inc.root_cause_service}</td>
                  <td>
                    <span className={`badge badge-${inc.severity}`}>
                      {sevLabel[inc.severity]}
                    </span>
                  </td>
                  <td style={{maxWidth:300, overflow:'hidden',
                              textOverflow:'ellipsis', whiteSpace:'nowrap'}}>
                    {inc.root_cause_summary}
                  </td>
                  <td>{inc.owning_team}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}