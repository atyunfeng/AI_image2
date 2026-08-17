from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class CostSummary(BaseModel):
    currency: str
    task_count: int
    succeeded_count: int
    failed_count: int
    reported_cost_minor: int
    average_cost_minor: float
    success_rate: float


class DailyCostPoint(BaseModel):
    date: date
    currency: str
    task_count: int
    reported_cost_minor: int


class CostBreakdownRow(BaseModel):
    provider: str
    model: str
    platform: str
    sku: str
    currency: str
    task_count: int
    succeeded_count: int
    failed_count: int
    reported_cost_minor: int


class CostReportResponse(BaseModel):
    generated_at: datetime
    cost_basis: Literal["provider_reported_or_estimated"]
    summaries: list[CostSummary]
    daily: list[DailyCostPoint]
    breakdown: list[CostBreakdownRow]


class OperationAlert(BaseModel):
    code: str
    severity: Literal["info", "warning", "critical"]
    title: str
    detail: str
    action_url: str


class FailureClassRow(BaseModel):
    classification: str
    count: int


class OperationsReportResponse(BaseModel):
    generated_at: datetime
    queued_count: int
    running_count: int
    review_pending_count: int
    failed_count: int
    total_calls: int
    succeeded_calls: int
    retry_calls: int
    success_rate: float
    retry_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    failure_classes: list[FailureClassRow]
    cost_groups: list[CostSummary]
    alerts: list[OperationAlert]
