"""
数据分析测试
"""
import pytest
from test_base import BaseAPITest, TenantTestMixin


@pytest.mark.analytics
class TestAnalytics(BaseAPITest, TenantTestMixin):
    """数据分析测试"""

    @pytest.mark.asyncio
    async def test_get_analytics_data(self):
        """测试获取分析数据"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取分析数据
        response = await self.client.get("/analytics")

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_get_conversation_analytics(self):
        """测试获取对话分析"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取对话分析
        response = await self.client.get("/analytics/conversations")

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, dict)
