"""
Webhook Schema
"""
from datetime import datetime

from pydantic import Field, HttpUrl

from schemas.base import BaseSchema, TimestampSchema


# ============ Webhook 配置 Schema ============
class WebhookConfigBase(BaseSchema):
    """Webhook 配置基础 Schema"""

    name: str = Field(..., min_length=1, max_length=128, description="名称")
    description: str | None = Field(None, max_length=1024, description="描述")
    url: HttpUrl = Field(..., description="Webhook URL")
    event_type: str = Field(..., description="事件类型")


class WebhookConfigCreate(WebhookConfigBase):
    """创建 Webhook 配置"""

    secret: str | None = Field(None, max_length=255, description="签名密钥")
    headers: dict | None = Field(None, description="自定义请求头")
    timeout: int = Field(30, ge=1, le=300, description="请求超时时间（秒）")
    retry_count: int = Field(3, ge=0, le=10, description="重试次数")
    retry_interval: int = Field(60, ge=10, le=3600, description="重试间隔（秒）")


class WebhookConfigUpdate(BaseSchema):
    """更新 Webhook 配置"""

    name: str | None = Field(None, min_length=1, max_length=128)
    description: str | None = None
    url: HttpUrl | None = None
    event_type: str | None = None
    secret: str | None = None
    headers: dict | None = None
    timeout: int | None = Field(None, ge=1, le=300)
    retry_count: int | None = Field(None, ge=0, le=10)
    retry_interval: int | None = Field(None, ge=10, le=3600)
    status: str | None = Field(None, pattern="^(active|inactive)$")


class WebhookConfigResponse(WebhookConfigBase, TimestampSchema):
    """Webhook 配置响应"""

    id: int
    tenant_id: str
    timeout: int
    retry_count: int
    retry_interval: int
    status: str
    failure_count: int
    last_triggered_at: datetime | None
    last_success_at: datetime | None


# ============ Webhook 日志 Schema ============
class WebhookLogResponse(TimestampSchema):
    """Webhook 日志响应"""

    id: int
    webhook_config_id: int
    tenant_id: str
    event_type: str
    event_id: str
    request_url: str
    response_status: int | None
    status: str
    attempt_count: int
    error_message: str | None
    duration_ms: int | None


class WebhookLogDetailResponse(WebhookLogResponse):
    """Webhook 日志详情响应"""

    request_headers: dict | None
    request_body: dict | None
    response_headers: dict | None
    response_body: str | None
    next_retry_at: datetime | None


# ============ Webhook 测试 Schema ============
class WebhookTestRequest(BaseSchema):
    """Webhook 测试请求"""

    payload: dict | None = Field(None, description="测试负载数据")


class WebhookTestResponse(BaseSchema):
    """Webhook 测试响应"""

    success: bool
    status_code: int | None
    response_time_ms: int | None
    response_body: str | None
    error_message: str | None


# ============ 事件类型 Schema ============
class EventTypeInfo(BaseSchema):
    """事件类型信息"""

    value: str
    name: str
    description: str


class WebhookEventTypesResponse(BaseSchema):
    """Webhook 事件类型响应"""

    event_types: list[EventTypeInfo]
