import pytest

from aiimage.assets.models import Asset, ImmutableAssetError


def test_asset_content_is_not_updated() -> None:
    asset = Asset(
        object_key="sha256/ab/abcdef",
        sha256="abcdef",
        size_bytes=3,
        mime_type="image/png",
    )

    with pytest.raises(ImmutableAssetError):
        asset.replace_content(b"new")

