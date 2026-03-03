

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(int, Enum):
    CRITICAL = 1
    HIGH     = 2
    MEDIUM   = 3
    LOW      = 4


class AnomalySchema(BaseModel):
    """Schema for a single anomaly event"""
    incident_id:  Optional[str]
    timestamp:    Optional[str]
    service:      str
    anomaly_type: str
    observed:     float
    expected:     float
    severity:     int

    class Config:
        # Allows creating from ORM objects too
        from_attributes = True


class BlastRadiusSchema(BaseModel):
    """Schema for blast radius analysis"""
    failed_service:      str
    directly_affected:   List[str]
    indirectly_affected: List[str]
    total_affected:      int
    criticality_score:   int
    service_tier:        str
    owning_team:         str


class IncidentSchema(BaseModel):
    """Schema for a full incident report"""
    incident_id:         str
    timestamp:           str
    severity:            int
    root_cause_service:  str
    root_cause_summary:  str
    owning_team:         str
    hypotheses:          List[str]
    recommended_fixes:   List[str]
    blast_radius:        Dict[str, Any]
    anomaly_count:       int
    affected_services:   List[str]
    similar_incidents:   List[str]
    primary_anomaly:     Dict[str, Any]
    status:              str


class ServiceNodeSchema(BaseModel):
    """Schema for a service in the dependency graph"""
    id:           str
    label:        str
    tier:         str
    criticality:  str
    team:         str


class ServiceEdgeSchema(BaseModel):
    """Schema for a dependency edge"""
    source: str
    target: str
    label:  str


class GraphSchema(BaseModel):
    """Schema for the full service graph"""
    nodes:                List[ServiceNodeSchema]
    edges:                List[ServiceEdgeSchema]
    total_services:       int
    total_dependencies:   int


class HealthSchema(BaseModel):
    """Schema for health check response"""
    status:     str
    timestamp:  str
    components: Dict[str, str]


class SimulateAnomalyRequest(BaseModel):
    """Schema for triggering a test anomaly via API"""
    service: str = Field(
        ...,
        description="Service to inject anomaly into",
        example="payment-service"
    )
    duration_seconds: int = Field(
        default=60,
        description="How long to run anomaly simulation",
        ge=10,
        le=300
    )


class APIResponse(BaseModel):
    """Generic API response wrapper"""
    success:   bool
    message:   str
    data:      Optional[Any] = None
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )