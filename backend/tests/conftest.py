"""
测试配置和 Fixtures
"""
import asyncio
import uuid
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timedelta
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from faker import Faker
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from core import create_access_token, hash_password
from db import get_db, get_redis
from db.session import Base
from models import Admin, Subscription, Tenant

# 使用内存数据库进行测试
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

# 创建测试会话工厂
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Faker实例
fake = Faker(["zh_CN"])


# ==================== 基础 Fixtures ====================


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    # 清理所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def redis_mock():
    """Mock Redis客户端"""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    redis.exists = AsyncMock(return_value=False)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    redis.ttl = AsyncMock(return_value=-1)
    redis.ping = AsyncMock(return_value=True)
    redis.info = AsyncMock(return_value={
        "connected_clients": 1,
        "used_memory_human": "1M",
        "uptime_in_days": 1,
        "total_commands_processed": 100,
    })
    return redis


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession, redis_mock) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    async def override_get_redis():
        return redis_mock

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ==================== 测试数据 Fixtures ====================


@pytest.fixture
def test_tenant_data() -> dict[str, Any]:
    """测试租户数据"""
    return {
        "company_name": "测试公司",
        "contact_name": "张三",
        "contact_email": "test@example.com",
        "contact_phone": "13800138000",
        "password": "testpassword123",
    }


@pytest.fixture
def test_webhook_data() -> dict[str, Any]:
    """测试 Webhook 数据"""
    return {
        "name": "测试 Webhook",
        "description": "测试描述",
        "url": "https://example.com/webhook",
        "event_type": "conversation.created",
        "timeout": 30,
        "retry_count": 3,
        "retry_interval": 60,
    }


@pytest.fixture
def admin_data() -> Dict[str, Any]:
    """管理员测试数据"""
    return {
        "username": "test_admin",
        "password": "Admin@123456",
        "email": fake.email(),
        "phone": fake.phone_number(),
        "role": "super_admin",
    }


@pytest.fixture
def tenant_data() -> Dict[str, Any]:
    """租户测试数据"""
    return {
        "company_name": fake.company(),
        "contact_name": fake.name(),
        "contact_email": fake.email(),
        "contact_phone": fake.phone_number(),
        "password": "Tenant@123456",
    }


@pytest.fixture
def knowledge_data() -> Dict[str, Any]:
    """知识库测试数据"""
    return {
        "knowledge_type": "faq",
        "title": fake.sentence(),
        "content": fake.text(),
        "category": "常见问题",
        "tags": ["测试", "FAQ"],
        "source": "manual",
        "priority": 1,
    }


@pytest.fixture
def conversation_data() -> Dict[str, Any]:
    """对话测试数据"""
    return {
        "user_id": f"user_{uuid.uuid4().hex[:8]}",
        "channel": "web",
        "metadata": {"source": "test", "device": "desktop"},
    }


@pytest.fixture
def payment_data() -> Dict[str, Any]:
    """支付测试数据"""
    return {
        "plan_type": "basic",
        "duration_months": 1,
        "payment_type": "pc",
        "subscription_type": "new",
        "description": "测试订阅",
    }


@pytest.fixture
def webhook_data() -> Dict[str, Any]:
    """Webhook测试数据"""
    return {
        "name": "测试Webhook",
        "endpoint_url": "https://example.com/webhook",
        "events": ["conversation.created", "conversation.closed"],
        "secret": "test_secret_key",
    }


@pytest.fixture
def model_config_data() -> Dict[str, Any]:
    """模型配置测试数据"""
    return {
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "api_key": "sk-test-key",
        "api_base": "https://api.openai.com/v1",
        "temperature": 0.7,
        "max_tokens": 2000,
        "use_case": "chat",
        "is_default": True,
    }


# ==================== 数据库实体 Fixtures ====================


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession, admin_data: Dict) -> Admin:
    """创建测试管理员"""
    admin = Admin(
        admin_id=f"ADMIN_{uuid.uuid4().hex[:12].upper()}",
        username=admin_data["username"],
        password_hash=hash_password(admin_data["password"]),
        email=admin_data["email"],
        phone=admin_data.get("phone"),
        role="super_admin",
        status="active",
        permissions=["*"],
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture
async def test_tenant(db_session: AsyncSession, tenant_data: Dict) -> Tenant:
    """创建测试租户"""
    tenant_id = f"TENANT_{uuid.uuid4().hex[:12].upper()}"
    api_key = f"sk_live_{uuid.uuid4().hex}"

    tenant = Tenant(
        tenant_id=tenant_id,
        company_name=tenant_data["company_name"],
        contact_name=tenant_data["contact_name"],
        contact_email=tenant_data["contact_email"],
        contact_phone=tenant_data.get("contact_phone"),
        password_hash=hash_password(tenant_data["password"]),
        api_key_hash=hash_password(api_key),
        status="active",
    )
    db_session.add(tenant)

    # 创建订阅
    subscription = Subscription(
        tenant_id=tenant_id,
        plan_type="free",
        status="active",
        start_date=datetime.utcnow(),
        expire_at=datetime.utcnow() + timedelta(days=365),
        enabled_features='["BASIC_CHAT"]',
        conversation_quota=1000,
        concurrent_quota=10,
        storage_quota=1,
        api_quota=10000,
    )
    db_session.add(subscription)

    await db_session.commit()
    await db_session.refresh(tenant)

    # 将API Key保存到tenant对象中以便测试使用
    tenant.plain_api_key = api_key

    return tenant


# ==================== Token Fixtures ====================


@pytest.fixture
def admin_token(test_admin: Admin) -> str:
    """生成管理员Token"""
    return create_access_token(
        subject=test_admin.admin_id,
        role=test_admin.role,
        expires_delta=timedelta(hours=8),
    )


@pytest.fixture
def tenant_token(test_tenant: Tenant) -> str:
    """生成租户Token"""
    return create_access_token(
        subject=test_tenant.tenant_id,
        tenant_id=test_tenant.tenant_id,
        expires_delta=timedelta(hours=24),
    )


@pytest.fixture
def admin_headers(admin_token: str) -> Dict[str, str]:
    """管理员请求头"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def tenant_headers(tenant_token: str) -> Dict[str, str]:
    """租户Token请求头"""
    return {
        "Authorization": f"Bearer {tenant_token}",
        "Content-Type": "application/json",
    }


@pytest.fixture
def tenant_api_key_headers(test_tenant: Tenant) -> Dict[str, str]:
    """租户API Key请求头"""
    return {
        "X-API-Key": test_tenant.plain_api_key,
        "Content-Type": "application/json",
    }


# ==================== Mock服务 Fixtures ====================


@pytest.fixture
def mock_llm_service():
    """Mock LLM服务"""
    mock_service = MagicMock()
    mock_service.chat = AsyncMock(
        return_value={
            "response": "这是AI的回复",
            "model": "gpt-3.5-turbo",
            "input_tokens": 10,
            "output_tokens": 15,
            "total_tokens": 25,
        }
    )
    mock_service.classify_intent = AsyncMock(return_value="order_inquiry")
    mock_service.extract_entities = AsyncMock(
        return_value={"order_id": "123456", "product": "商品名"}
    )
    return mock_service


@pytest.fixture
def mock_rag_service():
    """Mock RAG服务"""
    mock_service = MagicMock()
    mock_service.retrieve = AsyncMock(
        return_value=[
            {
                "knowledge_id": "K001",
                "title": "测试知识",
                "content": "知识内容",
                "score": 0.95,
            }
        ]
    )
    mock_service.generate = AsyncMock(
        return_value={
            "answer": "基于知识库的回答",
            "sources": ["K001"],
        }
    )
    return mock_service


@pytest.fixture
def mock_payment_service():
    """Mock支付服务"""
    mock_service = MagicMock()
    mock_service.create_payment_order = AsyncMock(
        return_value=(
            MagicMock(
                order_number="ORDER_TEST_001",
                amount=99.00,
                currency="CNY",
                expired_at=datetime.utcnow() + timedelta(hours=2),
            ),
            "<form>支付表单HTML</form>",
        )
    )
    mock_service.verify_payment = AsyncMock(return_value=True)
    return mock_service
