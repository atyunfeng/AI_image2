import asyncio
from uuid import UUID

from redis.asyncio import Redis

from aiimage.assets.storage import get_object_store
from aiimage.config import get_settings
from aiimage.db import get_database
from aiimage.providers.registry import ProviderRegistry
from aiimage.worker.executor import WorkerContext, execute_step
from aiimage.worker.recovery import recover_generation_steps
from aiimage.workflow.queue import QueueHints


async def run_worker() -> None:
    settings = get_settings()
    database = get_database()
    queue = QueueHints()
    redis = Redis.from_url(settings.redis_url)
    context = WorkerContext(
        session_factory=database.session_factory,
        object_store=get_object_store(),
        provider_registry=ProviderRegistry(secret_key_base64=settings.secret_key_base64),
    )
    try:
        await recover_generation_steps(database.session_factory, queue)
        while True:
            item = await redis.brpop(queue.queue_name, timeout=30)
            if item is not None:
                await execute_step(UUID(item[1].decode()), "worker-1", context)
            await recover_generation_steps(database.session_factory, queue)
    finally:
        await redis.aclose()
        await database.dispose()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
