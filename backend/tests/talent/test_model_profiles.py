from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from PIL import Image

from aiimage.talent.models import ModelProfile
from aiimage.talent.schemas import ModelProfileCreate
from aiimage.talent.service import (
    ModelProfileValidationError,
    authorization_is_current,
    validate_authorization,
)


def test_system_model_requires_not_required_authorization() -> None:
    today = datetime.now(UTC).date()
    validate_authorization(
        ModelProfileCreate(
            name="系统虚拟模特 A",
            profile_type="system_virtual",
            authorization_status="not_required",
        )
    )
    with pytest.raises(ModelProfileValidationError, match="not_required"):
        validate_authorization(
            ModelProfileCreate(
                name="invalid",
                profile_type="system_virtual",
                authorization_status="valid",
                authorization_expires_on=today + timedelta(days=30),
            )
        )


def test_brand_model_requires_current_authorization() -> None:
    today = datetime.now(UTC).date()
    with pytest.raises(ModelProfileValidationError, match="already be expired"):
        validate_authorization(
            ModelProfileCreate(
                name="expired",
                profile_type="brand_authorized",
                authorization_status="valid",
                authorization_expires_on=today - timedelta(days=1),
            )
        )
    profile = ModelProfile(
        name="brand",
        profile_type="brand_authorized",
        authorization_status="expired",
        authorization_expires_on=today - timedelta(days=1),
        attributes={},
        is_active=True,
    )
    assert not authorization_is_current(profile)


@pytest.mark.asyncio
async def test_create_upload_and_list_system_model(admin_client) -> None:
    created = await admin_client.post(
        "/api/v1/model-profiles",
        json={
            "name": "系统虚拟模特 A",
            "profile_type": "system_virtual",
            "authorization_status": "not_required",
            "attributes": {"presentation": "neutral", "style": "studio"},
        },
    )
    assert created.status_code == 201, created.text
    assert created.json()["is_selectable"] is False
    buffer = BytesIO()
    Image.new("RGB", (32, 64), "white").save(buffer, format="PNG")
    uploaded = await admin_client.post(
        f"/api/v1/model-profiles/{created.json()['id']}/references",
        data={"view": "front"},
        files={"file": ("model-front.png", buffer.getvalue(), "image/png")},
    )
    assert uploaded.status_code == 201
    profiles = (await admin_client.get("/api/v1/model-profiles")).json()
    profile = next(item for item in profiles if item["id"] == created.json()["id"])
    assert profile["is_selectable"] is True
    assert profile["references"][0]["view"] == "front"
