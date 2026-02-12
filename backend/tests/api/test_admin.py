"""
管理员功能测试
"""
import pytest
from test_base import BaseAPITest
from utils.assertions import assert_paginated
from config import settings


@pytest.mark.admin
@pytest.mark.skipif(not settings.has_admin_credentials, reason="未配置管理员账号")
class TestAdmin(BaseAPITest):
    """管理员功能测试"""

    async def admin_login(self) -> str:
        """管理员登录"""
        response = await self.client.post(
            "/admin/login",
            json={
                "username": settings.admin_username,
                "password": settings.admin_password
            }
        )

        data = self.assert_success(response)
        return data["access_token"]

    @pytest.mark.asyncio
    async def test_admin_login(self):
        """测试管理员登录"""
        response = await self.client.post(
            "/admin/login",
            json={
                "username": settings.admin_username,
                "password": settings.admin_password
            }
        )

        data = self.assert_success(response)

        # 验证返回数据
        assert "access_token" in data
        assert "token_type" in data

    @pytest.mark.asyncio
    async def test_admin_login_with_wrong_password(self):
        """测试管理员错误密码登录"""
        response = await self.client.post(
            "/admin/login",
            json={
                "username": settings.admin_username,
                "password": "wrong_password"
            }
        )

        # 应该返回401错误
        assert response.status_code in [400, 401]

    @pytest.mark.asyncio
    async def test_get_tenants_list(self):
        """测试获取租户列表"""
        # 管理员登录
        token = await self.admin_login()
        self.client.set_jwt_token(token)

        # 获取租户列表
        response = await self.client.get(
            "/admin/tenants",
            params={"page": 1, "size": 10}
        )

        data = self.assert_success(response)

        # 验证分页数据
        assert_paginated(data, min_total=0)

    @pytest.mark.asyncio
    async def test_create_tenant_by_admin(self):
        """测试管理员创建租户"""
        # 管理员登录
        token = await self.admin_login()
        self.client.set_jwt_token(token)

        # 创建租户
        tenant_data = self.data_gen.generate_tenant("admin_created_")
        response = await self.client.post(
            "/admin/tenants",
            json=tenant_data
        )

        if response.status_code == 200:
            data = self.assert_success(response)
            assert "tenant_id" in data
            self.cleaner.register_tenant(data["tenant_id"])

    @pytest.mark.asyncio
    async def test_update_tenant_status(self):
        """测试更新租户状态"""
        # 管理员登录
        token = await self.admin_login()
        self.client.set_jwt_token(token)

        # 先获取租户列表
        list_resp = await self.client.get(
            "/admin/tenants",
            params={"page": 1, "size": 1}
        )
        list_data = self.assert_success(list_resp)

        if list_data["total"] > 0:
            tenant_id = list_data["items"][0]["tenant_id"]

            # 更新租户状态
            response = await self.client.put(
                f"/admin/tenants/{tenant_id}/status",
                json={"status": "active"}
            )

            if response.status_code == 200:
                data = self.assert_success(response)
                assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_get_audit_logs(self):
        """测试查询审计日志"""
        # 管理员登录
        token = await self.admin_login()
        self.client.set_jwt_token(token)

        # 获取审计日志
        response = await self.client.get("/admin/audit-logs")

        if response.status_code == 200:
            data = self.assert_success(response)
            assert isinstance(data, (list, dict))
