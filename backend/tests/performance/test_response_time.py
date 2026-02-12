"""
响应时间测试
"""
import pytest
import time
from test_base import BaseAPITest, TenantTestMixin, ConversationTestMixin
from config import settings


@pytest.mark.performance
@pytest.mark.skipif(settings.skip_performance, reason="性能测试已跳过")
class TestResponseTime(BaseAPITest, TenantTestMixin, ConversationTestMixin):
    """响应时间测试"""

    @pytest.mark.asyncio
    async def test_tenant_info_response_time(self):
        """测试获取租户信息的响应时间"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 多次请求测量响应时间
        iterations = 10
        times = []

        for _ in range(iterations):
            start_time = time.time()
            response = await self.client.get("/tenant/info")
            end_time = time.time()
            
            self.assert_success(response)
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"\n租户信息查询响应时间:")
        print(f"  平均: {avg_time*1000:.2f}ms")
        print(f"  最小: {min_time*1000:.2f}ms")
        print(f"  最大: {max_time*1000:.2f}ms")
        print(f"  P95:  {p95_time*1000:.2f}ms")

        # 性能断言
        assert avg_time < 0.5  # 平均响应时间 < 500ms
        assert p95_time < 1.0  # P95 < 1s

    @pytest.mark.asyncio
    async def test_conversation_creation_response_time(self):
        """测试创建对话的响应时间"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 多次创建对话测量响应时间
        iterations = 10
        times = []

        for i in range(iterations):
            user_data = self.data_gen.generate_user(i)
            
            start_time = time.time()
            response = await self.client.post(
                "/conversation/create",
                json=user_data
            )
            end_time = time.time()
            
            data = self.assert_success(response)
            self.cleaner.register_conversation(data["conversation_id"])
            
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"\n创建对话响应时间:")
        print(f"  平均: {avg_time*1000:.2f}ms")
        print(f"  P95:  {p95_time*1000:.2f}ms")

        assert avg_time < 0.5
        assert p95_time < 1.0

    @pytest.mark.asyncio
    async def test_knowledge_search_response_time(self):
        """测试知识搜索的响应时间"""
        # 创建租户并导入知识
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        # 批量导入知识
        items = self.data_gen.get_predefined_knowledge()
        await self.client.post(
            "/knowledge/batch-import",
            json={"items": items}
        )

        # 多次搜索测量响应时间
        iterations = 10
        times = []
        queries = ["退货", "配送", "支付", "会员", "保修"]

        for i in range(iterations):
            query = queries[i % len(queries)]
            
            start_time = time.time()
            response = await self.client.post(
                "/knowledge/search",
                json={"query": query, "top_k": 5}
            )
            end_time = time.time()
            
            self.assert_success(response)
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        p95_time = sorted(times)[int(len(times) * 0.95)]

        print(f"\n知识搜索响应时间:")
        print(f"  平均: {avg_time*1000:.2f}ms")
        print(f"  P95:  {p95_time*1000:.2f}ms")

        assert avg_time < 1.0
        assert p95_time < 2.0
