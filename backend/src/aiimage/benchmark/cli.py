import argparse
import json
from pathlib import Path

from aiimage.benchmark.report import build_report
from aiimage.benchmark.runner import BenchmarkExecutionError, run_benchmark
from aiimage.benchmark.validator import validate_manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aiimage-benchmark")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="validate a 30-SKU manifest and assets")
    validate.add_argument("manifest", type=Path)
    run = commands.add_parser("run", help="run against a configured live provider")
    run.add_argument("manifest", type=Path)
    run.add_argument("--model-configuration-id", required=True)
    run.add_argument("--results", type=Path, default=Path("benchmark-results.jsonl"))
    run.add_argument("--api-base-url", default="http://localhost:8000/api/v1")
    run.add_argument("--email", required=True)
    run.add_argument("--password", required=True)
    run.add_argument("--timeout-seconds", type=int, default=600)
    report = commands.add_parser("report", help="aggregate JSONL attempt results")
    report.add_argument("results", type=Path)
    report.add_argument("--output", type=Path, default=Path("capability-report.json"))
    return parser


def main() -> None:
    arguments = _parser().parse_args()
    if arguments.command == "validate":
        data = json.loads(arguments.manifest.read_text())
        manifest = validate_manifest(data, base_dir=arguments.manifest.parent)
        print(f"valid: {len(manifest.products)} products")
    elif arguments.command == "run":
        try:
            run_benchmark(
                manifest_path=arguments.manifest,
                model_configuration_id=arguments.model_configuration_id,
                results_path=arguments.results,
                api_base_url=arguments.api_base_url,
                email=arguments.email,
                password=arguments.password,
                timeout_seconds=arguments.timeout_seconds,
            )
        except BenchmarkExecutionError as error:
            raise SystemExit(str(error)) from error
    else:
        report = build_report(arguments.results)
        arguments.output.write_text(report.model_dump_json(indent=2))
        print(arguments.output)
