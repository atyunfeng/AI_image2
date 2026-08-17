from io import BytesIO

import pytest
from PIL import Image


@pytest.mark.asyncio
async def test_compile_plan_from_one_front_reference(operator_client) -> None:
    product_response = await operator_client.post(
        "/api/v1/products", json={"sku": "M2-001", "name": "M2 衬衫", "category": "apparel"}
    )
    product_id = product_response.json()["id"]
    buffer = BytesIO()
    Image.new("RGB", (24, 24), "white").save(buffer, format="PNG")
    uploaded = await operator_client.post(
        f"/api/v1/products/{product_id}/references",
        data={"view": "front"},
        files={"file": ("front.png", buffer.getvalue(), "image/png")},
    )
    assert uploaded.status_code == 201
    packs = (await operator_client.get("/api/v1/template-packs")).json()
    by_slug = {pack["slug"]: pack for pack in packs}
    response = await operator_client.post(
        "/api/v1/production-plans/compile",
        json={
            "product_id": product_id,
            "platform_pack_version_id": by_slug["amazon-global"]["version_id"],
            "category_pack_version_id": by_slug["apparel-core"]["version_id"],
            "brand_pack_version_id": by_slug["brand-neutral"]["version_id"],
            "mode": "strict",
        },
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert len(body["items"]) == 3
    assert body["items"][0]["slot"] == "hero_front"
    assert body["compiled_snapshot"]["packs"]["platform"]["version"] == 1
