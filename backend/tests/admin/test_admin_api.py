from httpx import AsyncClient


async def test_admin_manages_users_without_exposing_credentials(admin_client: AsyncClient) -> None:
    created = await admin_client.post(
        "/api/v1/admin/users",
        json={
            "email": "designer@aiimage.local",
            "password": "Designer-Password-2026",
            "roles": ["designer"],
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body["email"] == "designer@aiimage.local"
    assert body["roles"] == ["designer"]
    assert "password" not in body
    assert "password_hash" not in body

    updated = await admin_client.patch(
        f"/api/v1/admin/users/{body['id']}",
        json={"roles": ["operator", "designer"], "is_active": False},
    )
    assert updated.status_code == 200
    assert updated.json()["roles"] == ["designer", "operator"]
    assert updated.json()["is_active"] is False

    users = await admin_client.get("/api/v1/admin/users")
    assert users.status_code == 200
    assert {user["email"] for user in users.json()} == {
        "admin@aiimage.local",
        "designer@aiimage.local",
    }


async def test_operator_cannot_use_admin_governance(operator_client: AsyncClient) -> None:
    assert (await operator_client.get("/api/v1/admin/users")).status_code == 403
    assert (await operator_client.get("/api/v1/admin/audit")).status_code == 403


async def test_final_active_admin_cannot_be_disabled(admin_client: AsyncClient) -> None:
    users = (await admin_client.get("/api/v1/admin/users")).json()
    admin = next(user for user in users if user["email"] == "admin@aiimage.local")

    response = await admin_client.patch(
        f"/api/v1/admin/users/{admin['id']}",
        json={"is_active": False},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "The final active administrator cannot be disabled"


async def test_admin_reads_paginated_redacted_audit_events(admin_client: AsyncClient) -> None:
    await admin_client.post(
        "/api/v1/admin/users",
        json={
            "email": "reviewer@aiimage.local",
            "password": "Reviewer-Password-2026",
            "roles": ["reviewer"],
        },
    )

    response = await admin_client.get(
        "/api/v1/admin/audit",
        params={"event_type": "user.created", "limit": 10},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 1
    assert body["items"][0]["event_type"] == "user.created"
    assert "password" not in str(body).lower()
