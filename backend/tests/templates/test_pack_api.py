import pytest


@pytest.mark.asyncio
async def test_list_packs_seeds_immutable_first_party_versions(operator_client) -> None:
    response = await operator_client.get("/api/v1/template-packs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 5
    amazon = next(pack for pack in body if pack["slug"] == "amazon-global")
    assert amazon["version"] == 1
    assert amazon["status"] == "published"
    assert amazon["source"] == "first_party_default"
    assert amazon["rules"]["slots"][0]["allow_text"] is False


@pytest.mark.asyncio
async def test_list_packs_is_idempotent(operator_client) -> None:
    first = await operator_client.get("/api/v1/template-packs")
    second = await operator_client.get("/api/v1/template-packs")
    assert [pack["version_id"] for pack in first.json()] == [
        pack["version_id"] for pack in second.json()
    ]
