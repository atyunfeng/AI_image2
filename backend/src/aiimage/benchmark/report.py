import json
import statistics
from collections import defaultdict
from pathlib import Path

from aiimage.benchmark.models import CapabilityReport


def build_report(results_path: Path) -> CapabilityReport:
    records = [json.loads(line) for line in results_path.read_text().splitlines() if line.strip()]
    if not records:
        raise ValueError("Benchmark results are empty")
    technical_passed = sum(bool(record.get("technical_passed")) for record in records)
    human_records = [record for record in records if record.get("human_review_passed") is not None]
    human_passed = sum(bool(record["human_review_passed"]) for record in human_records)
    categories: dict[str, dict[str, int]] = defaultdict(
        lambda: {"attempts": 0, "succeeded": 0, "technical_passed": 0}
    )
    for record in records:
        category = str(record.get("category") or "unknown")
        categories[category]["attempts"] += 1
        categories[category]["succeeded"] += int(record["status"] == "succeeded")
        categories[category]["technical_passed"] += int(bool(record.get("technical_passed")))
    technical_rate = technical_passed / len(records)
    human_rate = human_passed / len(human_records) if human_records else None
    return CapabilityReport(
        provider=records[0]["provider"],
        model_id=records[0]["model_id"],
        total_attempts=len(records),
        successful_attempts=sum(record["status"] == "succeeded" for record in records),
        total_cost_minor=sum(int(record.get("cost_minor", 0)) for record in records),
        median_latency_ms=int(statistics.median(record["latency_ms"] for record in records)),
        results_path=results_path,
        technical_passed_attempts=technical_passed,
        technical_pass_rate=technical_rate,
        human_reviewed_attempts=len(human_records),
        human_passed_attempts=human_passed,
        human_pass_rate=human_rate,
        category_results={key: value for key, value in sorted(categories.items())},
        release_ready=technical_rate >= 0.9 and human_rate is not None and human_rate >= 0.8,
    )
