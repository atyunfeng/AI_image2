import asyncio
import os
import socket
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
        max_concurrency=settings.worker_max_concurrency,
        provider_concurrency_limits=settings.provider_concurrency_limits,
        max_attempts=settings.worker_max_attempts,
        retry_base_seconds=settings.worker_retry_base_seconds,
    )
    worker_id = f"{socket.gethostname()}-{os.getpid()}"
    running: set[asyncio.Task[bool]] = set()
    try:
        await recover_generation_steps(database.session_factory, queue)
        while True:
            await redis.set("aiimage:worker:heartbeat", worker_id, ex=90)
            if len(running) >= settings.worker_max_concurrency:
                done, running = await asyncio.wait(
                    running,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in done:
                    task.result()
            item = await redis.brpop(queue.queue_name, timeout=5)
            if item is not None:
                step_id = UUID(item[1].decode())
                await queue.acknowledge(step_id)
                running.add(asyncio.create_task(execute_step(step_id, worker_id, context)))
            await recover_generation_steps(database.session_factory, queue)
    finally:
        if running:
            await asyncio.gather(*running, return_exceptions=True)
        await redis.delete("aiimage:worker:heartbeat")
        await redis.aclose()
        await database.dispose()


def main() -> None:
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()
