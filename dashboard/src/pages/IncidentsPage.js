import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [selected,  setSelected]  = useState(null);
  const [loading,   setLoading]   = useState(true);

  const load = () => {
    setLoading(true);
    api.getIncidents()
       .then(d => { setIncidents(d.incidents || []); setLoading(false); })
       .catch(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const sevLabel = { 1:'SEV-1 Critical', 2:'SEV-2 High',
                     3:'SEV-3 Medium',   4:'SEV-4 Low' };

  return (
    <div>
      <div className="page-header">
        <h1>🚨 Incidents</h1>
        <p>All detected incidents with RCA reports</p>
        <button className="refresh-btn" onClick={load}>🔄 Refresh</button>
      </div>

      {loading ? (
        <div className="loading">Loading incidents...</div>
      ) : incidents.length === 0 ? (
        <div className="empty">
          No incidents yet.<br/>
          Run the pipeline with --anomaly flag to generate incidents.
        </div>
      ) : (
        <div style={{display:'flex', gap:20}}>

          {/* Incident List */}
          <div style={{flex:1}}>
            <div className="table-card">
              <div className="table-card-header">
                {incidents.length} incidents found
              </div>
              <table>
                <thead>
                  <tr>
                    <th>ID</th><th>Service</th>
                    <th>Severity</th><th>Team</th>
                  </tr>
                </thead>
                <tbody>
                  {incidents.map(inc => (
                    <tr key={inc.incident_id}
                        onClick={() => setSelected(inc)}
                        style={{cursor:'pointer'}}>
                      <td style={{fontFamily:'monospace',
                                  color:'#63b3ed', fontSize:12}}>
                        {inc.incident_id}
                      </td>
                      <td>{inc.root_cause_service}</td>
                      <td>
                        <span className={`badge badge-${inc.severity}`}>
                          {sevLabel[inc.severity]}
                        </span>
                      </td>
                      <td>{inc.owning_team}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Incident Detail */}
          {selected && (
            <div style={{width:380}}>
              <div className="table-card">
                <div className="table-card-header">
                  Incident Detail
                  <button onClick={() => setSelected(null)}
                          style={{float:'right', background:'none',
                                  border:'none', color:'#718096',
                                  cursor:'pointer', fontSize:16}}>✕</button>
                </div>
                <div style={{padding:16}}>
                  <div style={{marginBottom:12}}>
                    <span className={`badge badge-${selected.severity}`}>
                      {sevLabel[selected.severity]}
                    </span>
                  </div>
                  <div style={{fontSize:13, lineHeight:1.8}}>
                    <div><b style={{color:'#a0aec0'}}>ID:</b> {selected.incident_id}</div>
                    <div><b style={{color:'#a0aec0'}}>Service:</b> {selected.root_cause_service}</div>
                    <div><b style={{color:'#a0aec0'}}>Team:</b> {selected.owning_team}</div>
                    <div style={{marginTop:10}}>
                      <b style={{color:'#a0aec0'}}>Root Cause:</b>
                      <p style={{color:'#cbd5e0', marginTop:4}}>
                        {selected.root_cause_summary}
                      </p>
                    </div>
                    <div style={{marginTop:10}}>
                      <b style={{color:'#a0aec0'}}>Top Fixes:</b>
                      <ul style={{color:'#cbd5e0', marginTop:4,
                                  paddingLeft:16}}>
                        {(selected.recommended_fixes || []).map((f,i) => (
                          <li key={i} style={{marginBottom:4}}>{f}</li>
                        ))}
                      </ul>
                    </div>
                    <div style={{marginTop:10}}>
                      <b style={{color:'#a0aec0'}}>Blast Radius:</b>
                      <p style={{color:'#fc8181', marginTop:4}}>
                        {selected.blast_radius?.directly_affected?.join(', ') || 'none'}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
