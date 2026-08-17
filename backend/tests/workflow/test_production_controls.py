from io import BytesIO

from PIL import Image


async def _plan_and_model(client):
    product = (
        await client.post(
            "/api/v1/products",
            json={"sku": "CONTROL-001", "name": "Control shirt", "category": "apparel"},
        )
    ).json()
    image = BytesIO()
    Image.new("RGB", (16, 16), "white").save(image, format="PNG")
    reference = (
        await client.post(
            f"/api/v1/products/{product['id']}/references",
            data={"view": "front"},
            files={"file": ("front.png", image.getvalue(), "image/png")},
        )
    ).json()
    packs = {pack["slug"]: pack for pack in (await client.get("/api/v1/template-packs")).json()}
    plan = (
        await client.post(
            "/api/v1/production-plans/compile",
            json={
                "product_id": product["id"],
                "platform_pack_version_id": packs["amazon-global"]["version_id"],
                "category_pack_version_id": packs["apparel-core"]["version_id"],
                "brand_pack_version_id": packs["brand-neutral"]["version_id"],
                "mode": "strict",
            },
        )
    ).json()
    model = (
        await client.post(
            "/api/v1/models",
            json={
                "name": "Control mock",
                "provider": "mock",
                "model_id": "mock-v1",
                "api_key": "control-key",
                "capabilities": ["reference_to_image"],
            },
        )
    ).json()
    return plan, model, reference


async def test_plan_items_are_editable_only_before_execution(admin_client) -> None:
    plan, model, reference = await _plan_and_model(admin_client)
    item = plan["items"][0]
    updated = await admin_client.patch(
        f"/api/v1/production-plans/{plan['id']}/items/{item['id']}",
        json={
            "prompt": "Updated hero prompt",
            "width": 1200,
            "model_configuration_id": model["id"],
            "reference_ids": [reference["id"]],
            "provider_parameters": {"seed": 9},
        },
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["provider_parameters"] == {"seed": 9}

    executed = await admin_client.post(
        f"/api/v1/production-plans/{plan['id']}/execute",
        json={"model_configuration_id": model["id"]},
    )
    assert executed.status_code == 201, executed.text
    assert executed.json()[0]["model_configuration_id"] == model["id"]
    locked = await admin_client.patch(
        f"/api/v1/production-plans/{plan['id']}/items/{item['id']}", json={"width": 900}
    )
    assert locked.status_code == 409


async def test_duplicate_batch_records_source_and_retry_rejects_active_batch(admin_client) -> None:
    plan, model, _ = await _plan_and_model(admin_client)
    batches = (
        await admin_client.post(
            f"/api/v1/production-plans/{plan['id']}/execute",
            json={"model_configuration_id": model["id"]},
        )
    ).json()
    source = batches[0]
    duplicate = await admin_client.post(
        f"/api/v1/batches/{source['id']}/duplicate",
        json={"prompt": "Variant prompt", "width": 900, "height": 900},
    )
    assert duplicate.status_code == 201, duplicate.text
    assert duplicate.json()["source_batch_id"] == source["id"]
    assert duplicate.json()["prompt"] == "Variant prompt"
    assert (await admin_client.post(f"/api/v1/batches/{source['id']}/retry")).status_code == 409
