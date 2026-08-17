from httpx import ASGITransport, AsyncClient

from aiimage.api.main import create_app


async def test_login_returns_bearer_token(authenticated_app) -> None:
    transport = ASGITransport(app=authenticated_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "admin@aiimage.local",
                "password": "LocalOnly-ChangeMe-2026",
            },
        )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"


async def test_me_rejects_anonymous() -> None:
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_admin_endpoint_rejects_operator(operator_client: AsyncClient) -> None:
    response = await operator_client.get("/api/v1/auth/admin-check")
    assert response.status_code == 403

