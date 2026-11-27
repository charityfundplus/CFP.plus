"""Per-ID policy for sandbox CMP work orders and evidence."""

import hmac
import os
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

from .core import Backend, Experiment
from .queue import Queue

RecordID = Annotated[str, StringConstraints(pattern=r"^[0-9]{1,64}$")]
WorkOrderID = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,100}$")]
JobID = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{32}$")]


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    token: Annotated[str, StringConstraints(min_length=32, max_length=256)]
    backends: set[Backend]
    work_orders: set[WorkOrderID] | None = None


class HandoffGrant(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recipient: RecordID
    reviewer: RecordID


class Configuration(BaseModel):
    model_config = ConfigDict(extra="forbid")
    database: Path
    principals: dict[RecordID, Policy]
    evidence_grants: dict[RecordID, dict[WorkOrderID, HandoffGrant]] = {}

    @field_validator("principals")
    @classmethod
    def unique_tokens(cls, principals):
        if len({p.token for p in principals.values()}) != len(principals):
            raise ValueError("Sandbox tokens must be unique by ID")
        return principals


class WorkOrder(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    work_order_id: WorkOrderID
    experiment: Experiment


class AccessDenied(Exception):
    pass


def configuration():
    path = os.environ.get("SUPER_QUANTUM_Z_QUEUE_CONFIG")
    if not path:
        raise AccessDenied("Shared sandbox queue is disabled")
    return Configuration.model_validate_json(Path(path).read_bytes())


def authorize(config, owner, authorization):
    policy = config.principals.get(owner)
    if policy is None or not hmac.compare_digest(
        authorization.encode(), f"Bearer {policy.token}".encode()
    ):
        raise AccessDenied("Unauthorized")
    return policy


def submit(config, owner, authorization, order):
    policy = authorize(config, owner, authorization)
    if order.experiment.backend not in policy.backends:
        raise AccessDenied("Backend is disabled for this ID")
    if policy.work_orders is not None and order.work_order_id not in policy.work_orders:
        raise AccessDenied("Work order is outside this ID's scope")
    return {"job": Queue(config.database).submit(owner, order.work_order_id, order.experiment)}


def evidence(config, owner, authorization, job):
    authorize(config, owner, authorization)
    return Queue(config.database).evidence(owner, job)
