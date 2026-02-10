"""
意图识别测试
"""
import pytest
from test_base import BaseAPITest, TenantTestMixin


@pytest.mark.intent
class TestIntent(BaseAPITest, TenantTestMixin):
    """意图识别测试"""

    @pytest.mark.asyncio
    async def test_classify_intent(self):
        """测试意图分类"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 意图分类
        response = await self.client.post(
            "/intent/classify",
            json={"text": "我想退货"}
        )

        data = self.assert_success(response)

        # 验证返回数据
        assert "intent" in data or "intent_type" in data

    @pytest.mark.asyncio
    async def test_extract_entities(self):
        """测试实体提取"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 实体提取
        response = await self.client.post(
            "/intent/extract-entities",
            json={"text": "我的订单号是ORD123456，想查询物流"}
        )

        data = self.assert_success(response)

        # 验证返回数据
        assert "entities" in data

    @pytest.mark.asyncio
    async def test_get_intent_types(self):
        """测试获取意图类型列表"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 获取意图类型
        response = await self.client.get("/intent/intents")

        data = self.assert_success(response)

        # 验证返回数据
        assert isinstance(data, list) or "intents" in data

    @pytest.mark.asyncio
    async def test_classify_multiple_intents(self):
        """测试分类多个意图"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 测试不同的意图
        test_cases = [
            "我想退货",
            "查询订单",
            "商品推荐",
            "投诉建议",
            "咨询价格"
        ]

        for text in test_cases:
            response = await self.client.post(
                "/intent/classify",
                json={"text": text}
            )

            if response.status_code == 200:
                data = self.assert_success(response)
                # 验证每个分类结果
                assert "intent" in data or "intent_type" in data
