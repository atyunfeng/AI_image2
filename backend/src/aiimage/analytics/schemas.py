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

