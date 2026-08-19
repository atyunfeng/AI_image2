from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from aiimage.catalog.models import ReferenceView


class BenchmarkCategory(StrEnum):
    APPAREL = "apparel"
    SHOES = "shoes"
    HATS = "hats"


class BenchmarkReference(BaseModel):
    view: ReferenceView
    path: Path
    sha256: str | None = None


class BenchmarkProduct(BaseModel):
    sku: str = Field(min_length=1)
    category: BenchmarkCategory
    references: list[BenchmarkReference]
    truth_anchors: dict[str, Any]
    requested_views: list[ReferenceView]


class BenchmarkManifest(BaseModel):
    version: int = 1
    mode: str = "strict"
    products: list[BenchmarkProduct]


class CapabilityReport(BaseModel):
    provider: str
    model_id: str
    total_attempts: int
    successful_attempts: int
    total_cost_minor: int
    median_latency_ms: int
    results_path: Path
    technical_passed_attempts: int = 0
    technical_pass_rate: float = 0
    human_reviewed_attempts: int = 0
    human_passed_attempts: int = 0
    human_pass_rate: float | None = None
    category_results: dict[str, dict[str, float | int]] = Field(default_factory=dict)
    release_ready: bool = False
