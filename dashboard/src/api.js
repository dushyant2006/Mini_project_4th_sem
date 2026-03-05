// src/api.js
// PURPOSE: All API calls to FastAPI backend in one place
// ============================================================

const BASE = "http://localhost:8000";

export const api = {
  // Incidents
  getIncidents:      () => fetch(`${BASE}/incidents/`).then(r => r.json()),
  getRecentIncidents:() => fetch(`${BASE}/incidents/recent`).then(r => r.json()),
  getIncidentStats:  () => fetch(`${BASE}/incidents/stats`).then(r => r.json()),
  getIncident:       (id) => fetch(`${BASE}/incidents/${id}`).then(r => r.json()),
  getKnowledgeBase:  () => fetch(`${BASE}/incidents/knowledge-base`).then(r => r.json()),

  // Anomalies
  getLiveAnomalies:  () => fetch(`${BASE}/anomalies/live`).then(r => r.json()),
  getAnomalySummary: () => fetch(`${BASE}/anomalies/summary`).then(r => r.json()),

  // Services
  getServiceGraph:   () => fetch(`${BASE}/services/graph`).then(r => r.json()),
  getServiceList:    () => fetch(`${BASE}/services/list`).then(r => r.json()),
  getBlastRadius:    (svc) => fetch(`${BASE}/services/${svc}/blast-radius`).then(r => r.json()),

  // Health
  getHealth:         () => fetch(`${BASE}/health`).then(r => r.json()),
};