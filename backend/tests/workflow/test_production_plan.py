from io import BytesIO

import pytest
from PIL import Image


async def _prepare_plan(client):
    product = (
        await client.post(
            "/api/v1/products",
            json={"sku": "SET-001", "name": "套图衬衫", "category": "apparel"},
        )
    ).json()
    buffer = BytesIO()
    Image.new("RGB", (32, 32), "white").save(buffer, format="PNG")
    await client.post(
        f"/api/v1/products/{product['id']}/references",
        data={"view": "front"},
        files={"file": ("front.png", buffer.getvalue(), "image/png")},
    )
    packs = {pack["slug"]: pack for pack in (await client.get("/api/v1/template-packs")).json()}
    plan = await client.post(
        "/api/v1/production-plans/compile",
        json={
            "product_id": product["id"],
            "platform_pack_version_id": packs["taobao-tmall-cn"]["version_id"],
            "category_pack_version_id": packs["apparel-core"]["version_id"],
            "brand_pack_version_id": packs["brand-neutral"]["version_id"],
            "mode": "strict",
        },
    )
    return plan.json()


@pytest.mark.asyncio
async def test_execute_plan_creates_one_batch_per_slot(admin_client) -> None:
    plan = await _prepare_plan(admin_client)
    model = await admin_client.post(
        "/api/v1/models",
        json={
            "name": "M2 mock",
            "provider": "mock",
            "model_id": "mock-v1",
            "api_key": "m2-test-key",
            "capabilities": ["reference_to_image"],
        },
    )
    response = await admin_client.post(
        f"/api/v1/production-plans/{plan['id']}/execute",
        json={"model_configuration_id": model.json()["id"]},
    )
    assert response.status_code == 201, response.text
    batches = response.json()
    assert [batch["requested_view"] for batch in batches] == ["front", "detail", "front"]
    assert {batch["production_plan_id"] for batch in batches} == {plan["id"]}
    assert len({batch["production_plan_item_id"] for batch in batches}) == 3


@pytest.mark.asyncio
async def test_production_plan_cannot_execute_twice(admin_client) -> None:
    plan = await _prepare_plan(admin_client)
    model = (
        await admin_client.post(
            "/api/v1/models",
            json={
                "name": "M2 once",
                "provider": "mock",
                "model_id": "mock-v1",
                "api_key": "m2-test-key",
                "capabilities": ["reference_to_image"],
            },
        )
    ).json()
    path = f"/api/v1/production-plans/{plan['id']}/execute"
    assert (await admin_client.post(path, json={"model_configuration_id": model["id"]})).status_code == 201
    second = await admin_client.post(path, json={"model_configuration_id": model["id"]})
    assert second.status_code == 422
    assert "already" in second.json()["detail"]
