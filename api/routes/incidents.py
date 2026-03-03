
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
import json
import os
import glob
import sys

router = APIRouter()

REPORTS_DIR = "reports"


def load_all_incidents() -> List[dict]:
    """Loads all incident JSON files from /reports/ directory"""
    incidents = []
    pattern   = os.path.join(REPORTS_DIR, "*_raw.json")
    files     = glob.glob(pattern)

    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                incidents.append(data)
        except Exception as e:
            print(f"Error loading {filepath}: {e}")

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
    limit:    int          = 20,
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

    if severity:
        incidents = [i for i in incidents
                     if i.get("severity") == severity]
    if service:
        incidents = [i for i in incidents
                     if i.get("root_cause_service") == service]

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

    sev_counts = {1: 0, 2: 0, 3: 0, 4: 0}
    for inc in incidents:
        sev = inc.get("severity", 4)
        sev_counts[sev] = sev_counts.get(sev, 0) + 1

    svc_counts = {}
    for inc in incidents:
        svc = inc.get("root_cause_service", "unknown")
        svc_counts[svc] = svc_counts.get(svc, 0) + 1

    return {
        "total_incidents": len(incidents),
        "by_severity": {
            "SEV-1 (Critical)": sev_counts[1],
            "SEV-2 (High)":     sev_counts[2],
            "SEV-3 (Medium)":   sev_counts[3],
            "SEV-4 (Low)":      sev_counts[4],
        },
        "by_service":  svc_counts,
        "most_affected": max(svc_counts, key=svc_counts.get)
                         if svc_counts else "none",
    }


@router.get("/knowledge-base", summary="RAG knowledge base stats")
async def knowledge_base_stats():
    """
    Returns statistics about the RAG incident knowledge base.
    Shows how many incidents the system has learned from.
    """
    ROOT = os.path.dirname(os.path.dirname(
           os.path.dirname(os.path.abspath(__file__))))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)

    try:
        from rca.rag_retriever import RAGRetriever
        rag   = RAGRetriever()
        stats = rag.get_stats()

        return {
            "message":           "RAG Knowledge Base Statistics",
            "seed_incidents":    stats["seed_incidents"],
            "learned_incidents": stats["learned_incidents"],
            "total_incidents":   stats["total"],
            "knowledge_base_path": "data/incident_knowledge_base.json",
            "description": (
                "The system automatically learns from every new incident. "
                f"Started with {stats['seed_incidents']} seed incidents, "
                f"has learned {stats['learned_incidents']} more from live operation."
            )
        }
    except Exception as e:
        return {
            "message": "Knowledge base not yet initialized",
            "error":   str(e),
            "tip":     "Run the full pipeline to generate incidents first"
        }


@router.get("/{incident_id}", summary="Get incident by ID")
async def get_incident(incident_id: str):
    """
    Returns full details for a specific incident.

    Parameters:
    - **incident_id**: e.g. INC-20250302-142305
    """
    incidents = load_all_incidents()

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

    report_text = load_report_text(incident_id)

    return {
        "incident":    match,
        "report_text": report_text or "Report text not available"
    }