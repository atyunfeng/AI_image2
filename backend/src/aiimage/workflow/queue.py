from uuid import UUID

from redis.asyncio import Redis

from aiimage.config import get_settings


class QueueHints:
    queue_name = "aiimage:generation:queued"

    async def publish(self, step_id: UUID) -> bool:
        client = Redis.from_url(get_settings().redis_url)
        try:
            await client.lpush(self.queue_name, str(step_id))
            return True
        except ConnectionError:
            return False
        finally:
            await client.aclose()


def get_queue_hints() -> QueueHints:
    return QueueHints()

