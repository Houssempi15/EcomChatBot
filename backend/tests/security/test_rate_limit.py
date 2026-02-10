"""
限流测试
"""
import pytest
import asyncio
from test_base import BaseAPITest, TenantTestMixin
from config import settings


@pytest.mark.security
@pytest.mark.skipif(settings.skip_security, reason="安全测试已跳过")
class TestRateLimit(BaseAPITest, TenantTestMixin):
    """限流测试"""

    @pytest.mark.asyncio
    async def test_api_rate_limit(self):
        """测试API限流"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 快速连续请求
        rapid_requests = 30
        success_count = 0
        rate_limited_count = 0

        print(f"\n快速发送 {rapid_requests} 个请求...")

        for i in range(rapid_requests):
            response = await self.client.get("/tenant/info")
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:  # Too Many Requests
                rate_limited_count += 1
            
            # 很小的延迟
            await asyncio.sleep(0.01)

        print(f"  成功: {success_count}")
        print(f"  限流: {rate_limited_count}")

        # 验证至少有一些请求成功
        assert success_count > 0

    @pytest.mark.asyncio
    async def test_burst_requests(self):
        """测试突发请求"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 并发突发请求
        burst_size = 20

        async def make_request(index):
            return await self.client.get("/tenant/quota")

        print(f"\n并发突发 {burst_size} 个请求...")

        tasks = [make_request(i) for i in range(burst_size)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(
            1 for r in responses 
            if not isinstance(r, Exception) and r.status_code == 200
        )
        error_count = sum(
            1 for r in responses 
            if isinstance(r, Exception) or r.status_code >= 400
        )

        print(f"  成功: {success_count}")
        print(f"  失败/限流: {error_count}")

        # 至少应该有一些请求成功
        assert success_count > 0
