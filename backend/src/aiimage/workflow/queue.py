from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError

from aiimage.config import get_settings


class QueueHints:
    queue_name = "aiimage:generation:queued"

    async def publish(self, step_id: UUID) -> bool:
        client = Redis.from_url(get_settings().redis_url)
        try:
            accepted = await client.set(
                f"aiimage:generation:wakeup:{step_id}",
                "1",
                ex=60,
                nx=True,
            )
            if not accepted:
                return True
            await client.lpush(self.queue_name, str(step_id))
            return True
        except RedisConnectionError:
            return False
        finally:
            await client.aclose()

    async def acknowledge(self, step_id: UUID) -> None:
        client = Redis.from_url(get_settings().redis_url)
        try:
            await client.delete(f"aiimage:generation:wakeup:{step_id}")
        except RedisConnectionError:
            return
        finally:
            await client.aclose()


def get_queue_hints() -> QueueHints:
    return QueueHints()
