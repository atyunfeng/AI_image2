import json
from pathlib import Path

from aiimage.benchmark.report import build_report


def test_report_aggregates_results(tmp_path: Path):
    path = tmp_path / "results.jsonl"
    records = [
        {
            "provider": "mock",
            "model_id": "v1",
            "status": "succeeded",
            "cost_minor": 0,
            "latency_ms": 100,
        },
        {
            "provider": "mock",
            "model_id": "v1",
            "status": "failed",
            "cost_minor": 2,
            "latency_ms": 200,
        },
    ]
    path.write_text("\n".join(json.dumps(r) for r in records))
    report = build_report(path)
    assert report.total_attempts == 2
    assert report.successful_attempts == 1
    assert report.median_latency_ms == 150
