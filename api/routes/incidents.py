from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import json
import os
import glob

router = APIRouter()

# Reports are saved as JSON files in /reports/ folder
REPORTS_DIR = "reports"


def load_all_incidents() -> List[dict]:
    """
    Loads all incident JSON files from /reports/ directory.
    Returns them sorted by timestamp (newest first).
    """
    incidents = []

    # glob finds all files matching a pattern
    # **/*_raw.json matches any _raw.json file in reports/
    pattern = os.path.join(REPORTS_DIR, "*_raw.json")
    files   = glob.glob(pattern)

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                incidents.append(data)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")

    # Sort by timestamp — newest first
    incidents.sort(
        key=lambda x: x.get("timestamp", ""),
        reverse=True
    )
    return incidents


def load_report_text(incident_id: str) -> Optional[str]:
    """Loads the text report for a specific incident ID"""
    pattern = os.path.join(REPORTS_DIR, f"{incident_id}_*.txt")
    files   = glob.glob(pattern)

    if not files:
        return None

    with open(files[0], "r", encoding="utf-8") as f:
        return f.read()


# ── ENDPOINTS ─────────────────────────────────────────────

@router.get("/", summary="List all incidents")
async def list_incidents(
    limit: int  = 20,
    severity: Optional[int] = None,
    service:  Optional[str] = None,
):
    """
    Returns list of all incidents.

    Query parameters:
    - **limit**: max number of results (default 20)
    - **severity**: filter by SEV level (1-4)
    - **service**: filter by service name
    """
    incidents = load_all_incidents()

    # Apply filters
    if severity:
        incidents = [i for i in incidents
                     if i.get("severity") == severity]
    if service:
        incidents = [i for i in incidents
                     if i.get("root_cause_service") == service]

    # Apply limit
    incidents = incidents[:limit]

    return {
        "total":     len(incidents),
        "incidents": incidents
    }


@router.get("/recent", summary="Get 10 most recent incidents")
async def recent_incidents():
    """Returns the 10 most recent incidents"""
    incidents = load_all_incidents()[:10]
    return {
        "total":     len(incidents),
        "incidents": incidents
    }


@router.get("/stats", summary="Incident statistics")
async def incident_stats():
    """Returns summary statistics about all incidents"""
    incidents = load_all_incidents()

    if not incidents:
        return {"message": "No incidents recorded yet"}

    # Count by severity
    sev_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for inc in incidents:
        sev = inc.get("severity", 4)
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    # Count by service
    svc_counts = {}
    for inc in incidents:
        svc = inc.get("root_cause_service", "unknown")
        svc_counts[svc] = svc_counts.get(svc, 0) + 1

    return {
        "total_incidents":   len(incidents),
        "by_severity": {
            "SEV-1 (Critical)": sev_counts[1],
            "SEV-2 (High)":     sev_counts[2],
            "SEV-3 (Medium)":   sev_counts[3],
            "SEV-4 (Low)":      sev_counts[4],
        },
        "by_service":        svc_counts,
        "most_affected":     max(svc_counts, key=svc_counts.get)
                             if svc_counts else "none",
    }


@router.get("/{incident_id}", summary="Get incident by ID")
async def get_incident(incident_id: str):
    """
    Returns full details for a specific incident.

    Parameters:
    - **incident_id**: e.g. INC-20250302-142305
    """
    incidents = load_all_incidents()

    # Find matching incident
    match = next(
        (i for i in incidents
         if i.get("incident_id") == incident_id),
        None
    )

    if not match:
        raise HTTPException(
            status_code=404,
            detail=f"Incident {incident_id} not found"
        )

    # Also load the text report
    report_text = load_report_text(incident_id)

    return {
        "incident":    match,
        "report_text": report_text or "Report text not available"
    }