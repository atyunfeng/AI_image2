async def test_create_product_and_upload_reference(admin_client, png_bytes: bytes) -> None:
    product_response = await admin_client.post(
        "/api/v1/products",
        json={"sku": "DRESS-001", "name": "Floral dress", "category": "apparel"},
    )
    assert product_response.status_code == 201
    product = product_response.json()

    response = await admin_client.post(
        f"/api/v1/products/{product['id']}/references",
        files={"file": ("front.png", png_bytes, "image/png")},
        data={"view": "front"},
    )

    assert response.status_code == 201
    assert response.json()["sha256"]
    assert response.json()["view"] == "front"


async def test_sku_is_case_insensitive_unique(admin_client) -> None:
    payload = {"sku": "SHOE-001", "name": "Runner", "category": "shoes"}
    assert (await admin_client.post("/api/v1/products", json=payload)).status_code == 201
    payload["sku"] = "shoe-001"
    assert (await admin_client.post("/api/v1/products", json=payload)).status_code == 409

