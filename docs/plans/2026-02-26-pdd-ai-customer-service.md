# 拼多多 AI 客服接入实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将拼多多买家消息通过官方开放平台 Webhook 接入现有 ecom-chat-bot，由 AI 自动回复，支持人工介入兜底。

**Architecture:** 拼多多 Webhook → PDD Channel Adapter（新增）→ 现有 AI 对话引擎（RAG + LLM）→ pdd.service.message.push 回复买家。人工介入通过关键词检测 + 置信度阈值触发。

**Tech Stack:** Python / FastAPI、拼多多开放平台 API、现有 LangChain + RAG 引擎、Redis（会话状态）

---

## 前置准备（非代码，需人工操作）

### 准备 A：申请拼多多开放平台应用

1. 登录商家后台：https://mms.pinduoduo.com
2. 进入开放平台：https://open.pinduoduo.com
3. 【开发者中心】→【账户信息】→ 完善开发者信息（企业需上传营业执照）
4. 【我的应用】→【创建新应用】，填写：
   - 应用名称：`xxx智能客服`
   - 应用描述：AI 自动回复买家咨询
   - 回调地址：开发阶段填 ngrok 临时地址，备案后换正式 HTTPS 域名
5. 申请以下接口权限（每个需填写使用说明）：
   - `pdd.service.message.push`（发送客服消息）
   - `pdd.im.conversation.list.get`（获取会话列表）
   - `pdd.im.message.list.get`（获取历史消息）
   - 消息推送订阅（Webhook 实时推送）
6. 提交审核，等待 1-3 个工作日
7. 审核通过后，在【我的应用】记录：
   - `Client ID` → 即 `PDD_APP_KEY`
   - `Client Secret` → 即 `PDD_APP_SECRET`

### 准备 B：域名备案（与代码开发并行）

- 在阿里云/腾讯云购买域名并提交 ICP 备案
- 备案周期约 7-20 个工作日
- 备案完成后配置 HTTPS（Let's Encrypt 或云厂商证书）
- 开发阶段用 ngrok 替代：`ngrok http 8000`，获得临时 HTTPS 地址用于调试

### 准备 C：配置环境变量

备案和审核完成后，在 `.env` 或 `docker-compose.yml` 中添加：

```env
PDD_APP_KEY=your_client_id
PDD_APP_SECRET=your_client_secret
PDD_WEBHOOK_TOKEN=your_webhook_verify_token
PDD_API_BASE_URL=https://gw-api.pinduoduo.com/api/router
```

---

## Task 1：添加 PDD 配置项

**Files:**
- Modify: `backend/core/config.py`

**Step 1: 读取现有 config.py 结构**

```bash
cat backend/core/config.py | head -80
```

**Step 2: 添加 PDD 配置字段**

在 Settings 类中追加：

```python
# 拼多多开放平台
PDD_APP_KEY: str = ""
PDD_APP_SECRET: str = ""
PDD_WEBHOOK_TOKEN: str = ""
PDD_API_BASE_URL: str = "https://gw-api.pinduoduo.com/api/router"
# AI 介入阈值：置信度低于此值时转人工
PDD_AI_CONFIDENCE_THRESHOLD: float = 0.6
# 触发转人工的关键词
PDD_HUMAN_TAKEOVER_KEYWORDS: list[str] = ["转人工", "人工客服", "真人", "投诉", "退款"]
```

**Step 3: 验证配置加载**

```bash
cd backend && python -c "from core.config import settings; print(settings.PDD_APP_KEY)"
```

Expected: 输出空字符串（未配置时）不报错

**Step 4: Commit**

```bash
git add backend/core/config.py
git commit -m "feat: add PDD open platform config fields"
```

---

## Task 2：实现拼多多 API 客户端

**Files:**
- Create: `backend/services/pdd_client.py`

**Step 1: 写失败测试**

Create `backend/tests/test_pdd_client.py`:

```python
import pytest
import hashlib
from unittest.mock import patch, AsyncMock
from services.pdd_client import PddClient

def test_sign_generation():
    """验证签名算法正确"""
    client = PddClient(app_key="test_key", app_secret="test_secret")
    params = {"type": "pdd.service.message.push", "timestamp": "1700000000"}
    sign = client._generate_sign(params)
    assert isinstance(sign, str)
    assert len(sign) == 32  # MD5 hex

def test_build_request_params():
    """验证请求参数构建"""
    client = PddClient(app_key="test_key", app_secret="test_secret")
    params = client._build_params("pdd.service.message.push", {"msg": "hello"})
    assert params["client_id"] == "test_key"
    assert params["type"] == "pdd.service.message.push"
    assert "sign" in params
    assert "timestamp" in params

@pytest.mark.asyncio
async def test_send_message_success():
    """验证发送消息调用"""
    client = PddClient(app_key="test_key", app_secret="test_secret")
    mock_response = {"result": {"is_success": True}}
    with patch.object(client, "_request", return_value=mock_response) as mock_req:
        result = await client.send_message(
            conversation_id="conv_123",
            content="您好，请问有什么可以帮您？",
            msg_type=1
        )
        assert result is True
        mock_req.assert_called_once()
```

**Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_pdd_client.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'services.pdd_client'"

**Step 3: 实现 PddClient**

Create `backend/services/pdd_client.py`:

```python
import hashlib
import time
import httpx
from typing import Any
from core.config import settings


class PddClient:
    """拼多多开放平台 API 客户端"""

    def __init__(self, app_key: str = None, app_secret: str = None):
        self.app_key = app_key or settings.PDD_APP_KEY
        self.app_secret = app_secret or settings.PDD_APP_SECRET
        self.base_url = settings.PDD_API_BASE_URL

    def _generate_sign(self, params: dict) -> str:
        """MD5 签名：secret + 排序后的 key+value + secret"""
        sorted_params = sorted(params.items())
        sign_str = self.app_secret
        for k, v in sorted_params:
            sign_str += f"{k}{v}"
        sign_str += self.app_secret
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    def _build_params(self, api_type: str, biz_params: dict) -> dict:
        """构建完整请求参数"""
        import json
        params = {
            "type": api_type,
            "client_id": self.app_key,
            "timestamp": str(int(time.time())),
            "data_type": "JSON",
            "version": "V1",
        }
        if biz_params:
            params["data"] = json.dumps(biz_params)
        params["sign"] = self._generate_sign(params)
        return params

    async def _request(self, api_type: str, biz_params: dict) -> dict:
        """发起 HTTP 请求"""
        params = self._build_params(api_type, biz_params)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(self.base_url, data=params)
            resp.raise_for_status()
            return resp.json()

    async def send_message(
        self,
        conversation_id: str,
        content: str,
        msg_type: int = 1,  # 1=文本
    ) -> bool:
        """发送客服消息给买家"""
        result = await self._request(
            "pdd.service.message.push",
            {
                "conversation_id": conversation_id,
                "msg_type": msg_type,
                "content": content,
            },
        )
        return result.get("result", {}).get("is_success", False)

    async def get_conversation_list(self, page: int = 1, page_size: int = 20) -> list:
        """获取会话列表"""
        result = await self._request(
            "pdd.im.conversation.list.get",
            {"page": page, "page_size": page_size},
        )
        return result.get("result", {}).get("conversation_list", [])
```

**Step 4: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_pdd_client.py -v
```

Expected: 3 PASSED

**Step 5: Commit**

```bash
git add backend/services/pdd_client.py backend/tests/test_pdd_client.py
git commit -m "feat: add PDD API client with MD5 sign and message push"
```

---

## Task 3：实现 Webhook 签名验证与消息解析

**Files:**
- Create: `backend/services/pdd_channel.py`

**Step 1: 写失败测试**

Create `backend/tests/test_pdd_channel.py`:

```python
import pytest
import hashlib
from services.pdd_channel import PddChannel

def test_verify_webhook_signature_valid():
    """合法签名应通过验证"""
    channel = PddChannel(webhook_token="my_token")
    body = b'{"type":"IM_NEW_MESSAGE","data":{}}'
    # 模拟拼多多签名：MD5(token + body)
    expected_sign = hashlib.md5(b"my_token" + body).hexdigest()
    assert channel.verify_signature(body, expected_sign) is True

def test_verify_webhook_signature_invalid():
    """非法签名应拒绝"""
    channel = PddChannel(webhook_token="my_token")
    body = b'{"type":"IM_NEW_MESSAGE"}'
    assert channel.verify_signature(body, "wrong_sign") is False

def test_parse_new_message_event():
    """解析新消息事件"""
    channel = PddChannel(webhook_token="my_token")
    payload = {
        "type": "IM_NEW_MESSAGE",
        "data": {
            "conversation_id": "conv_abc",
            "sender_id": "buyer_123",
            "content": "这个商品还有货吗",
            "msg_type": 1,
        }
    }
    msg = channel.parse_message(payload)
    assert msg["conversation_id"] == "conv_abc"
    assert msg["content"] == "这个商品还有货吗"
    assert msg["is_buyer"] is True

def test_should_transfer_to_human():
    """检测转人工关键词"""
    channel = PddChannel(webhook_token="my_token")
    assert channel.should_transfer_to_human("我要转人工") is True
    assert channel.should_transfer_to_human("这个多少钱") is False
    assert channel.should_transfer_to_human("我要投诉") is True
```

**Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_pdd_channel.py -v
```

Expected: FAIL

**Step 3: 实现 PddChannel**

Create `backend/services/pdd_channel.py`:

```python
import hashlib
from core.config import settings


class PddChannel:
    """拼多多消息渠道适配器"""

    def __init__(self, webhook_token: str = None):
        self.webhook_token = webhook_token or settings.PDD_WEBHOOK_TOKEN
        self.human_keywords = settings.PDD_HUMAN_TAKEOVER_KEYWORDS

    def verify_signature(self, body: bytes, signature: str) -> bool:
        """验证拼多多 Webhook 签名"""
        expected = hashlib.md5(
            self.webhook_token.encode("utf-8") + body
        ).hexdigest()
        return expected == signature

    def parse_message(self, payload: dict) -> dict | None:
        """将拼多多消息格式转换为内部统一格式"""
        if payload.get("type") != "IM_NEW_MESSAGE":
            return None
        data = payload.get("data", {})
        return {
            "conversation_id": data.get("conversation_id"),
            "sender_id": data.get("sender_id"),
            "content": data.get("content", ""),
            "msg_type": data.get("msg_type", 1),
            "is_buyer": True,  # Webhook 推送的均为买家消息
            "channel": "pinduoduo",
        }

    def should_transfer_to_human(self, content: str) -> bool:
        """检测是否需要转人工"""
        return any(kw in content for kw in self.human_keywords)
```

**Step 4: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_pdd_channel.py -v
```

Expected: 4 PASSED

**Step 5: Commit**

```bash
git add backend/services/pdd_channel.py backend/tests/test_pdd_channel.py
git commit -m "feat: add PDD webhook signature verification and message parser"
```

---

## Task 4：实现会话状态管理（Redis）

**Files:**
- Create: `backend/services/pdd_session.py`

**Step 1: 写失败测试**

Create `backend/tests/test_pdd_session.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from services.pdd_session import PddSessionManager

@pytest.mark.asyncio
async def test_set_and_get_human_mode():
    """设置人工接管后应返回 True"""
    manager = PddSessionManager()
    with patch.object(manager.redis, "set", new_callable=AsyncMock) as mock_set, \
         patch.object(manager.redis, "get", new_callable=AsyncMock, return_value=b"1"):
        await manager.set_human_mode("conv_123", True)
        result = await manager.is_human_mode("conv_123")
        assert result is True

@pytest.mark.asyncio
async def test_ai_mode_by_default():
    """默认应为 AI 模式"""
    manager = PddSessionManager()
    with patch.object(manager.redis, "get", new_callable=AsyncMock, return_value=None):
        result = await manager.is_human_mode("conv_new")
        assert result is False
```

**Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_pdd_session.py -v
```

**Step 3: 实现 PddSessionManager**

Create `backend/services/pdd_session.py`:

```python
from db.redis import get_redis_client

HUMAN_MODE_KEY = "pdd:human_mode:{conversation_id}"
HUMAN_MODE_TTL = 3600 * 8  # 8小时后自动恢复 AI 模式


class PddSessionManager:
    """管理拼多多会话的 AI/人工 模式状态"""

    def __init__(self):
        self.redis = get_redis_client()

    def _key(self, conversation_id: str) -> str:
        return HUMAN_MODE_KEY.format(conversation_id=conversation_id)

    async def set_human_mode(self, conversation_id: str, enabled: bool) -> None:
        key = self._key(conversation_id)
        if enabled:
            await self.redis.set(key, "1", ex=HUMAN_MODE_TTL)
        else:
            await self.redis.delete(key)

    async def is_human_mode(self, conversation_id: str) -> bool:
        val = await self.redis.get(self._key(conversation_id))
        return val is not None
```

**Step 4: 运行测试确认通过**

```bash
cd backend && python -m pytest tests/test_pdd_session.py -v
```

Expected: 2 PASSED

**Step 5: Commit**

```bash
git add backend/services/pdd_session.py backend/tests/test_pdd_session.py
git commit -m "feat: add PDD session manager for AI/human mode switching via Redis"
```

---

## Task 5：实现 Webhook 路由（核心处理逻辑）

**Files:**
- Create: `backend/api/routers/pdd_webhook.py`
- Modify: `backend/api/main.py`

**Step 1: 写失败测试**

Create `backend/tests/test_pdd_webhook.py`:

```python
import pytest
import hashlib
import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def make_signature(token: str, body: bytes) -> str:
    return hashlib.md5(token.encode() + body).hexdigest()

def test_webhook_invalid_signature():
    """签名错误应返回 403"""
    response = client.post(
        "/api/v1/pdd/webhook",
        content=b'{"type":"IM_NEW_MESSAGE"}',
        headers={"X-Pdd-Sign": "wrong_sign"},
    )
    assert response.status_code == 403

def test_webhook_non_message_event():
    """非消息事件应返回 200 但不处理"""
    body = json.dumps({"type": "ORDER_PAID", "data": {}}).encode()
    token = "test_token"
    sign = make_signature(token, body)
    with patch("api.routers.pdd_webhook.settings") as mock_settings:
        mock_settings.PDD_WEBHOOK_TOKEN = token
        response = client.post(
            "/api/v1/pdd/webhook",
            content=body,
            headers={"X-Pdd-Sign": sign},
        )
    assert response.status_code == 200
```

**Step 2: 运行测试确认失败**

```bash
cd backend && python -m pytest tests/test_pdd_webhook.py -v
```

**Step 3: 实现 Webhook 路由**

Create `backend/api/routers/pdd_webhook.py`:

```python
import logging
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from core.config import settings
from services.pdd_channel import PddChannel
from services.pdd_client import PddClient
from services.pdd_session import PddSessionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/pdd", tags=["pdd"])

channel = PddChannel()
pdd_client = PddClient()
session_manager = PddSessionManager()


@router.post("/webhook")
async def pdd_webhook(request: Request, background_tasks: BackgroundTasks):
    """接收拼多多消息推送"""
    body = await request.body()
    signature = request.headers.get("X-Pdd-Sign", "")

    if not channel.verify_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()
    msg = channel.parse_message(payload)

    if msg is None:
        return {"success": True}  # 非消息事件，忽略

    background_tasks.add_task(handle_message, msg)
    return {"success": True}


async def handle_message(msg: dict):
    """后台处理消息：AI 回复或转人工"""
    conversation_id = msg["conversation_id"]
    content = msg["content"]

    # 1. 检查是否已在人工模式
    if await session_manager.is_human_mode(conversation_id):
        logger.info(f"[PDD] conv={conversation_id} 人工模式，跳过 AI")
        return

    # 2. 检测转人工关键词
    if channel.should_transfer_to_human(content):
        await session_manager.set_human_mode(conversation_id, True)
        await pdd_client.send_message(
            conversation_id,
            "好的，正在为您转接人工客服，请稍候～",
        )
        logger.info(f"[PDD] conv={conversation_id} 触发转人工")
        return

    # 3. 调用现有 AI 引擎生成回复
    try:
        from services.ai_chat_service import AIChatService
        ai_service = AIChatService()
        reply = await ai_service.chat(
            message=content,
            conversation_id=conversation_id,
            channel="pinduoduo",
        )
        await pdd_client.send_message(conversation_id, reply)
        logger.info(f"[PDD] conv={conversation_id} AI 回复成功")
    except Exception as e:
        logger.error(f"[PDD] AI 回复失败: {e}")
        await pdd_client.send_message(
            conversation_id,
            "抱歉，系统繁忙，请稍后再试，或联系人工客服。",
        )
```

**Step 4: 注册路由到 main.py**

在 `backend/api/main.py` 中找到路由注册区域，添加：

```python
from api.routers import pdd_webhook
app.include_router(pdd_webhook.router)
```

**Step 5: 运行测试**

```bash
cd backend && python -m pytest tests/test_pdd_webhook.py -v
```

Expected: 2 PASSED

**Step 6: Commit**

```bash
git add backend/api/routers/pdd_webhook.py backend/api/main.py backend/tests/test_pdd_webhook.py
git commit -m "feat: add PDD webhook endpoint with AI auto-reply and human takeover"
```

---

## Task 6：本地联调测试

**Step 1: 启动依赖服务**

```bash
docker-compose up -d postgres redis
```

**Step 2: 启动后端**

```bash
cd backend && uvicorn api.main:app --reload --port 8000
```

**Step 3: 安装并启动 ngrok（临时公网地址）**

```bash
# 安装 ngrok（macOS）
brew install ngrok
# 启动隧道
ngrok http 8000
# 记录输出的 HTTPS 地址，例如：https://abc123.ngrok.io
```

**Step 4: 模拟拼多多推送消息**

```bash
# 替换 YOUR_TOKEN 和 ngrok 地址
TOKEN="your_webhook_token"
BODY='{"type":"IM_NEW_MESSAGE","data":{"conversation_id":"test_conv_001","sender_id":"buyer_001","content":"这个商品还有货吗","msg_type":1}}'
SIGN=$(echo -n "${TOKEN}${BODY}" | md5sum | awk '{print $1}')

curl -X POST https://abc123.ngrok.io/api/v1/pdd/webhook \
  -H "Content-Type: application/json" \
  -H "X-Pdd-Sign: $SIGN" \
  -d "$BODY"
```

Expected: `{"success": true}`，后台日志显示 AI 回复

**Step 5: 测试转人工**

```bash
BODY='{"type":"IM_NEW_MESSAGE","data":{"conversation_id":"test_conv_001","sender_id":"buyer_001","content":"我要转人工","msg_type":1}}'
# 重新计算签名后发送
```

Expected: 日志显示"触发转人工"

---

## Task 7：配置正式环境（备案完成后执行）

**Step 1: 配置 HTTPS 域名**

```bash
# 以 Nginx + Let's Encrypt 为例
certbot --nginx -d your-domain.com
```

**Step 2: 更新环境变量**

在 `.env` 或 `docker-compose.prod.yml` 中填入真实值：

```env
PDD_APP_KEY=your_real_client_id
PDD_APP_SECRET=your_real_client_secret
PDD_WEBHOOK_TOKEN=your_real_webhook_token
```

**Step 3: 在拼多多开放平台配置 Webhook 地址**

登录 https://open.pinduoduo.com → 我的应用 → 消息推送配置：
- Webhook URL：`https://your-domain.com/api/v1/pdd/webhook`
- 订阅事件：`IM_NEW_MESSAGE`

**Step 4: 生产环境部署**

```bash
docker-compose -f docker-compose.prod.yml up -d
```

**Step 5: 验证线上推送**

在拼多多商家后台发起一条测试消息，确认 AI 自动回复正常。

---

## 整体时间线

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| 代码开发 | Task 1-6 | 1-2 天 |
| 开放平台审核 | 申请接口权限 | 1-3 工作日 |
| 域名备案 | ICP 备案 | 7-20 工作日 |
| 联调上线 | Task 7 + 验证 | 半天 |

> 代码开发和备案/审��可以完全并行，不互相阻塞。

---

## 关键密钥获取位置汇总

| 密钥 | 获取位置 |
|------|----------|
| `PDD_APP_KEY` | 拼多多开放平台 → 我的应用 → Client ID |
| `PDD_APP_SECRET` | 拼多多开放平台 → 我的应用 → Client Secret |
| `PDD_WEBHOOK_TOKEN` | 拼多多开放平台 → 消息推送配置 → 自定义 Token |
| LLM API Key | 已在现有 `.env` 中配置（DeepSeek/OpenAI 等） |
