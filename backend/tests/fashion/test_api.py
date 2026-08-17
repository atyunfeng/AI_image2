from io import BytesIO

import pytest
from PIL import Image


async def _png() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (32, 64), "white").save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.asyncio
async def test_create_fashion_plan_with_capability_routing(admin_client) -> None:
    product = (
        await admin_client.post(
            "/api/v1/products",
            json={"sku": "FASHION-001", "name": "试穿衬衫", "category": "apparel"},
        )
    ).json()
    image = await _png()
    for view in ["front", "side", "back"]:
        response = await admin_client.post(
            f"/api/v1/products/{product['id']}/references",
            data={"view": view},
            files={"file": (f"{view}.png", image, "image/png")},
        )
        assert response.status_code == 201
    profile = (
        await admin_client.post(
            "/api/v1/model-profiles",
            json={
                "name": "Fashion system model",
                "profile_type": "system_virtual",
                "authorization_status": "not_required",
            },
        )
    ).json()
    for view in ["front", "side", "back"]:
        assert (
            await admin_client.post(
                f"/api/v1/model-profiles/{profile['id']}/references",
                data={"view": view},
                files={"file": (f"model-{view}.png", image, "image/png")},
            )
        ).status_code == 201
    model = (
        await admin_client.post(
            "/api/v1/models",
            json={
                "name": "Fashion Mock",
                "provider": "mock",
                "model_id": "mock-fashion-v1",
                "api_key": "fashion-key",
                "capabilities": [
                    "reference_to_image",
                    "multi_reference_to_image",
                    "virtual_try_on",
                ],
            },
        )
    ).json()
    response = await admin_client.post(
        "/api/v1/fashion-plans",
        json={
            "product_id": product["id"],
            "model_profile_id": profile["id"],
            "model_configuration_id": model["id"],
            "requested_outputs": ["product_front", "model_side", "virtual_try_on"],
            "mode": "strict",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert [batch["capability"] for batch in body["batches"]] == [
        "reference_to_image",
        "multi_reference_to_image",
        "virtual_try_on",
    ]
    assert {batch["fashion_plan_id"] for batch in body["batches"]} == {body["id"]}
