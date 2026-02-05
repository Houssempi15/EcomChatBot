"""
Webhook 管理服务
"""
import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime

import httpx
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core import ResourceNotFoundException
from models.webhook import WebhookConfig, WebhookLog
from schemas.webhook import WebhookConfigCreate, WebhookConfigUpdate

logger = logging.getLogger(__name__)


class WebhookService:
    """Webhook 管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_webhook(
        self,
        tenant_id: str,
        webhook_data: WebhookConfigCreate,
    ) -> WebhookConfig:
        """创建 Webhook 配置"""
        # 生成签名密钥（如果未提供）
        secret = webhook_data.secret or secrets.token_urlsafe(32)

        # 处理自定义请求头
        headers_json = None
        if webhook_data.headers:
            headers_json = json.dumps(webhook_data.headers)

        webhook = WebhookConfig(
            tenant_id=tenant_id,
            name=webhook_data.name,
            description=webhook_data.description,
            url=str(webhook_data.url),
            event_type=webhook_data.event_type,
            secret=secret,
            headers=headers_json,
            timeout=webhook_data.timeout,
            retry_count=webhook_data.retry_count,
            retry_interval=webhook_data.retry_interval,
            status="active",
            failure_count=0,
        )
        self.db.add(webhook)
        await self.db.commit()
        await self.db.refresh(webhook)

        return webhook

    async def get_webhook(
        self,
        webhook_id: int,
        tenant_id: str,
    ) -> WebhookConfig:
        """获取 Webhook 配置"""
        stmt = select(WebhookConfig).where(
            WebhookConfig.id == webhook_id,
            WebhookConfig.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        webhook = result.scalar_one_or_none()

        if not webhook:
            raise ResourceNotFoundException("Webhook", str(webhook_id))

        return webhook

    async def list_webhooks(
        self,
        tenant_id: str,
        page: int = 1,
        size: int = 20,
        event_type: str | None = None,
        status: str | None = None,
    ) -> tuple[list[WebhookConfig], int]:
        """列表查询 Webhook 配置"""
        # 构建查询条件
        conditions = [WebhookConfig.tenant_id == tenant_id]
        if event_type:
            conditions.append(WebhookConfig.event_type == event_type)
        if status:
            conditions.append(WebhookConfig.status == status)

        # 查询总数
        count_stmt = select(func.count(WebhookConfig.id)).where(and_(*conditions))
        total = await self.db.scalar(count_stmt)

        # 分页查询
        stmt = (
            select(WebhookConfig)
            .where(and_(*conditions))
            .order_by(WebhookConfig.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        webhooks = result.scalars().all()

        return list(webhooks), total or 0

    async def update_webhook(
        self,
        webhook_id: int,
        tenant_id: str,
        webhook_data: WebhookConfigUpdate,
    ) -> WebhookConfig:
        """更新 Webhook 配置"""
        webhook = await self.get_webhook(webhook_id, tenant_id)

        # 更新字段
        update_data = webhook_data.model_dump(exclude_unset=True)

        # 处理 URL
        if "url" in update_data and update_data["url"]:
            update_data["url"] = str(update_data["url"])

        # 处理自定义请求头
        if "headers" in update_data:
            if update_data["headers"]:
                update_data["headers"] = json.dumps(update_data["headers"])
            else:
                update_data["headers"] = None

        for field, value in update_data.items():
            setattr(webhook, field, value)

        # 如果从 inactive 切换到 active，重置失败计数
        if webhook_data.status == "active":
            webhook.failure_count = 0

        await self.db.commit()
        await self.db.refresh(webhook)

        return webhook

    async def delete_webhook(
        self,
        webhook_id: int,
        tenant_id: str,
    ) -> None:
        """删除 Webhook 配置"""
        webhook = await self.get_webhook(webhook_id, tenant_id)
        await self.db.delete(webhook)
        await self.db.commit()

    async def test_webhook(
        self,
        webhook_id: int,
        tenant_id: str,
        test_payload: dict | None = None,
    ) -> dict:
        """测试 Webhook 推送"""
        webhook = await self.get_webhook(webhook_id, tenant_id)

        # 构造测试负载
        payload = test_payload or {
            "event_id": f"test_{secrets.token_hex(8)}",
            "event_type": webhook.event_type,
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                "test": True,
                "message": "This is a test webhook",
            },
        }

        # 构造请求头
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "EcomChatBot-Webhook/1.0",
            "X-Webhook-Event": webhook.event_type,
            "X-Webhook-Timestamp": str(int(time.time())),
        }

        # 添加签名
        if webhook.secret:
            payload_str = json.dumps(payload, sort_keys=True)
            signature = hmac.new(
                webhook.secret.encode(),
                payload_str.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"

        # 添加自定义请求头
        if webhook.headers:
            custom_headers = json.loads(webhook.headers)
            headers.update(custom_headers)

        # 发送请求
        start_time = time.time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    webhook.url,
                    json=payload,
                    headers=headers,
                    timeout=webhook.timeout,
                )

            duration_ms = int((time.time() - start_time) * 1000)

            return {
                "success": 200 <= response.status_code < 300,
                "status_code": response.status_code,
                "response_time_ms": duration_ms,
                "response_body": response.text[:1000] if response.text else None,
                "error_message": None,
            }

        except httpx.TimeoutException:
            return {
                "success": False,
                "status_code": None,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "response_body": None,
                "error_message": "请求超时",
            }
        except Exception as e:
            return {
                "success": False,
                "status_code": None,
                "response_time_ms": int((time.time() - start_time) * 1000),
                "response_body": None,
                "error_message": str(e),
            }

    async def get_webhook_logs(
        self,
        webhook_id: int,
        tenant_id: str,
        page: int = 1,
        size: int = 20,
        status: str | None = None,
    ) -> tuple[list[WebhookLog], int]:
        """获取 Webhook 日志"""
        # 验证 Webhook 存在
        await self.get_webhook(webhook_id, tenant_id)

        # 构建查询条件
        conditions = [
            WebhookLog.webhook_config_id == webhook_id,
            WebhookLog.tenant_id == tenant_id,
        ]
        if status:
            conditions.append(WebhookLog.status == status)

        # 查询总数
        count_stmt = select(func.count(WebhookLog.id)).where(and_(*conditions))
        total = await self.db.scalar(count_stmt)

        # 分页查询
        stmt = (
            select(WebhookLog)
            .where(and_(*conditions))
            .order_by(WebhookLog.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        logs = result.scalars().all()

        return list(logs), total or 0

    async def get_webhook_log_detail(
        self,
        log_id: int,
        tenant_id: str,
    ) -> WebhookLog:
        """获取 Webhook 日志详情"""
        stmt = select(WebhookLog).where(
            WebhookLog.id == log_id,
            WebhookLog.tenant_id == tenant_id,
        )
        result = await self.db.execute(stmt)
        log = result.scalar_one_or_none()

        if not log:
            raise ResourceNotFoundException("WebhookLog", str(log_id))

        return log

    async def update_webhook_status(
        self,
        webhook_id: int,
        success: bool,
    ) -> None:
        """
        更新 Webhook 状态（内部使用）

        根据发送结果更新失败计数和最后触发时间
        """
        stmt = select(WebhookConfig).where(WebhookConfig.id == webhook_id)
        result = await self.db.execute(stmt)
        webhook = result.scalar_one_or_none()

        if not webhook:
            return

        webhook.last_triggered_at = datetime.utcnow()

        if success:
            webhook.failure_count = 0
            webhook.last_success_at = datetime.utcnow()
        else:
            webhook.failure_count += 1
            # 连续失败 10 次后自动禁用
            if webhook.failure_count >= 10:
                webhook.status = "failed"
                logger.warning(
                    f"Webhook {webhook_id} disabled due to consecutive failures"
                )

        await self.db.commit()
