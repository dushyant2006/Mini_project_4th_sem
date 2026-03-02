from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
import uuid


class LogLevel(str, Enum):
    DEBUG    = "DEBUG"
    INFO     = "INFO"
    WARNING  = "WARNING"
    ERROR    = "ERROR"
    CRITICAL = "CRITICAL"


class SpanStatus(str, Enum):
    OK      = "OK"
    ERROR   = "ERROR"
    TIMEOUT = "TIMEOUT"


class LogEvent(BaseModel):
    event_id:  str      = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service:   str
    level:     LogLevel
    message:   str
    trace_id:  Optional[str]       = None
    span_id:   Optional[str]       = None
    metadata:  Dict[str, Any]      = {}


class MetricEvent(BaseModel):
    event_id:    str      = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:   datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service:     str
    metric_name: str
    value:       float
    unit:        str              = ""
    tags:        Dict[str, str]   = {}


class TraceSpan(BaseModel):
    trace_id:       str      = Field(default_factory=lambda: str(uuid.uuid4()))
    span_id:        str      = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_span_id: Optional[str]      = None
    timestamp:      datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service:        str
    operation:      str
    duration_ms:    float
    status:         SpanStatus
    error_message:  Optional[str]      = None
    tags:           Dict[str, Any]     = {}


class AnomalyEvent(BaseModel):
    event_id:          str      = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp:         datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    service:           str
    anomaly_type:      str
    severity:          int
    metric_name:       str
    observed_value:    float
    expected_value:    float
    description:       str
    related_trace_ids: List[str] = []