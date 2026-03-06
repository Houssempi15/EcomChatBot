"""适配器注册表测试"""
from services.platform.adapter_registry import _adapters, get_supported_platforms

# 确保适配器被导入注册
import services.platform.pdd_adapter  # noqa: F401
import services.platform.douyin_adapter  # noqa: F401


def test_adapters_registered():
    assert "pinduoduo" in _adapters
    assert "douyin" in _adapters


def test_get_supported_platforms():
    platforms = get_supported_platforms()
    assert "pinduoduo" in platforms
    assert "douyin" in platforms
