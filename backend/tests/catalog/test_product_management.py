from io import BytesIO

from openpyxl import Workbook

from aiimage.bulk.service import parse_import


async def test_product_lifecycle_and_truth_anchor_versions(admin_client) -> None:
    created = await admin_client.post(
        "/api/v1/products",
        json={
            "sku": "LIFE-001",
            "name": "Original",
            "category": "apparel",
            "brand": "North",
        },
    )
    assert created.status_code == 201
    product_id = created.json()["id"]

    updated = await admin_client.patch(
        f"/api/v1/products/{product_id}",
        json={"name": "Updated", "category": "shoes", "brand": "South"},
    )
    assert updated.status_code == 200
    assert updated.json()["brand"] == "South"

    anchor = await admin_client.post(
        f"/api/v1/products/{product_id}/truth-anchors",
        json={"document": {"primary_color": "#102030", "material": "leather"}},
    )
    assert anchor.status_code == 201
    assert anchor.json()["version"] == 2

    detail = (await admin_client.get(f"/api/v1/products/{product_id}")).json()
    assert detail["latest_truth_anchor"]["version"] == 2
    assert [item["version"] for item in detail["truth_anchors"]] == [2, 1]
    assert detail["history"]["generations"] == 0

    archived = await admin_client.delete(f"/api/v1/products/{product_id}")
    assert archived.status_code == 204
    products = (await admin_client.get("/api/v1/products")).json()
    assert all(item["id"] != product_id for item in products)
    assert (await admin_client.get(f"/api/v1/products/{product_id}")).status_code == 404


def test_parse_xlsx_uses_same_row_contract_as_csv() -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["sku", "name", "category", "platform_slug", "reference_asset_id"])
    sheet.append(["shoe-9", "Runner", "shoes", "amazon-us", "asset-id"])
    buffer = BytesIO()
    workbook.save(buffer)

    rows = parse_import("catalog.xlsx", buffer.getvalue())

    assert rows == [
        {
            "sku": "shoe-9",
            "name": "Runner",
            "category": "shoes",
            "platform_slug": "amazon-us",
            "reference_asset_id": "asset-id",
        }
    ]
