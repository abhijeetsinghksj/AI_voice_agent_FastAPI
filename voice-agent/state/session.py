import json

import redis.asyncio as redis


class SessionStore:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def append_turn(self, session_id: str, role: str, content: str):
        key = f"session:{session_id}:history"
        await self.redis.rpush(key, json.dumps({"role": role, "content": content}))
        await self.redis.expire(key, 3600)

    async def get_history(self, session_id: str) -> list[dict]:
        key = f"session:{session_id}:history"
        rows = await self.redis.lrange(key, 0, -1)
        return [json.loads(r) for r in rows]
