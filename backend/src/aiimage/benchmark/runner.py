import json
import mimetypes
import time
from pathlib import Path
from typing import Any

import httpx

from aiimage.benchmark.validator import validate_manifest

TERMINAL_BATCH_STATUSES = {
    "review_pending",
    "approved",
    "rejected",
    "exported",
    "failed",
    "canceled",
}


class BenchmarkExecutionError(RuntimeError):
    pass


class BenchmarkApiClient:
    def __init__(
        self,
        *,
        api_base_url: str,
        email: str,
        password: str,
        timeout_seconds: int,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.client = httpx.Client(
            base_url=api_base_url.rstrip("/"),
            timeout=30,
            transport=transport,
        )
        response = self.client.post("/auth/login", json={"email": email, "password": password})
        self._raise(response, "Benchmark login failed")
        self.client.headers["Authorization"] = f"Bearer {response.json()['access_token']}"

    @staticmethod
    def _raise(response: httpx.Response, message: str) -> None:
        if response.is_error:
            raise BenchmarkExecutionError(
                f"{message}: HTTP {response.status_code} {response.text[:500]}"
            )

    def close(self) -> None:
        self.client.close()

    def model(self, model_configuration_id: str) -> dict[str, Any]:
        response = self.client.get("/models")
        self._raise(response, "Cannot read model configuration")
        model = next(
            (item for item in response.json() if item["id"] == model_configuration_id),
            None,
        )
        if model is None:
            raise BenchmarkExecutionError("Model configuration was not found")
        if model["provider"] == "mock":
            raise BenchmarkExecutionError("Mock Provider cannot produce a release benchmark")
        return model

    def ensure_product(self, product) -> str:
        response = self.client.get("/products")
        self._raise(response, "Cannot list products")
        existing = next((item for item in response.json() if item["sku"] == product.sku.upper()), None)
        if existing:
            product_id = existing["id"]
        else:
            response = self.client.post(
                "/products",
                json={"sku": product.sku, "name": product.sku, "category": product.category.value},
            )
            self._raise(response, f"Cannot create product {product.sku}")
            product_id = response.json()["id"]
        response = self.client.post(
            f"/products/{product_id}/truth-anchors",
            json={"document": product.truth_anchors},
        )
        self._raise(response, f"Cannot save truth anchor for {product.sku}")
        return product_id

    def upload_references(self, product_id: str, product, base_dir: Path) -> None:
        for reference in product.references:
            path = base_dir / reference.path
            mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            with path.open("rb") as handle:
                response = self.client.post(
                    f"/products/{product_id}/references",
                    data={"view": reference.view.value},
                    files={"file": (path.name, handle, mime_type)},
                )
            if response.status_code == 409:
                continue
            self._raise(response, f"Cannot upload reference {path.name}")

    def run_attempt(
        self,
        *,
        product_id: str,
        product,
        requested_view,
        model_configuration_id: str,
        mode: str,
    ) -> dict[str, Any]:
        started = time.monotonic()
        response = self.client.post(
            "/batches",
            json={
                "product_id": product_id,
                "model_configuration_id": model_configuration_id,
                "requested_view": requested_view.value,
                "mode": mode,
                "prompt": (
                    "30 SKU benchmark: preserve product identity, color, material, logo and structure"
                ),
                "width": 1024,
                "height": 1024,
            },
        )
        self._raise(response, f"Cannot create benchmark batch for {product.sku}")
        batch_id = response.json()["id"]
        deadline = time.monotonic() + self.timeout_seconds
        batch: dict[str, Any] = response.json()
        while time.monotonic() < deadline:
            response = self.client.get(f"/batches/{batch_id}")
            self._raise(response, f"Cannot poll benchmark batch {batch_id}")
            batch = response.json()
            if batch["status"] in TERMINAL_BATCH_STATUSES:
                break
            time.sleep(1)
        else:
            raise BenchmarkExecutionError(f"Benchmark batch {batch_id} timed out")

        quality_response = self.client.get(f"/batches/{batch_id}/quality")
        technical_passed = quality_response.is_success and bool(
            quality_response.json().get("passed")
        )
        return {
            "sku": product.sku,
            "category": product.category.value,
            "requested_view": requested_view.value,
            "batch_id": batch_id,
            "status": (
                "succeeded"
                if batch["status"] in {"review_pending", "approved", "exported"}
                else "failed"
            ),
            "batch_status": batch["status"],
            "technical_passed": technical_passed,
            "human_review_passed": None,
            "cost_minor": int(batch.get("estimated_cost_minor") or 0),
            "latency_ms": int((time.monotonic() - started) * 1000),
            "error_classification": batch.get("error_classification"),
        }


def run_benchmark(
    *,
    manifest_path: Path,
    model_configuration_id: str,
    results_path: Path,
    api_base_url: str,
    email: str,
    password: str,
    timeout_seconds: int = 600,
    transport: httpx.BaseTransport | None = None,
) -> None:
    manifest = validate_manifest(
        json.loads(manifest_path.read_text()),
        base_dir=manifest_path.parent,
    )
    api = BenchmarkApiClient(
        api_base_url=api_base_url,
        email=email,
        password=password,
        timeout_seconds=timeout_seconds,
        transport=transport,
    )
    try:
        model = api.model(model_configuration_id)
        with results_path.open("w", encoding="utf-8") as output:
            for product in manifest.products:
                product_id = api.ensure_product(product)
                api.upload_references(product_id, product, manifest_path.parent)
                for requested_view in product.requested_views:
                    record = api.run_attempt(
                        product_id=product_id,
                        product=product,
                        requested_view=requested_view,
                        model_configuration_id=model_configuration_id,
                        mode=manifest.mode,
                    )
                    record.update({"provider": model["provider"], "model_id": model["model_id"]})
                    output.write(json.dumps(record, ensure_ascii=False) + "\n")
                    output.flush()
    finally:
        api.close()
