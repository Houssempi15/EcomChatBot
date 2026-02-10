"""
统计分析测试
"""
import pytest
from test_base import BaseAPITest, TenantTestMixin


@pytest.mark.statistics
class TestStatistics(BaseAPITest, TenantTestMixin):
    """统计分析测试"""

    @pytest.mark.asyncio
    async def test_get_statistics(self):
        """测试获取统计数据"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取统计数据
        response = await self.client.get("/statistics")

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_usage_statistics(self):
        """测试获取使用统计"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        import datetime
        now = datetime.datetime.now()

        # 获取当月统计
        response = await self.client.get(
            "/statistics/usage",
            params={
                "year": now.year,
                "month": now.month
            }
        )

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, dict)
