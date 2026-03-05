import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function ServicesPage() {
  const [services,  setServices]  = useState([]);
  const [graph,     setGraph]     = useState(null);
  const [selected,  setSelected]  = useState(null);
  const [blast,     setBlast]     = useState(null);

  useEffect(() => {
    api.getServiceList().then(d => setServices(d.services || [])).catch(() => {});
    api.getServiceGraph().then(setGraph).catch(() => {});
  }, []);

  const handleBlastRadius = (svcName) => {
    setSelected(svcName);
    api.getBlastRadius(svcName).then(setBlast).catch(() => {});
  };

  const critClass = {
    critical: 'node-critical',
    high:     'node-high',
    medium:   'node-medium',
    low:      'node-low',
  };

  return (
    <div>
      <div className="page-header">
        <h1>🕸️ Service Dependency Graph</h1>
        <p>Click any service to see its blast radius</p>
      </div>

      {/* Visual Graph */}
      {graph && (
        <div className="graph-container">
          <div style={{marginBottom:12, fontSize:14, color:'#a0aec0'}}>
            {graph.total_services} services · {graph.total_dependencies} dependencies
          </div>
          <div>
            {graph.nodes.map(node => (
              <span
                key={node.id}
                className={`service-node ${critClass[node.criticality] || 'node-low'}`}
                onClick={() => handleBlastRadius(node.id)}
                style={{cursor:'pointer'}}
                title={`Team: ${node.team} | Tier: ${node.tier}`}
              >
                {node.label}
              </span>
            ))}
          </div>
          <div style={{marginTop:16, fontSize:12, color:'#718096'}}>
            🔴 Critical &nbsp; 🟠 High &nbsp; 🔵 Medium &nbsp; 🟢 Low
          </div>
        </div>
      )}

      {/* Blast Radius Result */}
      {selected && blast && (
        <div className="table-card" style={{marginBottom:20}}>
          <div className="table-card-header">
            💥 Blast Radius — {selected}
          </div>
          <div style={{padding:16, fontSize:13, lineHeight:2}}>
            <div>
              <b style={{color:'#a0aec0'}}>Criticality Score:</b>{' '}
              <span style={{color:'#fc8181', fontWeight:700}}>
                {blast.criticality_score}
              </span>
            </div>
            <div>
              <b style={{color:'#a0aec0'}}>Owning Team:</b>{' '}
              {blast.owning_team}
            </div>
            <div>
              <b style={{color:'#a0aec0'}}>Directly Affected:</b>{' '}
              <span style={{color:'#f6ad55'}}>
                {blast.directly_affected?.join(', ') || 'none'}
              </span>
            </div>
            <div>
              <b style={{color:'#a0aec0'}}>Indirectly Affected:</b>{' '}
              <span style={{color:'#fbd38d'}}>
                {blast.indirectly_affected?.join(', ') || 'none'}
              </span>
            </div>
            <div>
              <b style={{color:'#a0aec0'}}>Total Services Hit:</b>{' '}
              {blast.total_affected}
            </div>
          </div>
        </div>
      )}

      {/* Services Table */}
      <div className="table-card">
        <div className="table-card-header">All Services</div>
        <table>
          <thead>
            <tr>
              <th>Service</th><th>Team</th><th>Criticality</th>
              <th>Tier</th><th>Calls</th>
            </tr>
          </thead>
          <tbody>
            {services.map(svc => (
              <tr key={svc.name}
                  onClick={() => handleBlastRadius(svc.name)}
                  style={{cursor:'pointer'}}>
                <td style={{color:'#63b3ed'}}>{svc.name}</td>
                <td>{svc.team}</td>
                <td>
                  <span className={`badge badge-${
                    svc.criticality==='critical'?1:
                    svc.criticality==='high'?2:
                    svc.criticality==='medium'?3:4
                  }`}>
                    {svc.criticality}
                  </span>
                </td>
                <td>{svc.tier}</td>
                <td style={{fontSize:12, color:'#718096'}}>
                  {svc.dependencies?.join(', ') || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}