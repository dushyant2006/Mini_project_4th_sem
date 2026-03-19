# ============================================================
# api/routes/incidents.py
# PURPOSE: Incident endpoints with auth, rate limiting,
#          proper error handling
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional
from slowapi import Limiter
from slowapi.util import get_remote_address
import json, os, glob, sys

from api.auth import get_current_user, require_auth, require_permission

router  = APIRouter()
limiter = Limiter(key_func=get_remote_address)

REPORTS_DIR = "reports"


def load_all_incidents() -> List[dict]:
    incidents = []
    pattern   = os.path.join(REPORTS_DIR, "*_raw.json")
    for filepath in glob.glob(pattern):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                incidents.append(json.load(f))
        except Exception as e:
            print(f"⚠️ Error loading {filepath}: {e}")
    return sorted(incidents,
                  key=lambda x: x.get("timestamp", ""),
                  reverse=True)


def load_report_text(incident_id: str) -> Optional[str]:
    pattern = os.path.join(REPORTS_DIR, f"{incident_id}_*.txt")
    files   = glob.glob(pattern)
    if not files:
        return None
    try:
        with open(files[0], "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


@router.get("/", summary="List all incidents")
@limiter.limit("100/minute")
async def list_incidents(
    request:      Request,
    limit:        int            = 20,
    severity:     Optional[int]  = None,
    service:      Optional[str]  = None,
    current_user: Optional[dict] = Depends(get_current_user),
):
    """
    Returns list of all incidents.
    - **limit**: max results (1-100, default 20)
    - **severity**: filter by 1-4
    - **service**: filter by service name
    """
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(
                status_code=400,
                detail="Limit must be between 1 and 100"
            )
        if severity is not None and severity not in [1, 2, 3, 4]:
            raise HTTPException(
                status_code=400,
                detail="Severity must be 1 (Critical), 2 (High), 3 (Medium), or 4 (Low)"
            )

        incidents = load_all_incidents()

        if severity is not None:
            incidents = [i for i in incidents
                         if i.get("severity") == severity]
        if service:
            incidents = [i for i in incidents
                         if i.get("root_cause_service") == service]

        return {
            "total":     len(incidents),
            "incidents": incidents[:limit],
            "viewer":    current_user["username"] if current_user else "anonymous"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve incidents: {str(e)}"
        )


@router.get("/recent", summary="Get 10 most recent incidents")
@limiter.limit("100/minute")
async def recent_incidents(
    request:      Request,
    current_user: Optional[dict] = Depends(get_current_user),
):
    try:
        incidents = load_all_incidents()[:10]
        return {"total": len(incidents), "incidents": incidents}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve recent incidents: {str(e)}"
        )


@router.get("/stats", summary="Incident statistics")
@limiter.limit("60/minute")
async def incident_stats(
    request:      Request,
    current_user: Optional[dict] = Depends(get_current_user),
):
    try:
        incidents = load_all_incidents()
        if not incidents:
            return {
                "message": "No incidents recorded yet",
                "tip":     "Run: python data/simulate_telemetry.py --anomaly payment-service"
            }

        sev_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        svc_counts = {}

        for inc in incidents:
            sev = inc.get("severity", 4)
            sev_counts[sev] = sev_counts.get(sev, 0) + 1
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
            "by_service":     svc_counts,
            "most_affected":  max(svc_counts, key=svc_counts.get)
                              if svc_counts else "none",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute stats: {str(e)}"
        )


@router.get("/knowledge-base",
            summary="RAG knowledge base statistics")
@limiter.limit("30/minute")
async def knowledge_base_stats(
    request:      Request,
    current_user: Optional[dict] = Depends(get_current_user),
):
    try:
        ROOT = os.path.dirname(os.path.dirname(
               os.path.dirname(os.path.abspath(__file__))))
        if ROOT not in sys.path:
            sys.path.insert(0, ROOT)
        from rca.rag_retriever import RAGRetriever
        rag   = RAGRetriever()
        stats = rag.get_stats()
        return {
            "seed_incidents":    stats["seed_incidents"],
            "learned_incidents": stats["learned_incidents"],
            "total_incidents":   stats["total"],
            "description": (
                f"Started with {stats['seed_incidents']} seed incidents, "
                f"auto-learned {stats['learned_incidents']} from live operation."
            )
        }
    except Exception as e:
        return {
            "message": "Knowledge base not yet initialized",
            "tip":     "Run the full pipeline to generate incidents",
            "error":   str(e)
        }


@router.get("/{incident_id}", summary="Get incident by ID")
@limiter.limit("100/minute")
async def get_incident(
    request:      Request,
    incident_id:  str,
    current_user: Optional[dict] = Depends(get_current_user),
):
    try:
        if not incident_id.startswith("INC-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid incident ID format. Expected: INC-YYYYMMDD-HHMMSS"
            )
        incidents = load_all_incidents()
        match = next(
            (i for i in incidents if i.get("incident_id") == incident_id),
            None
        )
        if not match:
            raise HTTPException(
                status_code=404,
                detail=f"Incident '{incident_id}' not found. "
                       f"Check /incidents/ for available incidents."
            )
        return {
            "incident":    match,
            "report_text": load_report_text(incident_id)
                           or "Report text not available"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve incident: {str(e)}"
        )
