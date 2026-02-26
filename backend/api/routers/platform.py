"""
平台对接 API 路由
"""
import logging

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import DBDep, TenantTokenDep
from core.crypto import decrypt_field, encrypt_field
from models.platform import PlatformConfig
from schemas.platform import PlatformConfigCreate, PlatformConfigResponse, PinduoduoWebhookPayload
from services.platform.pinduoduo_client import PinduoduoClient
from services.platform.platform_message_service import PlatformMessageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/platform", tags=["平台对接"])

PDD_AUTH_URL = "https://mms.pinduoduo.com/open.html"
PDD_TOKEN_URL = "https://open-api.pinduoduo.com/oauth/token"


# ---------------------------------------------------------------------------
# Webhook（无需认证）
# ---------------------------------------------------------------------------

@router.post("/pinduoduo/webhook", summary="接收拼多多消息推送", include_in_schema=False)
async def pinduoduo_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DBDep,
    pdd_sign: str | None = Header(None, alias="pdd-sign"),
):
    """接收拼多多 Webhook 推送，验签后异步处理"""
    body = await request.body()

    try:
        payload_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="无效的请求体")

    # 验签：解析 shop_id → 查 config → 解密 secret → 验签
    shop_id = str(payload_data.get("shop_id", ""))
    if pdd_sign and shop_id:
        stmt = select(PlatformConfig).where(
            and_(
                PlatformConfig.platform_type == "pinduoduo",
                PlatformConfig.shop_id == shop_id,
                PlatformConfig.is_active == True,
            )
        )
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()

        if config and config.app_secret:
            try:
                plain_secret = decrypt_field(config.app_secret)
            except Exception:
                plain_secret = config.app_secret  # 兼容未加密的旧数据
            client = PinduoduoClient(config.app_key, plain_secret)
            if not client.verify_webhook_signature(body, pdd_sign):
                raise HTTPException(status_code=401, detail="Webhook 签名验证失败")
        else:
            # 未找到配置时拒绝带签名的请求
            if pdd_sign:
                raise HTTPException(status_code=401, detail="未找到对应的平台配置")

    service = PlatformMessageService(db)
    background_tasks.add_task(service.handle_pinduoduo_webhook, payload_data)

    return {"success": True}


# ---------------------------------------------------------------------------
# OAuth 授权（JWT 认证）
# ---------------------------------------------------------------------------

@router.get("/pinduoduo/auth", summary="跳转拼多多 OAuth 授权")
async def pinduoduo_auth(
    tenant_id: TenantTokenDep,
    app_key: str,
    redirect_uri: str,
):
    """重定向到拼多多 POP OAuth 授权页"""
    import urllib.parse
    params = {
        "response_type": "code",
        "client_id": app_key,
        "redirect_uri": redirect_uri,
        "state": tenant_id,
    }
    url = f"{PDD_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return RedirectResponse(url=url)


@router.get("/pinduoduo/callback", summary="拼多多 OAuth 回调", include_in_schema=False)
async def pinduoduo_callback(
    code: str,
    state: str,  # tenant_id
    db: DBDep,
):
    """处理拼多多 OAuth 回调，换取 access_token 并保存，然后重定向到前端"""
    import httpx
    from datetime import datetime, timedelta

    stmt = select(PlatformConfig).where(
        and_(
            PlatformConfig.tenant_id == state,
            PlatformConfig.platform_type == "pinduoduo",
        )
    )
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        return RedirectResponse(url="/settings?menu=platform&status=error&msg=no_config")

    try:
        plain_secret = decrypt_field(config.app_secret)
    except Exception:
        plain_secret = config.app_secret

    client = PinduoduoClient(config.app_key, plain_secret)
    try:
        token_data = await client.call_api(
            method="pdd.pop.auth.token.create",
            params={"code": code, "grant_type": "authorization_code"},
        )
    except Exception as e:
        logger.error("换取 access_token 失败: %s", e)
        return RedirectResponse(url="/settings?menu=platform&status=error&msg=token_failed")

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 7776000)
    owner_id = str(token_data.get("owner_id", ""))

    config.access_token = access_token
    config.refresh_token = refresh_token
    config.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    config.shop_id = owner_id
    config.is_active = True
    await db.commit()

    return RedirectResponse(url="/settings?menu=platform&status=success")


# ---------------------------------------------------------------------------
# 平台配置 CRUD（JWT 认证）
# ---------------------------------------------------------------------------

@router.get("/config", summary="获取平台配置", response_model=list[PlatformConfigResponse])
async def get_platform_configs(
    tenant_id: TenantTokenDep,
    db: DBDep,
):
    """获取当前租户的所有平台配置"""
    stmt = select(PlatformConfig).where(PlatformConfig.tenant_id == tenant_id)
    result = await db.execute(stmt)
    configs = result.scalars().all()
    return configs


@router.put("/config", summary="创建或更新平台配置", response_model=PlatformConfigResponse)
async def upsert_platform_config(
    tenant_id: TenantTokenDep,
    db: DBDep,
    body: PlatformConfigCreate,
    platform: str = "pinduoduo",
):
    """创建或更新指定平台的配置（upsert），app_secret 加密存储"""
    stmt = select(PlatformConfig).where(
        and_(
            PlatformConfig.tenant_id == tenant_id,
            PlatformConfig.platform_type == platform,
        )
    )
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    encrypted_secret = encrypt_field(body.app_secret)

    if config:
        config.app_key = body.app_key
        config.app_secret = encrypted_secret
        config.auto_reply_threshold = body.auto_reply_threshold
        config.human_takeover_message = body.human_takeover_message
    else:
        config = PlatformConfig(
            tenant_id=tenant_id,
            platform_type=platform,
            app_key=body.app_key,
            app_secret=encrypted_secret,
            auto_reply_threshold=body.auto_reply_threshold,
            human_takeover_message=body.human_takeover_message,
            is_active=False,
        )
        db.add(config)

    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/config/{platform}", summary="断开平台连接")
async def disconnect_platform(
    tenant_id: TenantTokenDep,
    db: DBDep,
    platform: str,
):
    """清除指定平台的 access_token，断开连接"""
    stmt = select(PlatformConfig).where(
        and_(
            PlatformConfig.tenant_id == tenant_id,
            PlatformConfig.platform_type == platform,
        )
    )
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="未找到该平台配置")

    config.access_token = None
    config.refresh_token = None
    config.expires_at = None
    config.is_active = False
    await db.commit()

    return {"success": True, "message": f"已断开 {platform} 连接"}


# ---------------------------------------------------------------------------
# 人工回复（JWT 认证）
# ---------------------------------------------------------------------------

class ManualReplyRequest(BaseModel):
    conversation_id: str
    content: str


@router.post("/pinduoduo/reply", summary="人工回复拼多多消息")
async def manual_reply(
    tenant_id: TenantTokenDep,
    db: DBDep,
    body: ManualReplyRequest,
):
    """管理员人工回复拼多多买家消息"""
    from datetime import datetime
    from models import Conversation, Message
    from sqlalchemy import select as sa_select

    # 查找会话
    stmt = sa_select(Conversation).where(
        and_(
            Conversation.tenant_id == tenant_id,
            Conversation.conversation_id == body.conversation_id,
            Conversation.platform_type == "pinduoduo",
        )
    )
    result = await db.execute(stmt)
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 查找平台配置
    stmt2 = sa_select(PlatformConfig).where(
        and_(
            PlatformConfig.tenant_id == tenant_id,
            PlatformConfig.platform_type == "pinduoduo",
            PlatformConfig.is_active == True,
        )
    )
    result2 = await db.execute(stmt2)
    config = result2.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=400, detail="平台未连接")

    try:
        plain_secret = decrypt_field(config.app_secret)
    except Exception:
        plain_secret = config.app_secret

    client = PinduoduoClient(config.app_key, plain_secret)
    try:
        await client.send_message(
            access_token=config.access_token,
            conversation_id=conversation.platform_conversation_id,
            content=body.content,
        )
    except Exception as e:
        logger.error("人工回复发送失败: %s", e)
        raise HTTPException(status_code=502, detail="消息发送失败")

    # 保存消息记录
    msg = Message(
        tenant_id=tenant_id,
        message_id=f"msg_{int(datetime.utcnow().timestamp())}_human",
        conversation_id=body.conversation_id,
        role="assistant",
        content=body.content,
    )
    db.add(msg)
    await db.commit()

    return {"success": True}
