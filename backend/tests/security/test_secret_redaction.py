import pytest


@pytest.mark.asyncio
async def test_secret_never_appears_in_model_response_or_logs(admin_client, caplog) -> None:
    secret = "provider-secret-that-must-not-leak"
    response = await admin_client.post(
        "/api/v1/models",
        json={
            "name": "secret-redaction-model",
            "provider": "generic_http",
            "model_id": "redaction-v1",
            "base_url": "https://provider.invalid",
            "api_key": secret,
            "capabilities": ["reference_to_image"],
        },
    )
    assert response.status_code == 201
    assert secret not in response.text
    assert secret not in caplog.text
