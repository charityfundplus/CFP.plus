from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class WorkOrderStatus(str, Enum):
    RECEIVED = "RECEIVED"
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    PROCESSING = "PROCESSING"
    CALLBACK_RECEIVED = "CALLBACK_RECEIVED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    BLOCKED = "BLOCKED"


class ExecutionStatus(str, Enum):
    RECORDED = "RECORDED"
    VERIFIED = "VERIFIED"
    BLOCKED = "BLOCKED"


class ExecutionEvent(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event: str
    component: str
    status: str
    http_status: Optional[int] = None
    detail: Dict[str, Any] = Field(default_factory=dict)


class WorkOrderCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    work_order_id: str
    provider: str
    model: str
    task: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class WorkOrderResponse(BaseModel):
    execution_id: str = Field(description="Operational Execution ID; not a CFP+ Canonical ID")
    work_order_id: str
    status: WorkOrderStatus
    created_at: datetime
    message: str


class EvidencePackageResponse(BaseModel):
    execution_id: str
    work_order_id: str
    provider: str
    model: str
    request_hash: str
    response_hash: str
    timestamp: datetime
    http_status: int
    execution_logs: List[ExecutionEvent]
    evidence_uri: str
    status: ExecutionStatus = ExecutionStatus.RECORDED
