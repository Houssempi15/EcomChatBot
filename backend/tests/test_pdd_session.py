import pytest
from unittest.mock import AsyncMock, MagicMock
from services.pdd_session import PddSessionManager

@pytest.mark.asyncio
async def test_set_and_get_human_mode():
    """设置人工接管后应返回 True"""
    mock_redis = MagicMock()
    mock_redis.set = AsyncMock()
    mock_redis.get = AsyncMock(return_value="1")
    manager = PddSessionManager(redis=mock_redis)
    await manager.set_human_mode("conv_123", True)
    result = await manager.is_human_mode("conv_123")
    assert result is True

@pytest.mark.asyncio
async def test_ai_mode_by_default():
    """默认应为 AI 模式"""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    manager = PddSessionManager(redis=mock_redis)
    result = await manager.is_human_mode("conv_new")
    assert result is False
