import pytest
from unittest.mock import AsyncMock, patch
from services.pdd_session import PddSessionManager

@pytest.mark.asyncio
async def test_set_and_get_human_mode():
    """设置人工接管后应返回 True"""
    manager = PddSessionManager()
    with patch.object(manager.redis, "set", new_callable=AsyncMock) as mock_set, \
         patch.object(manager.redis, "get", new_callable=AsyncMock, return_value=b"1"):
        await manager.set_human_mode("conv_123", True)
        result = await manager.is_human_mode("conv_123")
        assert result is True

@pytest.mark.asyncio
async def test_ai_mode_by_default():
    """默认应为 AI 模式"""
    manager = PddSessionManager()
    with patch.object(manager.redis, "get", new_callable=AsyncMock, return_value=None):
        result = await manager.is_human_mode("conv_new")
        assert result is False
