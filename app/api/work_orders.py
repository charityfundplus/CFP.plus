import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Tuple

from fastapi import APIRouter, Header, HTTPException, Response, status

from app.schemas import WorkOrderCreateRequest, WorkOrderResponse, WorkOrderStatus

router = APIRouter(prefix="/api/v1/work-orders", tags=["work-orders"])

# P0 in-memory store. Replace with persistent operational storage before deployment.
# idempotency_key -> (request_hash, WorkOrderResponse)
_IDEMPOTENCY_STORE: Dict[str, Tuple[str, WorkOrderResponse]] = {}


def _request_hash(body: WorkOrderCreateRequest) -> str:
    canonical = json.dumps(
        body.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@router.post("", response_model=WorkOrderResponse, status_code=status.HTTP_201_CREATED)
def create_work_order(
    body: WorkOrderCreateRequest,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> WorkOrderResponse:
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for state-changing requests.",
        )

    incoming_hash = _request_hash(body)
    prior = _IDEMPOTENCY_STORE.get(idempotency_key)
    if prior is not None:
        prior_hash, prior_response = prior
        if prior_hash != incoming_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency-Key was already used with a different request payload.",
            )
        response.status_code = status.HTTP_200_OK
        return prior_response

    result = WorkOrderResponse(
        execution_id=f"EXEC-{uuid.uuid4().hex.upper()}",
        work_order_id=body.work_order_id,
        status=WorkOrderStatus.RECEIVED,
        created_at=datetime.now(timezone.utc),
        message="Work Order accepted. Evidence collection is mandatory by server policy.",
    )
    _IDEMPOTENCY_STORE[idempotency_key] = (incoming_hash, result)
    return result
