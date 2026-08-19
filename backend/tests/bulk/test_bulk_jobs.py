from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from aiimage.bulk.models import BulkJob
from aiimage.bulk.service import process_next_bulk_job
from aiimage.workflow.queue import QueueHints


async def _setup(admin_client, png_bytes: bytes):
    product = (
        await admin_client.post(
            "/api/v1/products",
            json={"sku": "BULK-001", "name": "批量衬衫", "category": "apparel"},
        )
    ).json()
    uploaded = await admin_client.post(
        f"/api/v1/products/{product['id']}/references",
        data={"view": "front"},
        files={"file": ("front.png", png_bytes, "image/png")},
    )
    assert uploaded.status_code == 201
    model = (
        await admin_client.post(
            "/api/v1/models",
            json={
                "name": "Bulk Mock",
                "provider": "mock",
                "model_id": "mock-bulk",
                "capabilities": ["reference_to_image"],
            },
        )
    ).json()
    packs = {
        pack["slug"]: pack for pack in (await admin_client.get("/api/v1/template-packs")).json()
    }
    return product, model, packs


@pytest.mark.asyncio
async def test_bulk_csv_validates_then_queues_existing_sku(
    admin_client, session_factory, png_bytes: bytes
) -> None:
    _, model, packs = await _setup(admin_client, png_bytes)
    csv_bytes = (
        "sku,name,category,platform_slug,mode\nBULK-001,批量衬衫,apparel,jd-cn,strict\n"
    ).encode()
    form = {
        "model_configuration_id": model["id"],
        "category_pack_version_id": packs["apparel-core"]["version_id"],
        "brand_pack_version_id": packs["brand-neutral"]["version_id"],
    }

    validated = await admin_client.post(
        "/api/v1/bulk-jobs/import",
        data={**form, "dry_run": "true"},
        files={"file": ("products.csv", csv_bytes, "text/csv")},
    )
    assert validated.status_code == 202, validated.text
    assert validated.json()["status"] == "pending"
    await process_next_bulk_job(session_factory, QueueHints(), worker_id="test-worker")
    validated_body = (await admin_client.get(f"/api/v1/bulk-jobs/{validated.json()['id']}")).json()
    assert validated_body["status"] == "validated"
    assert validated_body["rows"][0]["status"] == "valid"

    queued = await admin_client.post(
        "/api/v1/bulk-jobs/import",
        data={**form, "dry_run": "false"},
        files={"file": ("products.csv", csv_bytes, "text/csv")},
    )
    assert queued.status_code == 202, queued.text
    await process_next_bulk_job(session_factory, QueueHints(), worker_id="test-worker")
    body = (await admin_client.get(f"/api/v1/bulk-jobs/{queued.json()['id']}")).json()
    assert body["status"] == "queued"
    assert body["succeeded_rows"] == 1
    assert len(body["rows"][0]["batch_ids"]) == 2


@pytest.mark.asyncio
async def test_bulk_csv_keeps_row_level_errors(
    admin_client, session_factory, png_bytes: bytes
) -> None:
    _, model, packs = await _setup(admin_client, png_bytes)
    csv_bytes = (
        "sku,name,category,platform_slug\nNEW-001,新品,apparel,missing-platform\n"
    ).encode()
    response = await admin_client.post(
        "/api/v1/bulk-jobs/import",
        data={
            "model_configuration_id": model["id"],
            "category_pack_version_id": packs["apparel-core"]["version_id"],
            "brand_pack_version_id": packs["brand-neutral"]["version_id"],
            "dry_run": "true",
        },
        files={"file": ("invalid.csv", csv_bytes, "text/csv")},
    )
    assert response.status_code == 202
    await process_next_bulk_job(session_factory, QueueHints(), worker_id="test-worker")
    body = (await admin_client.get(f"/api/v1/bulk-jobs/{response.json()['id']}")).json()
    assert body["status"] == "validation_failed"
    assert body["failed_rows"] == 1
    errors = await admin_client.get(f"/api/v1/bulk-jobs/{body['id']}/errors.csv")
    assert errors.status_code == 200
    assert "missing" not in errors.text
    assert "Unknown published platform_slug" in errors.text


@pytest.mark.asyncio
async def test_bulk_worker_recovers_an_expired_processing_lease(
    admin_client, session_factory, png_bytes: bytes
) -> None:
    _, model, packs = await _setup(admin_client, png_bytes)
    response = await admin_client.post(
        "/api/v1/bulk-jobs/import",
        data={
            "model_configuration_id": model["id"],
            "category_pack_version_id": packs["apparel-core"]["version_id"],
            "brand_pack_version_id": packs["brand-neutral"]["version_id"],
            "dry_run": "true",
        },
        files={
            "file": (
                "recover.csv",
                b"sku,name,category,platform_slug\nBULK-001,Shirt,apparel,jd-cn\n",
                "text/csv",
            )
        },
    )
    async with session_factory() as session:
        job = await session.get(BulkJob, UUID(response.json()["id"]))
        assert job is not None
        job.status = "processing"
        job.lease_owner = "dead-worker"
        job.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await session.commit()

    recovered = await process_next_bulk_job(
        session_factory, QueueHints(), worker_id="replacement-worker"
    )

    assert str(recovered) == response.json()["id"]
    body = (await admin_client.get(f"/api/v1/bulk-jobs/{recovered}")).json()
    assert body["status"] == "validated"
