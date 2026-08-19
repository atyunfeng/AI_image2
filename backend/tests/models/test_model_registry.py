async def test_api_key_is_write_only(admin_client) -> None:
    response = await admin_client.post(
        "/api/v1/models",
        json={
            "name": "Mock Image",
            "provider": "mock",
            "model_id": "mock-v1",
            "billing_currency": "cny",
            "api_key": "secret-provider-key",
            "capabilities": ["reference_to_image"],
        },
    )

    assert response.status_code == 201
    assert "secret-provider-key" not in response.text
    assert response.json()["key_suffix"] == "-key"
    assert response.json()["has_key"] is True
    assert response.json()["billing_currency"] == "CNY"


async def test_admin_rotates_and_disables_model_without_exposing_secret(admin_client) -> None:
    created = await admin_client.post(
        "/api/v1/models",
        json={
            "name": "Managed Image",
            "provider": "generic_http",
            "model_id": "image-v1",
            "base_url": "https://provider.invalid",
            "api_key": "first-provider-key",
            "capabilities": ["reference_to_image"],
        },
    )
    model_id = created.json()["id"]

    updated = await admin_client.patch(
        f"/api/v1/models/{model_id}",
        json={"api_key": "rotated-provider-key", "is_enabled": False},
    )

    assert updated.status_code == 200
    assert updated.json()["is_enabled"] is False
    assert updated.json()["key_suffix"] == "-key"
    assert "rotated-provider-key" not in updated.text

    audit = await admin_client.get("/api/v1/admin/audit", params={"event_type": "model.updated"})
    assert audit.status_code == 200
    details = audit.json()["items"][0]["details"]
    assert details["key_rotated"] is True
    assert "provider-key" not in str(details)


async def test_operator_can_select_models_but_cannot_manage_them(operator_client) -> None:
    assert (await operator_client.get("/api/v1/models")).status_code == 200
    create = await operator_client.post(
        "/api/v1/models",
        json={
            "name": "Forbidden",
            "provider": "mock",
            "model_id": "mock-v1",
            "capabilities": ["reference_to_image"],
        },
    )
    assert create.status_code == 403
