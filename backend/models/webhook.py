"""
Webhook 模型
"""
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import TenantBaseModel


class WebhookEventType(str, Enum):
    """Webhook 事件类型"""

    # 会话事件
    CONVERSATION_CREATED = "conversation.created"
    CONVERSATION_CLOSED = "conversation.closed"

    # 消息事件
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"

    # 用户事件
    USER_CREATED = "user.created"

    # 订阅事件
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_EXPIRED = "subscription.expired"

    # 配额事件
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"


class WebhookConfig(TenantBaseModel):
    """Webhook 配置表"""

    __tablename__ = "webhook_configs"
    __table_args__ = (
        Index("idx_webhook_tenant", "tenant_id"),
        Index("idx_webhook_event_type", "event_type"),
        Index("idx_webhook_status", "status"),
        {"comment": "Webhook配置表"},
    )

    # 基本信息
    name: Mapped[str] = mapped_column(String(128), nullable=False, comment="名称")
    description: Mapped[str | None] = mapped_column(Text, comment="描述")
    url: Mapped[str] = mapped_column(String(512), nullable=False, comment="Webhook URL")

    # 事件类型
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="事件类型"
    )

    # 安全配置
    secret: Mapped[str | None] = mapped_column(
        String(255), comment="签名密钥（用于验证请求）"
    )

    # 请求配置
    headers: Mapped[str | None] = mapped_column(
        Text, comment="自定义请求头（JSON格式）"
    )
    timeout: Mapped[int] = mapped_column(
        Integer, default=30, comment="请求超时时间（秒）"
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, default=3, comment="重试次数"
    )
    retry_interval: Mapped[int] = mapped_column(
        Integer, default=60, comment="重试间隔（秒）"
    )

    # 状态
    status: Mapped[str] = mapped_column(
        String(16),
        default="active",
        comment="状态(active/inactive/failed)",
    )
    failure_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="连续失败次数"
    )
    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后触发时间"
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="最后成功时间"
    )

    def __repr__(self) -> str:
        return f"<WebhookConfig {self.name} ({self.event_type})>"


class WebhookLog(TenantBaseModel):
    """Webhook 发送日志表"""

    __tablename__ = "webhook_logs"
    __table_args__ = (
        Index("idx_webhook_log_config", "webhook_config_id"),
        Index("idx_webhook_log_tenant", "tenant_id"),
        Index("idx_webhook_log_status", "status"),
        Index("idx_webhook_log_created", "created_at"),
        {"comment": "Webhook发送日志表"},
    )

    # 关联配置
    webhook_config_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("webhook_configs.id", ondelete="CASCADE"),
        nullable=False,
        comment="Webhook配置ID",
    )

    # 事件信息
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="事件类型"
    )
    event_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="事件唯一ID"
    )

    # 请求信息
    request_url: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="请求URL"
    )
    request_headers: Mapped[str | None] = mapped_column(
        Text, comment="请求头（JSON格式）"
    )
    request_body: Mapped[str | None] = mapped_column(Text, comment="请求体")

    # 响应信息
    response_status: Mapped[int | None] = mapped_column(
        Integer, comment="响应状态码"
    )
    response_headers: Mapped[str | None] = mapped_column(
        Text, comment="响应头（JSON格式）"
    )
    response_body: Mapped[str | None] = mapped_column(Text, comment="响应体")

    # 执行信息
    status: Mapped[str] = mapped_column(
        String(16),
        default="pending",
        comment="状态(pending/success/failed/retrying)",
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, default=1, comment="尝试次数"
    )
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")

    # 耗时
    duration_ms: Mapped[int | None] = mapped_column(Integer, comment="请求耗时（毫秒）")

    # 下次重试时间
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime, comment="下次重试时间"
    )

    def __repr__(self) -> str:
        return f"<WebhookLog {self.event_id} ({self.status})>"
