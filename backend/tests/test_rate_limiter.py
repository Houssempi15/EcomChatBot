"""速率限制器测试"""
from services.platform.rate_limiter import PLATFORM_LIMITS, RateLimiter


def test_platform_limits_defined():
    assert "pinduoduo" in PLATFORM_LIMITS
    assert "douyin" in PLATFORM_LIMITS
    assert "taobao" in PLATFORM_LIMITS
    assert "jd" in PLATFORM_LIMITS
    assert "kuaishou" in PLATFORM_LIMITS


def test_platform_limits_structure():
    for platform, limits in PLATFORM_LIMITS.items():
        assert "calls_per_second" in limits
        assert "calls_per_minute" in limits
        assert limits["calls_per_second"] > 0
        assert limits["calls_per_minute"] > 0
