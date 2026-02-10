"""
并发会话测试
"""
import pytest
import asyncio
import time
from test_base import BaseAPITest, TenantTestMixin
from config import settings


@pytest.mark.performance
@pytest.mark.slow
@pytest.mark.skipif(settings.skip_performance, reason="性能测试已跳过")
class TestConcurrentSessions(BaseAPITest, TenantTestMixin):
    """并发会话测试"""

    @pytest.mark.asyncio
    async def test_concurrent_tenant_registration(self):
        """测试并发租户注册"""
        concurrent_count = min(5, settings.max_concurrent // 2)
        print(f"\n并发注册 {concurrent_count} 个租户...")

        async def register_tenant(index):
            tenant_data = self.data_gen.generate_tenant(
                f"{settings.tenant_prefix}perf_{index}_"
            )
            response = await self.client.post(
                "/tenant/register",
                json=tenant_data
            )
            return response

        start_time = time.time()
        tasks = [register_tenant(i) for i in range(concurrent_count)]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        elapsed = end_time - start_time

        # 验证成功数
        success_count = sum(1 for r in responses if r.status_code == 200)

        print(f"✓ 注册成功: {success_count}/{concurrent_count}")
        print(f"✓ 总耗时: {elapsed:.2f}秒")
        print(f"✓ 平均耗时: {elapsed/concurrent_count:.3f}秒/请求")

        # 注册清理
        for response in responses:
            if response.status_code == 200:
                data = response.json()["data"]
                self.cleaner.register_tenant(data["tenant_id"])

        assert success_count >= concurrent_count * 0.9

    @pytest.mark.asyncio
    async def test_concurrent_knowledge_creation(self):
        """测试并发创建知识"""
        # 创建租户
        tenant_info = await self.create_test_tenant()
        self.client.set_api_key(tenant_info["api_key"])

        concurrent_count = min(10, settings.max_concurrent)
        print(f"\n并发创建 {concurrent_count} 条知识...")

        async def create_knowledge(index):
            knowledge_data = self.data_gen.generate_knowledge_item(
                f"分类{index}"
            )
            response = await self.client.post(
                "/knowledge/create",
                json=knowledge_data
            )
            return response

        start_time = time.time()
        tasks = [create_knowledge(i) for i in range(concurrent_count)]
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        elapsed = end_time - start_time

        success_count = sum(1 for r in responses if r.status_code == 200)

        print(f"✓ 创建成功: {success_count}/{concurrent_count}")
        print(f"✓ 总耗时: {elapsed:.2f}秒")
        print(f"✓ 平均耗时: {elapsed/concurrent_count:.3f}秒/请求")
        print(f"✓ QPS: {concurrent_count/elapsed:.2f}")

        # 注册清理
        for response in responses:
            if response.status_code == 200:
                data = response.json()["data"]
                self.cleaner.register_knowledge(data["knowledge_id"])

        assert success_count >= concurrent_count * 0.9
        assert elapsed / concurrent_count < 1.0
