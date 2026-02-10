"""
监控统计测试
"""
import pytest
from test_base import BaseAPITest, TenantTestMixin, ConversationTestMixin


@pytest.mark.monitor
class TestMonitor(BaseAPITest, TenantTestMixin, ConversationTestMixin):
    """监控统计测试"""

    @pytest.mark.asyncio
    async def test_conversation_statistics(self):
        """测试对话统计"""
        # 创建租户和对话
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 创建几个对话
        for _ in range(3):
            await self.create_test_conversation()

        # 获取对话统计
        response = await self.client.get("/monitor/conversations")
        data = self.assert_success(response)

        # 验证返回数据
        assert "total_conversations" in data or "total" in data

    @pytest.mark.asyncio
    async def test_response_time_statistics(self):
        """测试响应时间统计"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取响应时间统计
        response = await self.client.get("/monitor/response-time")
        data = self.assert_success(response)

        # 验证返回数据
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_satisfaction_statistics(self):
        """测试满意度统计"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 创建并关闭对话（带评分）
        conversation_id = await self.create_test_conversation()
        await self.client.put(
            f"/conversation/{conversation_id}",
            json={
                "status": "closed",
                "satisfaction_score": 5,
                "feedback": "很好"
            }
        )

        # 获取满意度统计
        response = await self.client.get("/monitor/satisfaction")
        data = self.assert_success(response)

        # 验证返回数据
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_dashboard_summary(self):
        """测试Dashboard汇总"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取Dashboard数据
        response = await self.client.get("/monitor/dashboard")
        data = self.assert_success(response)

        # 验证返回数据
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_hourly_trend(self):
        """测试每小时趋势"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取每小时趋势
        response = await self.client.get("/monitor/trend/hourly")

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, (list, dict))

    @pytest.mark.asyncio
    async def test_monitor_with_date_range(self):
        """测试指定日期范围的监控数据"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        import datetime
        end_date = datetime.datetime.now()
        start_date = end_date - datetime.timedelta(days=7)

        # 获取指定日期范围的统计
        response = await self.client.get(
            "/monitor/conversations",
            params={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, dict)
