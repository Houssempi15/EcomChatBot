"""
Webhook API 路由
"""
from fastapi import APIRouter, Query

from api.dependencies import DBDep, TenantDep
from schemas import ApiResponse, PaginatedResponse
from schemas.webhook import (
    EventTypeInfo,
    WebhookConfigCreate,
    WebhookConfigResponse,
    WebhookConfigUpdate,
    WebhookEventTypesResponse,
    WebhookLogDetailResponse,
    WebhookLogResponse,
    WebhookTestRequest,
    WebhookTestResponse,
)
from services.webhook.events import get_event_type_info
from services.webhook_service import WebhookService

router = APIRouter(prefix="/webhooks", tags=["Webhook"])


@router.get("/event-types", response_model=ApiResponse[WebhookEventTypesResponse])
async def get_event_types():
    """
    获取所有可用的事件类型

    返回所有支持的 Webhook 事件类型及其描述
    """
    event_types = get_event_type_info()
    response = WebhookEventTypesResponse(
        event_types=[EventTypeInfo(**et) for et in event_types]
    )
    return ApiResponse(data=response)


@router.post("", response_model=ApiResponse[WebhookConfigResponse])
async def create_webhook(
    webhook_data: WebhookConfigCreate,
    tenant_id: TenantDep,
    db: DBDep,
):
    """
    创建 Webhook 配置

    创建新的 Webhook 配置，用于接收指定事件的通知
    """
    service = WebhookService(db)
    webhook = await service.create_webhook(tenant_id, webhook_data)
    return ApiResponse(data=webhook)


@router.get("", response_model=ApiResponse[PaginatedResponse[WebhookConfigResponse]])
async def list_webhooks(
    tenant_id: TenantDep,
    db: DBDep,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    event_type: str | None = Query(None, description="事件类型筛选"),
    status: str | None = Query(None, pattern="^(active|inactive|failed)$"),
):
    """
    获取 Webhook 列表

    分页查询当前租户的所有 Webhook 配置
    """
    service = WebhookService(db)
    webhooks, total = await service.list_webhooks(
        tenant_id=tenant_id,
        page=page,
        size=size,
        event_type=event_type,
        status=status,
    )

    paginated = PaginatedResponse.create(
        items=webhooks,
        total=total,
        page=page,
        size=size,
    )
    return ApiResponse(data=paginated)


@router.get("/{webhook_id}", response_model=ApiResponse[WebhookConfigResponse])
async def get_webhook(
    webhook_id: int,
    tenant_id: TenantDep,
    db: DBDep,
):
    """
    获取 Webhook 详情

    获取指定 Webhook 配置的详细信息
    """
    service = WebhookService(db)
    webhook = await service.get_webhook(webhook_id, tenant_id)
    return ApiResponse(data=webhook)


@router.put("/{webhook_id}", response_model=ApiResponse[WebhookConfigResponse])
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookConfigUpdate,
    tenant_id: TenantDep,
    db: DBDep,
):
    """
    更新 Webhook 配置

    更新指定 Webhook 的配置信息
    """
    service = WebhookService(db)
    webhook = await service.update_webhook(webhook_id, tenant_id, webhook_data)
    return ApiResponse(data=webhook)


@router.delete("/{webhook_id}", response_model=ApiResponse[dict])
async def delete_webhook(
    webhook_id: int,
    tenant_id: TenantDep,
    db: DBDep,
):
    """
    删除 Webhook 配置

    删除指定的 Webhook 配置及其所有日志
    """
    service = WebhookService(db)
    await service.delete_webhook(webhook_id, tenant_id)
    return ApiResponse(data={"message": "删除成功"})


@router.post("/{webhook_id}/test", response_model=ApiResponse[WebhookTestResponse])
async def test_webhook(
    webhook_id: int,
    tenant_id: TenantDep,
    db: DBDep,
    test_data: WebhookTestRequest | None = None,
):
    """
    测试 Webhook 推送

    向指定 Webhook URL 发送测试请求，验证配置是否正确
    """
    service = WebhookService(db)
    payload = test_data.payload if test_data else None
    result = await service.test_webhook(webhook_id, tenant_id, payload)

    response = WebhookTestResponse(
        success=result["success"],
        status_code=result.get("status_code"),
        response_time_ms=result.get("response_time_ms"),
        response_body=result.get("response_body"),
        error_message=result.get("error_message"),
    )
    return ApiResponse(data=response)


@router.get(
    "/{webhook_id}/logs",
    response_model=ApiResponse[PaginatedResponse[WebhookLogResponse]],
)
async def get_webhook_logs(
    webhook_id: int,
    tenant_id: TenantDep,
    db: DBDep,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None, pattern="^(pending|success|failed|retrying)$"),
):
    """
    获取 Webhook 日志

    分页查询指定 Webhook 的发送日志
    """
    service = WebhookService(db)
    logs, total = await service.get_webhook_logs(
        webhook_id=webhook_id,
        tenant_id=tenant_id,
        page=page,
        size=size,
        status=status,
    )

    paginated = PaginatedResponse.create(
        items=logs,
        total=total,
        page=page,
        size=size,
    )
    return ApiResponse(data=paginated)


@router.get(
    "/{webhook_id}/logs/{log_id}",
    response_model=ApiResponse[WebhookLogDetailResponse],
)
async def get_webhook_log_detail(
    webhook_id: int,
    log_id: int,
    tenant_id: TenantDep,
    db: DBDep,
):
    """
    获取 Webhook 日志详情

    获取指定日志的详细信息，包括请求和响应内容
    """
    # 验证 webhook 属于当前租户
    service = WebhookService(db)
    await service.get_webhook(webhook_id, tenant_id)

    log = await service.get_webhook_log_detail(log_id, tenant_id)
    return ApiResponse(data=log)
