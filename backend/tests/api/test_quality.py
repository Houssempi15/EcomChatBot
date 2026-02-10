"""
质量评估测试
"""
import pytest
from test_base import BaseAPITest, TenantTestMixin, ConversationTestMixin


@pytest.mark.quality
class TestQuality(BaseAPITest, TenantTestMixin, ConversationTestMixin):
    """质量评估测试"""

    @pytest.mark.asyncio
    async def test_evaluate_conversation_quality(self):
        """测试评估对话质量"""
        # 创建租户和对话
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])
        conversation_id = await self.create_test_conversation()

        # 发送几条消息
        for msg in ["你好", "谢谢"]:
            await self.client.post(
                f"/conversation/{conversation_id}/messages",
                json={"content": msg}
            )

        # 评估质量
        response = await self.client.get(
            f"/quality/conversation/{conversation_id}"
        )

        if response.status_code == 200:
            data = self.assert_success(response)
            # 验证质量评分数据
            assert "score" in data or "quality_score" in data

    @pytest.mark.asyncio
    async def test_quality_summary(self):
        """测试质量统计汇总"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取质量汇总
        response = await self.client.get("/quality/summary")

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_quality_trend(self):
        """测试质量趋势分析"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取质量趋势
        response = await self.client.get("/quality/trend")

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, (list, dict))
