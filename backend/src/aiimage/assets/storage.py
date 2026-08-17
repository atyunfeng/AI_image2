import asyncio
import hashlib
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import boto3

from aiimage.config import get_settings

ALLOWED_ASSET_TYPES = {"image/jpeg", "image/png", "image/webp", "application/zip"}
MAX_ASSET_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class StoredObject:
    object_key: str
    sha256: str
    size_bytes: int
    mime_type: str


class ObjectStore(Protocol):
    async def put(self, *, content: bytes, mime_type: str) -> StoredObject:
        raise NotImplementedError

    async def get(self, *, object_key: str) -> bytes:
        raise NotImplementedError


def describe_object(*, content: bytes, mime_type: str) -> StoredObject:
    if mime_type not in ALLOWED_ASSET_TYPES:
        raise ValueError(f"Unsupported asset MIME type: {mime_type}")
    if not content or len(content) > MAX_ASSET_BYTES:
        raise ValueError("Asset must be between 1 byte and 100 MiB")
    digest = hashlib.sha256(content).hexdigest()
    return StoredObject(
        object_key=f"sha256/{digest[:2]}/{digest}",
        sha256=digest,
        size_bytes=len(content),
        mime_type=mime_type,
    )


class InMemoryObjectStore:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    async def put(self, *, content: bytes, mime_type: str) -> StoredObject:
        stored = describe_object(content=content, mime_type=mime_type)
        self.objects.setdefault(stored.object_key, content)
        return stored

    async def get(self, *, object_key: str) -> bytes:
        return self.objects[object_key]


class S3ObjectStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            region_name="us-east-1",
        )

    async def put(self, *, content: bytes, mime_type: str) -> StoredObject:
        stored = describe_object(content=content, mime_type=mime_type)
        await asyncio.to_thread(self._ensure_bucket)
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=stored.object_key,
            Body=content,
            ContentType=mime_type,
        )
        return stored

    async def get(self, *, object_key: str) -> bytes:
        response = await asyncio.to_thread(
            self.client.get_object,
            Bucket=self.bucket,
            Key=object_key,
        )
        return await asyncio.to_thread(response["Body"].read)

    def _ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except self.client.exceptions.ClientError:
            self.client.create_bucket(Bucket=self.bucket)


@lru_cache
def get_object_store() -> ObjectStore:
    return S3ObjectStore()
