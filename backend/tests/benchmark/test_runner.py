import json

import httpx
import pytest

from aiimage.benchmark.runner import BenchmarkApiClient, BenchmarkExecutionError


def test_release_benchmark_rejects_mock_provider() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/auth/login"):
            return httpx.Response(200, json={"access_token": "token"})
        if request.url.path.endswith("/models"):
            return httpx.Response(
                200,
                json=[{"id": "model-1", "provider": "mock", "model_id": "mock-v1"}],
            )
        return httpx.Response(404, text=json.dumps({"detail": "not found"}))

    client = BenchmarkApiClient(
        api_base_url="http://test/api/v1",
        email="admin@example.com",
        password="not-used-by-mock",
        timeout_seconds=1,
        transport=httpx.MockTransport(handler),
    )
    try:
        with pytest.raises(BenchmarkExecutionError, match="Mock Provider"):
            client.model("model-1")
    finally:
        client.close()
