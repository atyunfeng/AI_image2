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
