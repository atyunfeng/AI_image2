async def test_admin_authors_versions_and_publishes_immutably(admin_client) -> None:
    created = await admin_client.post(
        "/api/v1/template-packs",
        json={"slug": "brand-editorial", "name": "Editorial", "kind": "brand", "rules": {"tone": "warm"}},
    )
    assert created.status_code == 201, created.text
    pack = created.json()
    assert pack["versions"][0]["status"] == "draft"

    published = await admin_client.post(
        f"/api/v1/template-pack-versions/{pack['versions'][0]['id']}/publish"
    )
    assert published.status_code == 200
    assert published.json()["status"] == "published"

    copied = await admin_client.post(
        f"/api/v1/template-packs/{pack['id']}/versions",
        json={"source_version_id": pack["versions"][0]["id"], "rules": {"tone": "cool"}},
    )
    assert copied.status_code == 201
    assert copied.json()["version"] == 2
    assert copied.json()["status"] == "draft"

    managed = (await admin_client.get("/api/v1/template-packs/manage")).json()
    editorial = next(item for item in managed if item["slug"] == "brand-editorial")
    assert [version["version"] for version in editorial["versions"]] == [2, 1]
    assert editorial["versions"][1]["rules"] == {"tone": "warm"}


async def test_pack_slug_is_unique_and_management_is_protected(admin_client, operator_client) -> None:
    payload = {"slug": "unique-pack", "name": "One", "kind": "category", "rules": {}}
    assert (await admin_client.post("/api/v1/template-packs", json=payload)).status_code == 201
    assert (await admin_client.post("/api/v1/template-packs", json=payload)).status_code == 409
    assert (await operator_client.get("/api/v1/template-packs/manage")).status_code == 403
