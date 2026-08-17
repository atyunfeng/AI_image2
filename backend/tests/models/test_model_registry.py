async def test_api_key_is_write_only(admin_client) -> None:
    response = await admin_client.post(
        "/api/v1/models",
        json={
            "name": "Mock Image",
            "provider": "mock",
            "model_id": "mock-v1",
            "api_key": "secret-provider-key",
            "capabilities": ["reference_to_image"],
        },
    )

    assert response.status_code == 201
    assert "secret-provider-key" not in response.text
    assert response.json()["key_suffix"] == "-key"
    assert response.json()["has_key"] is True

