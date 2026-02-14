"""
测试基类
"""
import pytest
from typing import Dict, Any, Optional

from utils import APIClient, assert_success, assert_error
from utils.test_data import TestDataGenerator
from utils.cleanup import cleaner
from config import settings


class BaseAPITest:
    """API测试基类"""

    @pytest.fixture(autouse=True)
    async def setup(self, client: APIClient):
        """每个测试前的准备"""
        self.client = client
        self.data_gen = TestDataGenerator()
        self.cleaner = cleaner

    def assert_success(self, response, status_code: int = 200, message: Optional[str] = None):
        """断言响应成功"""
        return assert_success(response, status_code, message)

    def assert_error(
        self,
        response,
        expected_status: int = 400,
        expected_code: Optional[str] = None,
        message: Optional[str] = None
    ):
        """断言响应错误"""
        return assert_error(response, expected_status, expected_code, message)


class TenantTestMixin:
    """租户测试混入类"""

    async def create_test_tenant(self) -> Dict[str, Any]:
        """创建测试租户并返回租户信息"""
        # 生成租户数据
        tenant_data = self.data_gen.generate_tenant(settings.tenant_prefix)

        # 注册租户
        response = await self.client.post(
            "/tenant/register",
            json=tenant_data
        )

        data = self.assert_success(response)

        # 注册清理
        self.cleaner.register_tenant(data["tenant_id"])

        return {
            "tenant_id": data["tenant_id"],
            "api_key": data["api_key"],
            "email": tenant_data["contact_email"],
            "password": tenant_data["password"],
        }

    async def login_tenant(self, email: str, password: str) -> str:
        """租户登录并返回JWT Token"""
        response = await self.client.post(
            "/tenant/login",
            json={"email": email, "password": password}
        )

        data = self.assert_success(response)
        return data["access_token"]


class ConversationTestMixin:
    """对话测试混入类"""

    async def create_test_conversation(self, user_id: Optional[str] = None) -> str:
        """创建测试对话并返回conversation_id"""
        user_data = self.data_gen.generate_user()
        if user_id:
            user_data["user_id"] = user_id

        response = await self.client.post(
            "/conversation/create",
            json=user_data
        )

        data = self.assert_success(response)
        conversation_id = data["conversation_id"]

        # 注册清理
        self.cleaner.register_conversation(conversation_id)

        return conversation_id


class KnowledgeTestMixin:
    """知识库测试混入类"""

    async def create_test_knowledge(self, category: str = "测试分类") -> str:
        """创建测试知识条目并返回knowledge_id"""
        knowledge_data = self.data_gen.generate_knowledge_item(category)

        response = await self.client.post(
            "/knowledge/create",
            json=knowledge_data
        )

        data = self.assert_success(response)
        knowledge_id = data["knowledge_id"]

        # 注册清理
        self.cleaner.register_knowledge(knowledge_id)

        return knowledge_id

    async def batch_create_knowledge(self, count: int = 5) -> list:
        """批量创建知识条目"""
        items = self.data_gen.generate_knowledge_batch(count)

        response = await self.client.post(
            "/knowledge/batch-import",
            json={"items": items}
        )

        data = self.assert_success(response)

        # 注册清理
        for item in data.get("created", []):
            self.cleaner.register_knowledge(item["knowledge_id"])

        return data


class ModelConfigTestMixin:
    """模型配置测试混入类"""

    async def create_test_model_config(
        self,
        provider: str = "zhipuai",
        api_key: Optional[str] = None
    ) -> str:
        """创建测试模型配置并返回config_id"""
        if api_key is None:
            if provider == "zhipuai":
                api_key = settings.zhipuai_api_key
            elif provider == "openai":
                api_key = settings.openai_api_key
            elif provider == "deepseek":
                api_key = settings.deepseek_api_key

        config_data = self.data_gen.generate_model_config(provider, api_key)

        response = await self.client.post(
            "/models",
            json=config_data
        )

        data = self.assert_success(response)
        config_id = data["id"]

        # 注册清理
        self.cleaner.register_model_config(config_id)

        return config_id
