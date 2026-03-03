

from fastapi import APIRouter
from typing import List, Optional
from datetime import datetime, timezone
import json, os, glob

router = APIRouter()

# In-memory store for recent anomalies
# In production this would come from PostgreSQL
_recent_anomalies = []
MAX_ANOMALIES = 100


def get_anomalies_from_reports() -> List[dict]:
    """Extracts anomaly data from saved incident reports"""
    anomalies = []
    pattern   = os.path.join("reports", "*_raw.json")

    for filepath in glob.glob(pattern):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                # Extract primary anomaly from each report
                primary = data.get("primary_anomaly", {})
                if primary:
                    anomalies.append({
                        "incident_id":   data.get("incident_id"),
                        "timestamp":     data.get("timestamp"),
                        "service":       data.get("root_cause_service"),
                        "anomaly_type":  primary.get("type"),
                        "observed":      primary.get("observed_value"),
                        "expected":      primary.get("expected_value"),
                        "severity":      primary.get("severity"),
                    })
        except Exception:
            continue

    anomalies.sort(
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )
    return anomalies


@router.get("/live", summary="Live anomaly feed")
async def live_anomalies(limit: int = 20):
    """Returns most recent anomalies detected by ML models"""
    anomalies = get_anomalies_from_reports()[:limit]
    return {
        "total":     len(anomalies),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "anomalies": anomalies
    }


@router.get("/by-service/{service_name}",
            summary="Anomalies for a specific service")
async def anomalies_by_service(service_name: str):
    """Returns all anomalies for a specific service"""
    all_anomalies = get_anomalies_from_reports()
    filtered = [
        a for a in all_anomalies
        if a.get("service") == service_name
    ]
    return {
        "service":   service_name,
        "total":     len(filtered),
        "anomalies": filtered
    }


@router.get("/summary", summary="Anomaly summary statistics")
async def anomaly_summary():
    """Returns summary of all detected anomalies"""
    anomalies = get_anomalies_from_reports()

    if not anomalies:
        return {"message": "No anomalies detected yet"}

    type_counts = {}
    for a in anomalies:
        t = a.get("anomaly_type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1

    return {
        "total_anomalies": len(anomalies),
        "by_type":         type_counts,
        "latest":          anomalies[0] if anomalies else None,
    }