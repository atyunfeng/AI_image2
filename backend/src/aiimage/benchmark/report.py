import json
import statistics
from pathlib import Path

from aiimage.benchmark.models import CapabilityReport


def build_report(results_path: Path) -> CapabilityReport:
    records = [json.loads(line) for line in results_path.read_text().splitlines() if line.strip()]
    if not records:
        raise ValueError("Benchmark results are empty")
    return CapabilityReport(
        provider=records[0]["provider"],
        model_id=records[0]["model_id"],
        total_attempts=len(records),
        successful_attempts=sum(record["status"] == "succeeded" for record in records),
        total_cost_minor=sum(int(record.get("cost_minor", 0)) for record in records),
        median_latency_ms=int(statistics.median(record["latency_ms"] for record in records)),
        results_path=results_path,
    )
