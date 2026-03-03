# ============================================================
# rca/incident_store.py
# PURPOSE: Persistent storage for incident knowledge base
#
# Every resolved incident is saved here automatically.
# The RAG retriever searches BOTH hardcoded + learned incidents.
#
# Storage: JSON file at data/incident_knowledge_base.json
# ============================================================

import json
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Optional

# Path to the knowledge base file
KB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "incident_knowledge_base.json"
)


class IncidentStore:
    """
    Persistent JSON-based storage for learned incidents.

    Every time the platform resolves a new incident,
    it's saved here so future similar incidents can
    benefit from this experience.

    Think of it as the system's memory of past outages.
    """

    def __init__(self):
        self.kb_path = KB_PATH
        # Ensure data/ directory exists
        os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
        self.incidents = self._load()
        print(f"✅ Incident Store loaded — "
              f"{len(self.incidents)} learned incidents in knowledge base")

    def _load(self) -> List[Dict]:
        """Loads incidents from JSON file"""
        if not os.path.exists(self.kb_path):
            # First run — create empty knowledge base
            self._save([])
            return []
        try:
            with open(self.kb_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, incidents: List[Dict]):
        """Saves incidents to JSON file"""
        with open(self.kb_path, "w", encoding="utf-8") as f:
            json.dump(incidents, f, indent=2, default=str)

    def add_incident(self, rca_report: Dict) -> str:
        """
        Saves a new resolved incident to the knowledge base.

        Converts the RCA report format into the standard
        incident format used by RAGRetriever.

        Returns the new incident ID.
        """
        # Generate a unique incident ID
        inc_id = rca_report.get(
            "incident_id",
            f"LEARNED-{uuid.uuid4().hex[:8].upper()}"
        )

        primary = rca_report.get("primary_anomaly", {})
        blast   = rca_report.get("blast_radius", {})

        # Build the learned incident record
        new_incident = {
            "id":                inc_id,
            "date":              datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "service":           rca_report.get("root_cause_service", "unknown"),
            "anomaly_type":      primary.get("type", "unknown"),
            "root_cause":        rca_report.get("root_cause_summary", ""),
            "symptoms": (
                f"Observed {primary.get('metric_name','metric')} = "
                f"{primary.get('observed_value','?')} "
                f"(expected {primary.get('expected_value','?')}). "
                f"Affected services: "
                f"{blast.get('directly_affected', [])}"
            ),
            "resolution":        " | ".join(
                rca_report.get("recommended_fixes", [])[:2]
            ),
            "duration_minutes":  30,   # estimated
            "severity":          rca_report.get("severity", 3),
            "hypotheses":        rca_report.get("hypotheses", []),
            "blast_radius":      blast,
            "learned_at":        datetime.now(timezone.utc).isoformat(),
            "source":            "auto_learned",
        }

        # Add to in-memory list
        self.incidents.append(new_incident)

        # Persist to disk
        self._save(self.incidents)

        print(f"🧠 LEARNED: New incident saved to knowledge base")
        print(f"   ID      : {inc_id}")
        print(f"   Service : {new_incident['service']}")
        print(f"   Total KB: {len(self.incidents)} incidents")

        return inc_id

    def get_all(self) -> List[Dict]:
        """Returns all learned incidents"""
        return self.incidents

    def get_by_service(self, service: str) -> List[Dict]:
        """Returns all incidents for a specific service"""
        return [i for i in self.incidents
                if i.get("service") == service]

    def count(self) -> int:
        """Returns total number of learned incidents"""
        return len(self.incidents)

    def clear(self):
        """Clears all learned incidents (for testing)"""
        self.incidents = []
        self._save([])
        print("🗑️  Incident knowledge base cleared")