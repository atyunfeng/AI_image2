from pathlib import Path


class BenchmarkRunnerUnavailable(RuntimeError):
    pass


def run_benchmark(*, manifest_path: Path, model_configuration_id: str, results_path: Path) -> None:
    del manifest_path, model_configuration_id, results_path
    raise BenchmarkRunnerUnavailable(
        "Live benchmark execution requires a configured provider and real 30-SKU assets; "
        "validate the manifest first, then run from the operator environment."
    )
