import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function AnomaliesPage() {
  const [anomalies, setAnomalies] = useState([]);
  const [summary,   setSummary]   = useState(null);
  const [loading,   setLoading]   = useState(true);

  const load = () => {
    setLoading(true);
    api.getLiveAnomalies()
       .then(d => { setAnomalies(d.anomalies || []); setLoading(false); })
       .catch(() => setLoading(false));
    api.getAnomalySummary().then(setSummary).catch(() => {});
  };

  useEffect(() => {
    load();
    // Auto-refresh every 10 seconds
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, []);

  const sevColor = { 1:'#fc8181', 2:'#f6ad55', 3:'#fbd38d', 4:'#63b3ed' };

  return (
    <div>
      <div className="page-header">
        <h1>🔍 Live Anomaly Feed</h1>
        <p>Real-time anomalies detected by ML models — auto-refreshes every 10s</p>
        <button className="refresh-btn" onClick={load}>🔄 Refresh</button>
      </div>

      {/* Summary */}
      {summary && summary.total_anomalies > 0 && (
        <div className="stats-grid" style={{gridTemplateColumns:'repeat(3,1fr)'}}>
          <div className="stat-card">
            <div className="stat-label">Total Anomalies</div>
            <div className="stat-value">{summary.total_anomalies}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Latest Service</div>
            <div className="stat-value" style={{fontSize:18}}>
              {summary.latest?.service || '—'}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Latest Type</div>
            <div className="stat-value" style={{fontSize:14}}>
              {summary.latest?.anomaly_type?.replace(/_/g,' ') || '—'}
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div className="loading">Loading anomalies...</div>
      ) : anomalies.length === 0 ? (
        <div className="empty">
          No anomalies detected yet.<br/>
          Run: <code style={{color:'#63b3ed'}}>
            python data/simulate_telemetry.py --anomaly payment-service
          </code>
        </div>
      ) : (
        <div className="table-card">
          <div className="table-card-header">
            {anomalies.length} anomalies detected
          </div>
          <table>
            <thead>
              <tr>
                <th>Time</th><th>Service</th><th>Type</th>
                <th>Observed</th><th>Expected</th><th>Severity</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a, i) => (
                <tr key={i}>
                  <td style={{fontSize:11, color:'#718096'}}>
                    {a.timestamp ? new Date(a.timestamp)
                      .toLocaleTimeString() : '—'}
                  </td>
                  <td style={{color:'#63b3ed'}}>{a.service}</td>
                  <td style={{fontSize:12}}>
                    {a.anomaly_type?.replace(/_/g,' ')}
                  </td>
                  <td style={{color: sevColor[a.severity] || '#fff',
                              fontWeight:600}}>
                    {a.observed}
                  </td>
                  <td style={{color:'#718096'}}>{a.expected}</td>
                  <td>
                    <span className={`badge badge-${a.severity}`}>
                      SEV-{a.severity}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}