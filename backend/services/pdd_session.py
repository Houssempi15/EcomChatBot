"""
拼多多会话状态管理 — AI / 人工 模式切换（Redis 存储）
"""
import redis.asyncio as aioredis

from core.config import settings

HUMAN_MODE_KEY = "pdd:human_mode:{conversation_id}"
HUMAN_MODE_TTL = 3600 * 8  # 8小时后自动恢复 AI 模式


class PddSessionManager:
    """管理拼多多会话的 AI/人工 模式状态"""

    def __init__(self):
        self.redis: aioredis.Redis = aioredis.from_url(
            settings.redis_url_str,
            encoding="utf-8",
            decode_responses=False,
        )

    def _key(self, conversation_id: str) -> str:
        return HUMAN_MODE_KEY.format(conversation_id=conversation_id)

    async def set_human_mode(self, conversation_id: str, enabled: bool) -> None:
        key = self._key(conversation_id)
        if enabled:
            await self.redis.set(key, "1", ex=HUMAN_MODE_TTL)
        else:
            await self.redis.delete(key)

    async def is_human_mode(self, conversation_id: str) -> bool:
        val = await self.redis.get(self._key(conversation_id))
        return val is not None
