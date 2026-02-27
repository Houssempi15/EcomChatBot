# 电商 AI 内容生成与数据分析平台 - 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有电商智能客服 SaaS 平台上新增商品同步、AI 内容生成、智能定价、订单分析 6 大功能模块。

**Architecture:** 功能模块独立扩展，每个功能作为独立 service + router，共享现有基础设施（Celery、Milvus、Redis、MinIO）。平台对接采用适配器模式，统一抽象接口。所有 AI 生成通过现有模型配置系统管理多模态大模型。

**Tech Stack:** FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL + Alembic / Next.js 14 + Ant Design v6 + Zustand + TypeScript / Celery + Redis + Milvus + MinIO

**设计文档:** `docs/plans/2026-02-28-ecommerce-ai-content-platform-design.md`

---

## 阶段 1：商品同步与知识库集成

### Task 1: 创建 Product 数据模型

**Files:**
- Create: `backend/models/product.py`
- Modify: `backend/models/__init__.py`
- Test: `backend/tests/models/test_product.py`

**Step 1: 编写模型文件**

```python
# backend/models/product.py
"""商品数据模型"""
import json
from enum import Enum as PyEnum

from sqlalchemy import (
    DateTime, Float, Index, Integer, Numeric, String, Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from models.base import TenantBaseModel


class JSONField(TypeDecorator):
    """跨数据库兼容的 JSON 类型"""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class ProductStatus(str, PyEnum):
    """商品状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"


class SyncTarget(str, PyEnum):
    """同步目标"""
    PRODUCT = "product"
    ORDER = "order"


class SyncType(str, PyEnum):
    """同步类型"""
    FULL = "full"
    INCREMENTAL = "incremental"


class SyncTaskStatus(str, PyEnum):
    """同步任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Product(TenantBaseModel):
    """商品表"""

    __tablename__ = "products"
    __table_args__ = (
        Index("idx_product_tenant", "tenant_id"),
        Index("idx_product_platform", "platform_config_id"),
        Index("idx_product_platform_id", "platform_product_id"),
        Index("idx_product_status", "status"),
        Index("idx_product_category", "category"),
        {"comment": "商品表"},
    )

    platform_config_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="平台配置ID"
    )
    platform_product_id: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="平台侧商品ID"
    )
    title: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="商品标题"
    )
    description: Mapped[str | None] = mapped_column(
        Text, comment="商品描述"
    )
    price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, comment="当前售价"
    )
    original_price: Mapped[float | None] = mapped_column(
        Numeric(10, 2), comment="原价"
    )
    currency: Mapped[str] = mapped_column(
        String(8), nullable=False, default="CNY", comment="货币"
    )
    category: Mapped[str | None] = mapped_column(
        String(128), comment="商品分类"
    )
    images: Mapped[list | None] = mapped_column(
        JSONField, comment="商品图片URL列表(JSON)"
    )
    videos: Mapped[list | None] = mapped_column(
        JSONField, comment="商品视频URL列表(JSON)"
    )
    attributes: Mapped[dict | None] = mapped_column(
        JSONField, comment="SKU属性(JSON)"
    )
    sales_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="销量"
    )
    stock: Mapped[int] = mapped_column(
        Integer, default=0, comment="库存"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active",
        comment="状态(active/inactive/deleted)"
    )
    platform_data: Mapped[dict | None] = mapped_column(
        JSONField, comment="平台原始数据(JSON)"
    )
    knowledge_base_id: Mapped[int | None] = mapped_column(
        Integer, comment="关联知识库条目ID"
    )
    last_synced_at: Mapped[str | None] = mapped_column(
        DateTime, comment="最近同步时间"
    )

    def __repr__(self) -> str:
        return f"<Product {self.title} ({self.status})>"


class PlatformSyncTask(TenantBaseModel):
    """平台同步任务表"""

    __tablename__ = "platform_sync_tasks"
    __table_args__ = (
        Index("idx_sync_task_tenant", "tenant_id"),
        Index("idx_sync_task_status", "status"),
        {"comment": "平台同步任务表"},
    )

    platform_config_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="平台配置ID"
    )
    sync_target: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="同步目标(product/order)"
    )
    sync_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="同步类型(full/incremental)"
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending",
        comment="状态(pending/running/completed/failed)"
    )
    total_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="需同步总数"
    )
    synced_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="已同步数"
    )
    failed_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="失败数"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, comment="错误信息"
    )
    started_at: Mapped[str | None] = mapped_column(
        DateTime, comment="开始时间"
    )
    completed_at: Mapped[str | None] = mapped_column(
        DateTime, comment="完成时间"
    )

    def __repr__(self) -> str:
        return f"<PlatformSyncTask {self.sync_target}/{self.sync_type} ({self.status})>"


class ProductSyncSchedule(TenantBaseModel):
    """商品同步调度配置表"""

    __tablename__ = "product_sync_schedules"
    __table_args__ = (
        Index("idx_sync_schedule_tenant", "tenant_id"),
        {"comment": "商品同步调度配置表"},
    )

    platform_config_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="平台配置ID"
    )
    interval_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60, comment="同步间隔(分钟)"
    )
    is_active: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="是否启用"
    )
    last_run_at: Mapped[str | None] = mapped_column(
        DateTime, comment="上次执行时间"
    )
    next_run_at: Mapped[str | None] = mapped_column(
        DateTime, comment="下次执行时间"
    )

    def __repr__(self) -> str:
        return f"<ProductSyncSchedule platform={self.platform_config_id} interval={self.interval_minutes}m>"
```

**Step 2: 注册模型到 `__init__.py`**

在 `backend/models/__init__.py` 中添加导入：

```python
from models.product import (
    Product, PlatformSyncTask, ProductSyncSchedule,
    ProductStatus, SyncTarget, SyncType, SyncTaskStatus,
)
```

并添加到 `__all__` 列表。

**Step 3: 运行验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot/backend && python -c "from models.product import Product, PlatformSyncTask, ProductSyncSchedule; print('OK')"`
Expected: OK

**Step 4: 提交**

```bash
git add backend/models/product.py backend/models/__init__.py
git commit -m "feat: add Product, PlatformSyncTask, ProductSyncSchedule models"
```

---

### Task 2: 创建数据库迁移

**Files:**
- Create: `backend/migrations/versions/013_add_product_tables.py`

**Step 1: 编写迁移文件**

```python
# backend/migrations/versions/013_add_product_tables.py
"""Add product sync tables

Revision ID: 013_add_product_tables
Revises: 012_remove_quota_system
Create Date: 2026-02-28

Description:
    - 创建 products 表（商品数据）
    - 创建 platform_sync_tasks 表（同步任务）
    - 创建 product_sync_schedules 表（同步调度配置）
"""

from alembic import op

revision = "013_add_product_tables"
down_revision = "012_remove_quota_system"
branch_labels = None
depends_on = None


def upgrade():
    # 创建 products 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            platform_config_id INTEGER NOT NULL,
            platform_product_id VARCHAR(128) NOT NULL,
            title VARCHAR(512) NOT NULL,
            description TEXT,
            price NUMERIC(10, 2) NOT NULL,
            original_price NUMERIC(10, 2),
            currency VARCHAR(8) NOT NULL DEFAULT 'CNY',
            category VARCHAR(128),
            images TEXT,
            videos TEXT,
            attributes TEXT,
            sales_count INTEGER DEFAULT 0,
            stock INTEGER DEFAULT 0,
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            platform_data TEXT,
            knowledge_base_id INTEGER,
            last_synced_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_product_tenant ON products (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_product_platform ON products (platform_config_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_product_platform_id ON products (platform_product_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_product_status ON products (status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_product_category ON products (category)")

    # 创建 platform_sync_tasks 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS platform_sync_tasks (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            platform_config_id INTEGER NOT NULL,
            sync_target VARCHAR(32) NOT NULL,
            sync_type VARCHAR(32) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            total_count INTEGER DEFAULT 0,
            synced_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            error_message TEXT,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_task_tenant ON platform_sync_tasks (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_task_status ON platform_sync_tasks (status)")

    # 创建 product_sync_schedules 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS product_sync_schedules (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            platform_config_id INTEGER NOT NULL,
            interval_minutes INTEGER NOT NULL DEFAULT 60,
            is_active INTEGER NOT NULL DEFAULT 1,
            last_run_at TIMESTAMP,
            next_run_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """)

    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_schedule_tenant ON product_sync_schedules (tenant_id)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS product_sync_schedules")
    op.execute("DROP TABLE IF EXISTS platform_sync_tasks")
    op.execute("DROP TABLE IF EXISTS products")
```

**Step 2: 运行迁移**

Run: `cd /Users/zhulang/work/ecom-chat-bot && docker compose exec api alembic upgrade head`
Expected: Running upgrade 012_remove_quota_system -> 013_add_product_tables

**Step 3: 提交**

```bash
git add backend/migrations/versions/013_add_product_tables.py
git commit -m "migration: add products, platform_sync_tasks, product_sync_schedules tables"
```

---

### Task 3: 创建 Product Schemas

**Files:**
- Create: `backend/schemas/product.py`

**Step 1: 编写 Schema 文件**

```python
# backend/schemas/product.py
"""商品相关 Pydantic Schema"""
from datetime import datetime

from pydantic import BaseModel, Field

from schemas.base import BaseSchema, TimestampSchema


# ===== Product Schemas =====

class ProductBase(BaseSchema):
    """商品基础 Schema"""
    title: str = Field(..., min_length=1, max_length=512, description="商品标题")
    description: str | None = Field(None, description="商品描述")
    price: float = Field(..., ge=0, description="当前售价")
    original_price: float | None = Field(None, ge=0, description="原价")
    currency: str = Field("CNY", max_length=8, description="货币")
    category: str | None = Field(None, max_length=128, description="商品分类")
    images: list[str] | None = Field(None, description="商品图片URL列表")
    videos: list[str] | None = Field(None, description="商品视频URL列表")
    attributes: dict | None = Field(None, description="SKU属性")
    sales_count: int = Field(0, ge=0, description="销量")
    stock: int = Field(0, ge=0, description="库存")


class ProductResponse(ProductBase, TimestampSchema):
    """商品响应"""
    id: int
    tenant_id: str
    platform_config_id: int
    platform_product_id: str
    status: str
    knowledge_base_id: int | None = None
    last_synced_at: datetime | None = None
    platform_data: dict | None = None


class ProductListQuery(BaseModel):
    """商品列表查询参数"""
    keyword: str | None = Field(None, description="搜索关键词")
    category: str | None = Field(None, description="分类筛选")
    status: str | None = Field(None, pattern="^(active|inactive|deleted)$", description="状态筛选")
    platform_config_id: int | None = Field(None, description="平台筛选")
    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")


# ===== Sync Task Schemas =====

class SyncTaskResponse(BaseSchema, TimestampSchema):
    """同步任务响应"""
    id: int
    tenant_id: str
    platform_config_id: int
    sync_target: str
    sync_type: str
    status: str
    total_count: int
    synced_count: int
    failed_count: int
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class TriggerSyncRequest(BaseModel):
    """触发同步请求"""
    platform_config_id: int = Field(..., description="平台配置ID")
    sync_type: str = Field("full", pattern="^(full|incremental)$", description="同步类型")


# ===== Sync Schedule Schemas =====

class SyncScheduleResponse(BaseSchema, TimestampSchema):
    """同步��度响应"""
    id: int
    tenant_id: str
    platform_config_id: int
    interval_minutes: int
    is_active: bool
    last_run_at: datetime | None = None
    next_run_at: datetime | None = None


class SyncScheduleUpdate(BaseModel):
    """更新同步调度"""
    interval_minutes: int | None = Field(None, ge=10, le=1440, description="同步间隔(分钟)")
    is_active: bool | None = Field(None, description="是否启用")
```

**Step 2: 运行验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot/backend && python -c "from schemas.product import ProductResponse, TriggerSyncRequest; print('OK')"`
Expected: OK

**Step 3: 提交**

```bash
git add backend/schemas/product.py
git commit -m "feat: add product, sync task, sync schedule schemas"
```

---

### Task 4: 创建平台适配器抽象基类和拼多多适配器

**Files:**
- Create: `backend/services/platform/base_adapter.py`
- Create: `backend/services/platform/pdd_adapter.py`
- Create: `backend/services/platform/adapter_factory.py`

**Step 1: 编写抽象基类**

```python
# backend/services/platform/base_adapter.py
"""电商平台适配器抽象基类"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ProductDTO:
    """商品数据传输对象"""
    platform_product_id: str
    title: str
    price: float
    original_price: float | None = None
    description: str | None = None
    category: str | None = None
    images: list[str] = field(default_factory=list)
    videos: list[str] = field(default_factory=list)
    attributes: dict | None = None
    sales_count: int = 0
    stock: int = 0
    status: str = "active"
    platform_data: dict | None = None


@dataclass
class OrderDTO:
    """订单数据传输对象"""
    platform_order_id: str
    product_id: str | None = None
    product_title: str = ""
    buyer_id: str = ""
    quantity: int = 1
    unit_price: float = 0.0
    total_amount: float = 0.0
    status: str = "pending"
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    completed_at: datetime | None = None
    refund_amount: float | None = None
    platform_data: dict | None = None


@dataclass
class PageResult:
    """分页结果"""
    items: list
    total: int
    page: int
    page_size: int


class BasePlatformAdapter(ABC):
    """电商平台适配器抽象基类

    所有电商平台（拼多多、淘宝、京东等）的适配器都继承此类，
    实现统一的商品/订单操作接口。
    """

    def __init__(self, app_key: str, app_secret: str, access_token: str | None = None):
        self.app_key = app_key
        self.app_secret = app_secret
        self.access_token = access_token

    @abstractmethod
    async def fetch_products(self, page: int = 1, page_size: int = 50) -> PageResult:
        """分页拉取商品列表"""
        ...

    @abstractmethod
    async def fetch_product_detail(self, product_id: str) -> ProductDTO:
        """获取商品详情"""
        ...

    @abstractmethod
    async def fetch_updated_products(self, since: datetime) -> list[ProductDTO]:
        """拉取指定时间后变更的商品"""
        ...

    @abstractmethod
    async def upload_image(self, product_id: str, image_url: str) -> str:
        """上传图片到平台，返回平台侧图片URL"""
        ...

    @abstractmethod
    async def upload_video(self, product_id: str, video_url: str) -> str:
        """上传视频到平台，返回平台侧视频URL"""
        ...

    @abstractmethod
    async def update_product(self, product_id: str, data: dict) -> bool:
        """更新商品信息"""
        ...

    @abstractmethod
    async def fetch_orders(
        self,
        page: int = 1,
        page_size: int = 50,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        status: str | None = None,
    ) -> PageResult:
        """分页拉取订单列表"""
        ...

    @abstractmethod
    async def fetch_order_detail(self, order_id: str) -> OrderDTO:
        """获取订单详情"""
        ...
```

**Step 2: 编写拼多多适配器**

```python
# backend/services/platform/pdd_adapter.py
"""拼多多平台适配器"""
import logging
from datetime import datetime

from services.platform.base_adapter import (
    BasePlatformAdapter, OrderDTO, PageResult, ProductDTO,
)
from services.platform.pinduoduo_client import PinduoduoClient

logger = logging.getLogger(__name__)


class PddAdapter(BasePlatformAdapter):
    """拼多多平台适配器"""

    def __init__(self, app_key: str, app_secret: str, access_token: str | None = None):
        super().__init__(app_key, app_secret, access_token)
        self.client = PinduoduoClient(app_key, app_secret)

    def _parse_product(self, raw: dict) -> ProductDTO:
        """将拼多多商品原始数据转为 ProductDTO"""
        images = []
        if raw.get("image_url"):
            images.append(raw["image_url"])
        if raw.get("thumb_url"):
            images.extend(raw.get("carousel_gallery_list", []))

        return ProductDTO(
            platform_product_id=str(raw.get("goods_id", "")),
            title=raw.get("goods_name", ""),
            price=float(raw.get("min_group_price", 0)) / 100,  # 拼多多价格单位为分
            original_price=float(raw.get("min_normal_price", 0)) / 100 if raw.get("min_normal_price") else None,
            description=raw.get("goods_desc", ""),
            category=raw.get("category_name", ""),
            images=images,
            videos=[],
            attributes=raw.get("sku_list"),
            sales_count=raw.get("sold_quantity", 0),
            stock=raw.get("goods_quantity", 0),
            status="active" if raw.get("is_onsale") else "inactive",
            platform_data=raw,
        )

    async def fetch_products(self, page: int = 1, page_size: int = 50) -> PageResult:
        """拉取拼多多商品列表"""
        result = await self.client.call_api(
            method="pdd.goods.list.get",
            params={
                "page": str(page),
                "page_size": str(page_size),
                "outer_goods_id": "",
            },
            access_token=self.access_token,
        )

        response = result.get("goods_list_get_response", {})
        goods_list = response.get("goods_list", [])
        total = response.get("total_count", 0)

        products = [self._parse_product(g) for g in goods_list]

        return PageResult(
            items=products,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def fetch_product_detail(self, product_id: str) -> ProductDTO:
        """获取拼多多商品详情"""
        result = await self.client.call_api(
            method="pdd.goods.information.get",
            params={"goods_id": product_id},
            access_token=self.access_token,
        )
        goods_info = result.get("goods_information_get_response", {}).get("goods_info", {})
        return self._parse_product(goods_info)

    async def fetch_updated_products(self, since: datetime) -> list[ProductDTO]:
        """拉取指定时间后变更的商品"""
        timestamp = int(since.timestamp())
        result = await self.client.call_api(
            method="pdd.goods.list.get",
            params={
                "page": "1",
                "page_size": "100",
                "update_start_time": str(timestamp),
            },
            access_token=self.access_token,
        )
        response = result.get("goods_list_get_response", {})
        goods_list = response.get("goods_list", [])
        return [self._parse_product(g) for g in goods_list]

    async def upload_image(self, product_id: str, image_url: str) -> str:
        """上传图片到拼多多"""
        result = await self.client.call_api(
            method="pdd.goods.image.upload",
            params={"image_url": image_url},
            access_token=self.access_token,
        )
        return result.get("goods_image_upload_response", {}).get("image_url", "")

    async def upload_video(self, product_id: str, video_url: str) -> str:
        """上传视频到拼多多"""
        result = await self.client.call_api(
            method="pdd.goods.video.upload",
            params={"video_url": video_url},
            access_token=self.access_token,
        )
        return result.get("goods_video_upload_response", {}).get("video_id", "")

    async def update_product(self, product_id: str, data: dict) -> bool:
        """更新拼多多商品信息"""
        params = {"goods_id": product_id, **data}
        result = await self.client.call_api(
            method="pdd.goods.information.update",
            params=params,
            access_token=self.access_token,
        )
        return "error_response" not in result

    async def fetch_orders(
        self,
        page: int = 1,
        page_size: int = 50,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        status: str | None = None,
    ) -> PageResult:
        """拉取拼多多订单列表"""
        params: dict = {
            "page": str(page),
            "page_size": str(page_size),
        }
        if start_time:
            params["start_confirm_at"] = str(int(start_time.timestamp()))
        if end_time:
            params["end_confirm_at"] = str(int(end_time.timestamp()))
        if status:
            # 拼多多订单状态映射
            status_map = {
                "pending": "1",
                "paid": "2",
                "shipped": "3",
                "completed": "5",
            }
            if status in status_map:
                params["order_status"] = status_map[status]

        result = await self.client.call_api(
            method="pdd.order.list.get",
            params=params,
            access_token=self.access_token,
        )

        response = result.get("order_list_get_response", {})
        order_list = response.get("order_list", [])
        total = response.get("total_count", 0)

        orders = [self._parse_order(o) for o in order_list]

        return PageResult(items=orders, total=total, page=page, page_size=page_size)

    def _parse_order(self, raw: dict) -> OrderDTO:
        """将拼多多订单原始数据转为 OrderDTO"""
        return OrderDTO(
            platform_order_id=str(raw.get("order_sn", "")),
            product_id=str(raw.get("goods_id", "")),
            product_title=raw.get("goods_name", ""),
            buyer_id=str(raw.get("buyer_id", "")),
            quantity=raw.get("goods_count", 1),
            unit_price=float(raw.get("goods_price", 0)) / 100,
            total_amount=float(raw.get("pay_amount", 0)) / 100,
            status=self._map_order_status(raw.get("order_status", 0)),
            paid_at=datetime.fromtimestamp(raw["confirm_time"]) if raw.get("confirm_time") else None,
            shipped_at=datetime.fromtimestamp(raw["shipping_time"]) if raw.get("shipping_time") else None,
            platform_data=raw,
        )

    @staticmethod
    def _map_order_status(pdd_status: int) -> str:
        """拼多多订单状态映射"""
        status_map = {
            1: "pending",
            2: "paid",
            3: "shipped",
            5: "completed",
            6: "refunded",
            7: "cancelled",
        }
        return status_map.get(pdd_status, "pending")

    async def fetch_order_detail(self, order_id: str) -> OrderDTO:
        """获取拼多多订单详情"""
        result = await self.client.call_api(
            method="pdd.order.information.get",
            params={"order_sn": order_id},
            access_token=self.access_token,
        )
        order_info = result.get("order_information_get_response", {}).get("order_info", {})
        return self._parse_order(order_info)
```

**Step 3: 编写适配器工厂**

```python
# backend/services/platform/adapter_factory.py
"""平台适配器工厂"""
from models.platform import PlatformConfig
from services.platform.base_adapter import BasePlatformAdapter
from services.platform.pdd_adapter import PddAdapter


def create_adapter(config: PlatformConfig) -> BasePlatformAdapter:
    """根据平台配置创建对应的适配器实例"""
    adapters = {
        "pinduoduo": PddAdapter,
    }

    adapter_class = adapters.get(config.platform_type)
    if not adapter_class:
        raise ValueError(f"不支持的平台类型: {config.platform_type}")

    return adapter_class(
        app_key=config.app_key,
        app_secret=config.app_secret,
        access_token=config.access_token,
    )
```

**Step 4: 运行验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot/backend && python -c "from services.platform.adapter_factory import create_adapter; from services.platform.base_adapter import BasePlatformAdapter; print('OK')"`
Expected: OK

**Step 5: 提交**

```bash
git add backend/services/platform/base_adapter.py backend/services/platform/pdd_adapter.py backend/services/platform/adapter_factory.py
git commit -m "feat: add platform adapter abstraction with PDD implementation"
```

---

### Task 5: 创建商品同步服务

**Files:**
- Create: `backend/services/product_sync_service.py`

**Step 1: 编写同步服务**

```python
# backend/services/product_sync_service.py
"""商品同步服务"""
import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.platform import PlatformConfig
from models.product import (
    PlatformSyncTask, Product, ProductSyncSchedule,
    SyncTaskStatus, SyncTarget, SyncType,
)
from services.knowledge_service import KnowledgeService
from services.platform.adapter_factory import create_adapter

logger = logging.getLogger(__name__)


class ProductSyncService:
    """商品同步服务

    负责从电商平台拉取商品数据，写入 Product 表，
    并自动生成知识库条目。
    """

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ===== 商品 CRUD =====

    async def list_products(
        self,
        keyword: str | None = None,
        category: str | None = None,
        status: str | None = None,
        platform_config_id: int | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[Product], int]:
        """查询商品列表"""
        conditions = [Product.tenant_id == self.tenant_id]
        if keyword:
            conditions.append(Product.title.ilike(f"%{keyword}%"))
        if category:
            conditions.append(Product.category == category)
        if status:
            conditions.append(Product.status == status)
        if platform_config_id:
            conditions.append(Product.platform_config_id == platform_config_id)

        # 总数
        count_stmt = select(func.count(Product.id)).where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # 分页
        stmt = (
            select(Product)
            .where(and_(*conditions))
            .order_by(Product.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        products = list(result.scalars().all())

        return products, total

    async def get_product(self, product_id: int) -> Product | None:
        """获取商品详情"""
        stmt = select(Product).where(
            and_(Product.id == product_id, Product.tenant_id == self.tenant_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # ===== 同步逻辑 =====

    async def trigger_sync(
        self, platform_config_id: int, sync_type: str = "full"
    ) -> PlatformSyncTask:
        """触发同步任务"""
        # 检查是否有正在运行的同步任务
        stmt = select(PlatformSyncTask).where(
            and_(
                PlatformSyncTask.tenant_id == self.tenant_id,
                PlatformSyncTask.platform_config_id == platform_config_id,
                PlatformSyncTask.sync_target == SyncTarget.PRODUCT.value,
                PlatformSyncTask.status.in_([
                    SyncTaskStatus.PENDING.value,
                    SyncTaskStatus.RUNNING.value,
                ]),
            )
        )
        existing = (await self.db.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ValueError("已有正在运行的同步任务，请等待完成后再试")

        task = PlatformSyncTask(
            tenant_id=self.tenant_id,
            platform_config_id=platform_config_id,
            sync_target=SyncTarget.PRODUCT.value,
            sync_type=sync_type,
            status=SyncTaskStatus.PENDING.value,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task

    async def execute_sync(self, task_id: int) -> None:
        """执行同步任务（由 Celery Task 调用）"""
        stmt = select(PlatformSyncTask).where(PlatformSyncTask.id == task_id)
        task = (await self.db.execute(stmt)).scalar_one_or_none()
        if not task:
            logger.error("同步任务不存在: %d", task_id)
            return

        # 获取平台配置
        config_stmt = select(PlatformConfig).where(
            PlatformConfig.id == task.platform_config_id
        )
        config = (await self.db.execute(config_stmt)).scalar_one_or_none()
        if not config:
            task.status = SyncTaskStatus.FAILED.value
            task.error_message = "平台配置不存在"
            await self.db.commit()
            return

        # 更新任务状态
        task.status = SyncTaskStatus.RUNNING.value
        task.started_at = datetime.utcnow()
        await self.db.commit()

        try:
            adapter = create_adapter(config)

            if task.sync_type == SyncType.FULL.value:
                await self._full_sync(adapter, config.id, task)
            else:
                await self._incremental_sync(adapter, config.id, task)

            task.status = SyncTaskStatus.COMPLETED.value
            task.completed_at = datetime.utcnow()
        except Exception as e:
            logger.exception("同步任务失败: %d", task_id)
            task.status = SyncTaskStatus.FAILED.value
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()

        await self.db.commit()

    async def _full_sync(
        self, adapter, platform_config_id: int, task: PlatformSyncTask
    ) -> None:
        """全量同步"""
        page = 1
        page_size = 50
        total_synced = 0
        total_failed = 0

        while True:
            result = await adapter.fetch_products(page=page, page_size=page_size)
            task.total_count = result.total

            for dto in result.items:
                try:
                    await self._upsert_product(platform_config_id, dto)
                    total_synced += 1
                except Exception as e:
                    logger.error("同步商品失败 %s: %s", dto.platform_product_id, e)
                    total_failed += 1

            task.synced_count = total_synced
            task.failed_count = total_failed
            await self.db.commit()

            if page * page_size >= result.total:
                break
            page += 1

    async def _incremental_sync(
        self, adapter, platform_config_id: int, task: PlatformSyncTask
    ) -> None:
        """增量同步"""
        # 获取上次同步时间
        schedule_stmt = select(ProductSyncSchedule).where(
            and_(
                ProductSyncSchedule.tenant_id == self.tenant_id,
                ProductSyncSchedule.platform_config_id == platform_config_id,
            )
        )
        schedule = (await self.db.execute(schedule_stmt)).scalar_one_or_none()
        since = schedule.last_run_at if schedule and schedule.last_run_at else (
            datetime.utcnow() - timedelta(hours=1)
        )

        updated_products = await adapter.fetch_updated_products(since)
        task.total_count = len(updated_products)

        total_synced = 0
        total_failed = 0
        for dto in updated_products:
            try:
                await self._upsert_product(platform_config_id, dto)
                total_synced += 1
            except Exception as e:
                logger.error("增量同步商品失败 %s: %s", dto.platform_product_id, e)
                total_failed += 1

        task.synced_count = total_synced
        task.failed_count = total_failed

        # 更新调度时间
        if schedule:
            schedule.last_run_at = datetime.utcnow()
            schedule.next_run_at = datetime.utcnow() + timedelta(minutes=schedule.interval_minutes)

    async def _upsert_product(self, platform_config_id: int, dto) -> Product:
        """新增或更新商品"""
        stmt = select(Product).where(
            and_(
                Product.tenant_id == self.tenant_id,
                Product.platform_config_id == platform_config_id,
                Product.platform_product_id == dto.platform_product_id,
            )
        )
        product = (await self.db.execute(stmt)).scalar_one_or_none()

        if product:
            # 更新
            product.title = dto.title
            product.description = dto.description
            product.price = dto.price
            product.original_price = dto.original_price
            product.category = dto.category
            product.images = dto.images
            product.videos = dto.videos
            product.attributes = dto.attributes
            product.sales_count = dto.sales_count
            product.stock = dto.stock
            product.status = dto.status
            product.platform_data = dto.platform_data
            product.last_synced_at = datetime.utcnow()
        else:
            # 新建
            product = Product(
                tenant_id=self.tenant_id,
                platform_config_id=platform_config_id,
                platform_product_id=dto.platform_product_id,
                title=dto.title,
                description=dto.description,
                price=dto.price,
                original_price=dto.original_price,
                category=dto.category,
                images=dto.images,
                videos=dto.videos,
                attributes=dto.attributes,
                sales_count=dto.sales_count,
                stock=dto.stock,
                status=dto.status,
                platform_data=dto.platform_data,
                last_synced_at=datetime.utcnow(),
            )
            self.db.add(product)

        await self.db.flush()

        # 自动生成/更新知识库条目
        await self._sync_to_knowledge_base(product)

        return product

    async def _sync_to_knowledge_base(self, product: Product) -> None:
        """将商品信息同步到知识库"""
        knowledge_service = KnowledgeService(self.db, self.tenant_id)

        # 格式化商品知识内容
        content_parts = [
            f"商品名称：{product.title}",
            f"价格：{product.price}元",
        ]
        if product.original_price:
            content_parts.append(f"原价：{product.original_price}元")
        if product.category:
            content_parts.append(f"分类：{product.category}")
        if product.description:
            content_parts.append(f"描述：{product.description}")
        if product.attributes:
            content_parts.append(f"规格：{product.attributes}")
        content_parts.append(f"库存：{product.stock}")
        content_parts.append(f"销量：{product.sales_count}")

        content = "\n".join(content_parts)

        if product.knowledge_base_id:
            # 更新已有知识库条目
            await knowledge_service.update_knowledge(
                knowledge_id=None,
                db_id=product.knowledge_base_id,
                title=product.title,
                content=content,
                category=product.category,
            )
        else:
            # 创建新的知识库条目
            kb = await knowledge_service.create_knowledge(
                knowledge_type="product",
                title=product.title,
                content=content,
                category=product.category,
                tags=["商品", "自动同步"],
            )
            product.knowledge_base_id = kb.id

    # ===== 同步调度 =====

    async def get_sync_schedule(self, platform_config_id: int) -> ProductSyncSchedule | None:
        """获取同步调度配置"""
        stmt = select(ProductSyncSchedule).where(
            and_(
                ProductSyncSchedule.tenant_id == self.tenant_id,
                ProductSyncSchedule.platform_config_id == platform_config_id,
            )
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def update_sync_schedule(
        self,
        platform_config_id: int,
        interval_minutes: int | None = None,
        is_active: bool | None = None,
    ) -> ProductSyncSchedule:
        """创建或更新同步调度配置"""
        schedule = await self.get_sync_schedule(platform_config_id)

        if not schedule:
            schedule = ProductSyncSchedule(
                tenant_id=self.tenant_id,
                platform_config_id=platform_config_id,
                interval_minutes=interval_minutes or 60,
                is_active=1 if is_active is not False else 0,
                next_run_at=datetime.utcnow() + timedelta(minutes=interval_minutes or 60),
            )
            self.db.add(schedule)
        else:
            if interval_minutes is not None:
                schedule.interval_minutes = interval_minutes
            if is_active is not None:
                schedule.is_active = 1 if is_active else 0
            if interval_minutes:
                schedule.next_run_at = datetime.utcnow() + timedelta(minutes=interval_minutes)

        await self.db.commit()
        await self.db.refresh(schedule)
        return schedule

    # ===== 同步任务查询 =====

    async def list_sync_tasks(
        self, platform_config_id: int | None = None, page: int = 1, size: int = 20
    ) -> tuple[list[PlatformSyncTask], int]:
        """查询同步任务列表"""
        conditions = [
            PlatformSyncTask.tenant_id == self.tenant_id,
            PlatformSyncTask.sync_target == SyncTarget.PRODUCT.value,
        ]
        if platform_config_id:
            conditions.append(PlatformSyncTask.platform_config_id == platform_config_id)

        count_stmt = select(func.count(PlatformSyncTask.id)).where(and_(*conditions))
        total = (await self.db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(PlatformSyncTask)
            .where(and_(*conditions))
            .order_by(PlatformSyncTask.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        result = await self.db.execute(stmt)
        tasks = list(result.scalars().all())

        return tasks, total
```

**Step 2: 运行验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot/backend && python -c "from services.product_sync_service import ProductSyncService; print('OK')"`
Expected: OK

**Step 3: 提交**

```bash
git add backend/services/product_sync_service.py
git commit -m "feat: add ProductSyncService with full/incremental sync and knowledge base integration"
```

---

### Task 6: 创建 Celery 同步任务

**Files:**
- Create: `backend/tasks/product_sync_tasks.py`
- Modify: `backend/tasks/celery_app.py`

**Step 1: 编写 Celery 任务**

```python
# backend/tasks/product_sync_tasks.py
"""商品同步 Celery 任务"""
import asyncio
import logging

from tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    name="tasks.product_sync_tasks.run_product_sync",
    soft_time_limit=1800,
    time_limit=1860,
)
def run_product_sync(task_id: int, tenant_id: str):
    """执行商品同步任务"""
    asyncio.run(_run_product_sync(task_id, tenant_id))


async def _run_product_sync(task_id: int, tenant_id: str):
    from db.session import async_session_factory
    from services.product_sync_service import ProductSyncService

    async with async_session_factory() as db:
        service = ProductSyncService(db, tenant_id)
        await service.execute_sync(task_id)


@celery_app.task(name="tasks.product_sync_tasks.run_scheduled_syncs")
def run_scheduled_syncs():
    """执行所有到期的定时同步任务"""
    asyncio.run(_run_scheduled_syncs())


async def _run_scheduled_syncs():
    from datetime import datetime
    from sqlalchemy import and_, select
    from db.session import async_session_factory
    from models.product import ProductSyncSchedule
    from services.product_sync_service import ProductSyncService

    async with async_session_factory() as db:
        now = datetime.utcnow()
        stmt = select(ProductSyncSchedule).where(
            and_(
                ProductSyncSchedule.is_active == 1,
                ProductSyncSchedule.next_run_at <= now,
            )
        )
        result = await db.execute(stmt)
        schedules = list(result.scalars().all())

        for schedule in schedules:
            try:
                service = ProductSyncService(db, schedule.tenant_id)
                task = await service.trigger_sync(
                    platform_config_id=schedule.platform_config_id,
                    sync_type="incremental",
                )
                # 异步执行同步
                run_product_sync.delay(task.id, schedule.tenant_id)
                logger.info(
                    "触发增量同步: tenant=%s, platform=%d",
                    schedule.tenant_id, schedule.platform_config_id,
                )
            except ValueError as e:
                logger.warning("跳过同步: %s", e)
            except Exception:
                logger.exception(
                    "触发定时同步失败: tenant=%s", schedule.tenant_id
                )
```

**Step 2: 在 `celery_app.py` 中注册任务模块和定时任务**

在 `backend/tasks/celery_app.py` 的 `include` 列表中添加：
```python
"tasks.product_sync_tasks",
```

在 `celery_app.conf.beat_schedule` 中添加：
```python
"run-scheduled-product-syncs": {
    "task": "tasks.product_sync_tasks.run_scheduled_syncs",
    "schedule": 300.0,  # 每5分钟检查一次
},
```

在 `task_routes` 中添加：
```python
"tasks.product_sync_tasks.*": {"queue": "data_processing"},
```

**Step 3: 运行验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot/backend && python -c "from tasks.product_sync_tasks import run_product_sync, run_scheduled_syncs; print('OK')"`
Expected: OK

**Step 4: 提交**

```bash
git add backend/tasks/product_sync_tasks.py backend/tasks/celery_app.py
git commit -m "feat: add Celery tasks for product sync and scheduled sync"
```

---

### Task 7: 创建商品 API 路由

**Files:**
- Create: `backend/api/routers/product.py`
- Modify: `backend/api/routers/__init__.py` (或 main.py 中的路由注册)

**Step 1: 编写路由文件**

```python
# backend/api/routers/product.py
"""商品管理 API 路由"""
from fastapi import APIRouter, Query

from api.dependencies import DBDep, TenantFlexDep
from schemas.base import ApiResponse, PaginatedResponse
from schemas.product import (
    ProductListQuery, ProductResponse,
    SyncScheduleResponse, SyncScheduleUpdate,
    SyncTaskResponse, TriggerSyncRequest,
)
from services.product_sync_service import ProductSyncService
from tasks.product_sync_tasks import run_product_sync

router = APIRouter(prefix="/products", tags=["商品管理"])


@router.get("", response_model=ApiResponse[PaginatedResponse[ProductResponse]])
async def list_products(
    tenant_id: TenantFlexDep,
    db: DBDep,
    keyword: str | None = None,
    category: str | None = None,
    status: str | None = None,
    platform_config_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """查询商品列表"""
    service = ProductSyncService(db, tenant_id)
    products, total = await service.list_products(
        keyword=keyword,
        category=category,
        status=status,
        platform_config_id=platform_config_id,
        page=page,
        size=size,
    )
    paginated = PaginatedResponse.create(
        items=products, total=total, page=page, size=size
    )
    return ApiResponse(data=paginated)


@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
async def get_product(
    product_id: int,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """获取商品详情"""
    service = ProductSyncService(db, tenant_id)
    product = await service.get_product(product_id)
    if not product:
        return ApiResponse(success=False, error={"code": "NOT_FOUND", "message": "商品不存在"})
    return ApiResponse(data=product)


# ===== 同步相关 =====

@router.post("/sync", response_model=ApiResponse[SyncTaskResponse])
async def trigger_sync(
    request: TriggerSyncRequest,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """触发商品同步"""
    service = ProductSyncService(db, tenant_id)
    try:
        task = await service.trigger_sync(
            platform_config_id=request.platform_config_id,
            sync_type=request.sync_type,
        )
    except ValueError as e:
        return ApiResponse(success=False, error={"code": "SYNC_CONFLICT", "message": str(e)})

    # 异步执行
    run_product_sync.delay(task.id, tenant_id)

    return ApiResponse(data=task)


@router.get("/sync/tasks", response_model=ApiResponse[PaginatedResponse[SyncTaskResponse]])
async def list_sync_tasks(
    tenant_id: TenantFlexDep,
    db: DBDep,
    platform_config_id: int | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
):
    """查询同步任务列表"""
    service = ProductSyncService(db, tenant_id)
    tasks, total = await service.list_sync_tasks(
        platform_config_id=platform_config_id,
        page=page,
        size=size,
    )
    paginated = PaginatedResponse.create(
        items=tasks, total=total, page=page, size=size
    )
    return ApiResponse(data=paginated)


# ===== 同步调度 =====

@router.get("/sync/schedule/{platform_config_id}", response_model=ApiResponse[SyncScheduleResponse | None])
async def get_sync_schedule(
    platform_config_id: int,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """获取同步调度配置"""
    service = ProductSyncService(db, tenant_id)
    schedule = await service.get_sync_schedule(platform_config_id)
    return ApiResponse(data=schedule)


@router.put("/sync/schedule/{platform_config_id}", response_model=ApiResponse[SyncScheduleResponse])
async def update_sync_schedule(
    platform_config_id: int,
    request: SyncScheduleUpdate,
    tenant_id: TenantFlexDep,
    db: DBDep,
):
    """更新同步调度配置"""
    service = ProductSyncService(db, tenant_id)
    schedule = await service.update_sync_schedule(
        platform_config_id=platform_config_id,
        interval_minutes=request.interval_minutes,
        is_active=request.is_active,
    )
    return ApiResponse(data=schedule)
```

**Step 2: 在主应用中注册路由**

在 FastAPI 应用的路由注册处（检查 `backend/main.py` 或 `backend/api/__init__.py`）添加：

```python
from api.routers.product import router as product_router
app.include_router(product_router, prefix="/api/v1")
```

**注意**：固定路由 `/sync`、`/sync/tasks`、`/sync/schedule/{id}` 必须在参数路由 `/{product_id}` 之前注册。当前文件中已按此顺序排列，但需要确认 FastAPI 处理顺序。如果有冲突，需要将 sync 路由的前缀改为 `/products/sync` 开头。

**Step 3: 运行验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot/backend && python -c "from api.routers.product import router; print('routes:', [r.path for r in router.routes])"`
Expected: 打印出所有路由路径

**Step 4: 提交**

```bash
git add backend/api/routers/product.py backend/main.py
git commit -m "feat: add product management API routes"
```

---

### Task 8: 创建前端类型定义和 API 函数

**Files:**
- Modify: `frontend/src/types/index.ts`
- Create: `frontend/src/lib/api/product.ts`

**Step 1: 在 `types/index.ts` 中添加商品相关类型**

```typescript
// ===== 商品管理 =====

interface Product {
  id: number;
  tenant_id: string;
  platform_config_id: number;
  platform_product_id: string;
  title: string;
  description: string | null;
  price: number;
  original_price: number | null;
  currency: string;
  category: string | null;
  images: string[] | null;
  videos: string[] | null;
  attributes: Record<string, unknown> | null;
  sales_count: number;
  stock: number;
  status: 'active' | 'inactive' | 'deleted';
  knowledge_base_id: number | null;
  last_synced_at: string | null;
  platform_data: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

interface SyncTask {
  id: number;
  tenant_id: string;
  platform_config_id: number;
  sync_target: 'product' | 'order';
  sync_type: 'full' | 'incremental';
  status: 'pending' | 'running' | 'completed' | 'failed';
  total_count: number;
  synced_count: number;
  failed_count: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

interface SyncSchedule {
  id: number;
  tenant_id: string;
  platform_config_id: number;
  interval_minutes: number;
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
  updated_at: string;
}
```

**Step 2: 创建 API 函数文件**

```typescript
// frontend/src/lib/api/product.ts
import apiClient from './client';
import type { ApiResponse, PaginatedResponse, Product, SyncTask, SyncSchedule } from '@/types';

export const productApi = {
  // ===== 商品 =====

  async listProducts(params?: {
    keyword?: string;
    category?: string;
    status?: string;
    platform_config_id?: number;
    page?: number;
    size?: number;
  }): Promise<ApiResponse<PaginatedResponse<Product>>> {
    const { data } = await apiClient.get('/products', { params });
    return data;
  },

  async getProduct(productId: number): Promise<ApiResponse<Product>> {
    const { data } = await apiClient.get(`/products/${productId}`);
    return data;
  },

  // ===== 同步 =====

  async triggerSync(platformConfigId: number, syncType: 'full' | 'incremental' = 'full'): Promise<ApiResponse<SyncTask>> {
    const { data } = await apiClient.post('/products/sync', {
      platform_config_id: platformConfigId,
      sync_type: syncType,
    });
    return data;
  },

  async listSyncTasks(params?: {
    platform_config_id?: number;
    page?: number;
    size?: number;
  }): Promise<ApiResponse<PaginatedResponse<SyncTask>>> {
    const { data } = await apiClient.get('/products/sync/tasks', { params });
    return data;
  },

  // ===== 同步调度 =====

  async getSyncSchedule(platformConfigId: number): Promise<ApiResponse<SyncSchedule | null>> {
    const { data } = await apiClient.get(`/products/sync/schedule/${platformConfigId}`);
    return data;
  },

  async updateSyncSchedule(
    platformConfigId: number,
    params: { interval_minutes?: number; is_active?: boolean }
  ): Promise<ApiResponse<SyncSchedule>> {
    const { data } = await apiClient.put(`/products/sync/schedule/${platformConfigId}`, params);
    return data;
  },
};
```

**Step 3: 在 `frontend/src/lib/api/index.ts` 中导出**

```typescript
export { productApi } from './product';
```

**Step 4: 提交**

```bash
git add frontend/src/types/index.ts frontend/src/lib/api/product.ts frontend/src/lib/api/index.ts
git commit -m "feat: add product types and API client functions"
```

---

### Task 9: 创建商品管理前端页面

**Files:**
- Create: `frontend/src/app/(dashboard)/products/page.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx` (添加菜单项)

**Step 1: 在 Sidebar 中添加「商品管理」菜单项**

在 `Sidebar.tsx` 的 `menuItems` 数组中，在 `知识库` 之后添加：

```typescript
{ key: '/products', icon: ShoppingOutlined, label: '商品管理' },
```

并在文件顶部导入 `ShoppingOutlined`：

```typescript
import { ShoppingOutlined } from '@ant-design/icons';
```

**Step 2: 创建商品管理页面**

```tsx
// frontend/src/app/(dashboard)/products/page.tsx
'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  Card, Table, Button, Input, Select, Space, Tag, Image,
  message, Modal, Typography, Descriptions, Progress, Tooltip,
  InputNumber, Switch, Row, Col, Statistic,
} from 'antd';
import {
  SyncOutlined, SearchOutlined, ShoppingOutlined,
  ClockCircleOutlined, CheckCircleOutlined, CloseCircleOutlined,
  LoadingOutlined,
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { productApi } from '@/lib/api/product';
import type { Product, SyncTask, SyncSchedule } from '@/types';

const { Search } = Input;
const { Text, Title } = Typography;

export default function ProductsPage() {
  // 商品列表状态
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [size, setSize] = useState(20);
  const [keyword, setKeyword] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [loading, setLoading] = useState(false);

  // 同步状态
  const [syncTasks, setSyncTasks] = useState<SyncTask[]>([]);
  const [syncSchedule, setSyncSchedule] = useState<SyncSchedule | null>(null);
  const [syncing, setSyncing] = useState(false);

  // 商品详情弹窗
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);

  // 同步配置弹窗
  const [scheduleOpen, setScheduleOpen] = useState(false);
  const [scheduleInterval, setScheduleInterval] = useState(60);
  const [scheduleActive, setScheduleActive] = useState(true);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await productApi.listProducts({
        keyword: keyword || undefined,
        status: statusFilter,
        page,
        size,
      });
      if (resp.success && resp.data) {
        setProducts(resp.data.items);
        setTotal(resp.data.total);
      }
    } catch {
      message.error('加载商品列表失败');
    } finally {
      setLoading(false);
    }
  }, [keyword, statusFilter, page, size]);

  const loadSyncTasks = useCallback(async () => {
    try {
      const resp = await productApi.listSyncTasks({ page: 1, size: 5 });
      if (resp.success && resp.data) {
        setSyncTasks(resp.data.items);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  useEffect(() => {
    loadSyncTasks();
  }, [loadSyncTasks]);

  const handleSync = async (syncType: 'full' | 'incremental') => {
    setSyncing(true);
    try {
      // TODO: 支持多平台选择，当前使用第一个平台
      const resp = await productApi.triggerSync(1, syncType);
      if (resp.success) {
        message.success('同步任务已创建');
        loadSyncTasks();
      } else {
        message.error(resp.error?.message || '触发同步失败');
      }
    } catch {
      message.error('触发同步失败');
    } finally {
      setSyncing(false);
    }
  };

  const handleSaveSchedule = async () => {
    try {
      // TODO: 支持多平台选择
      const resp = await productApi.updateSyncSchedule(1, {
        interval_minutes: scheduleInterval,
        is_active: scheduleActive,
      });
      if (resp.success) {
        message.success('同步配置已更新');
        setSyncSchedule(resp.data);
        setScheduleOpen(false);
      }
    } catch {
      message.error('更新同步配置失败');
    }
  };

  const statusTagMap: Record<string, { color: string; text: string }> = {
    active: { color: 'green', text: '在售' },
    inactive: { color: 'default', text: '下架' },
    deleted: { color: 'red', text: '已删除' },
  };

  const syncStatusTagMap: Record<string, { color: string; icon: React.ReactNode }> = {
    pending: { color: 'default', icon: <ClockCircleOutlined /> },
    running: { color: 'processing', icon: <LoadingOutlined /> },
    completed: { color: 'success', icon: <CheckCircleOutlined /> },
    failed: { color: 'error', icon: <CloseCircleOutlined /> },
  };

  const columns: ColumnsType<Product> = [
    {
      title: '商品图片',
      dataIndex: 'images',
      width: 80,
      render: (images: string[] | null) =>
        images && images.length > 0 ? (
          <Image src={images[0]} width={60} height={60} style={{ objectFit: 'cover', borderRadius: 4 }} />
        ) : (
          <div style={{ width: 60, height: 60, background: '#f0f0f0', borderRadius: 4, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <ShoppingOutlined style={{ fontSize: 20, color: '#999' }} />
          </div>
        ),
    },
    {
      title: '商品标题',
      dataIndex: 'title',
      ellipsis: true,
      render: (title: string, record) => (
        <a onClick={() => { setSelectedProduct(record); setDetailOpen(true); }}>{title}</a>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      width: 120,
      render: (price: number, record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ color: '#f5222d' }}>¥{price.toFixed(2)}</Text>
          {record.original_price && (
            <Text delete type="secondary" style={{ fontSize: 12 }}>¥{record.original_price.toFixed(2)}</Text>
          )}
        </Space>
      ),
    },
    {
      title: '分类',
      dataIndex: 'category',
      width: 100,
      render: (cat: string | null) => cat || '-',
    },
    {
      title: '销量',
      dataIndex: 'sales_count',
      width: 80,
      sorter: (a, b) => a.sales_count - b.sales_count,
    },
    {
      title: '库存',
      dataIndex: 'stock',
      width: 80,
    },
    {
      title: '状态',
      dataIndex: 'status',
      width: 80,
      render: (status: string) => {
        const tag = statusTagMap[status] || { color: 'default', text: status };
        return <Tag color={tag.color}>{tag.text}</Tag>;
      },
    },
    {
      title: '最近同步',
      dataIndex: 'last_synced_at',
      width: 160,
      render: (time: string | null) =>
        time ? new Date(time).toLocaleString('zh-CN') : '-',
    },
  ];

  return (
    <div style={{ padding: 24 }}>
      <Title level={4} style={{ marginBottom: 24 }}>
        <ShoppingOutlined style={{ marginRight: 8 }} />
        商品管理
      </Title>

      {/* 同步状态卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="商品总数" value={total} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="在售商品"
              value={products.filter(p => p.status === 'active').length}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="最近同步"
              value={
                syncTasks.length > 0 && syncTasks[0].completed_at
                  ? new Date(syncTasks[0].completed_at).toLocaleString('zh-CN')
                  : '暂无'
              }
              valueStyle={{ fontSize: 14 }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Space>
              <Button
                type="primary"
                icon={<SyncOutlined spin={syncing} />}
                loading={syncing}
                onClick={() => handleSync('full')}
              >
                全量同步
              </Button>
              <Button
                icon={<SyncOutlined />}
                onClick={() => handleSync('incremental')}
              >
                增量同步
              </Button>
              <Tooltip title="同步调度配置">
                <Button
                  icon={<ClockCircleOutlined />}
                  onClick={() => setScheduleOpen(true)}
                />
              </Tooltip>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 最近同步任务 */}
      {syncTasks.length > 0 && syncTasks[0].status === 'running' && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space>
            <LoadingOutlined />
            <Text>正在同步中...</Text>
            <Progress
              percent={
                syncTasks[0].total_count > 0
                  ? Math.round((syncTasks[0].synced_count / syncTasks[0].total_count) * 100)
                  : 0
              }
              size="small"
              style={{ width: 200 }}
            />
            <Text type="secondary">
              {syncTasks[0].synced_count}/{syncTasks[0].total_count}
            </Text>
          </Space>
        </Card>
      )}

      {/* 搜索和筛选 */}
      <Card style={{ marginBottom: 16 }}>
        <Space>
          <Search
            placeholder="搜索商品标题"
            allowClear
            style={{ width: 300 }}
            onSearch={(value) => { setKeyword(value); setPage(1); }}
          />
          <Select
            placeholder="商品状态"
            allowClear
            style={{ width: 120 }}
            value={statusFilter}
            onChange={(value) => { setStatusFilter(value); setPage(1); }}
            options={[
              { value: 'active', label: '在售' },
              { value: 'inactive', label: '下架' },
              { value: 'deleted', label: '已删除' },
            ]}
          />
        </Space>
      </Card>

      {/* 商品表格 */}
      <Card>
        <Table
          columns={columns}
          dataSource={products}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: size,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 件商品`,
            onChange: (p, s) => { setPage(p); setSize(s); },
          }}
        />
      </Card>

      {/* 商品详情弹窗 */}
      <Modal
        title="商品详情"
        open={detailOpen}
        onCancel={() => setDetailOpen(false)}
        footer={null}
        width={700}
      >
        {selectedProduct && (
          <Descriptions column={2} bordered size="small">
            <Descriptions.Item label="商品标题" span={2}>{selectedProduct.title}</Descriptions.Item>
            <Descriptions.Item label="价格">¥{selectedProduct.price}</Descriptions.Item>
            <Descriptions.Item label="原价">
              {selectedProduct.original_price ? `¥${selectedProduct.original_price}` : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="分类">{selectedProduct.category || '-'}</Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusTagMap[selectedProduct.status]?.color}>
                {statusTagMap[selectedProduct.status]?.text}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="销量">{selectedProduct.sales_count}</Descriptions.Item>
            <Descriptions.Item label="库存">{selectedProduct.stock}</Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>
              {selectedProduct.description || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="商品图片" span={2}>
              <Space>
                {selectedProduct.images?.map((img, idx) => (
                  <Image key={idx} src={img} width={80} height={80} style={{ objectFit: 'cover' }} />
                ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="知识库关联">
              {selectedProduct.knowledge_base_id ? (
                <Tag color="blue">已关联 (ID: {selectedProduct.knowledge_base_id})</Tag>
              ) : (
                <Tag>未关联</Tag>
              )}
            </Descriptions.Item>
            <Descriptions.Item label="最近同步">
              {selectedProduct.last_synced_at
                ? new Date(selectedProduct.last_synced_at).toLocaleString('zh-CN')
                : '-'}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 同步调度配置弹窗 */}
      <Modal
        title="同步调度配置"
        open={scheduleOpen}
        onCancel={() => setScheduleOpen(false)}
        onOk={handleSaveSchedule}
        okText="保存"
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <Text>启用定时同步</Text>
            <Switch
              checked={scheduleActive}
              onChange={setScheduleActive}
              style={{ marginLeft: 16 }}
            />
          </div>
          <div>
            <Text>同步间隔（分钟）</Text>
            <InputNumber
              min={10}
              max={1440}
              value={scheduleInterval}
              onChange={(v) => v && setScheduleInterval(v)}
              style={{ marginLeft: 16, width: 120 }}
            />
          </div>
          {syncSchedule && (
            <div>
              <Text type="secondary">
                上次同步：{syncSchedule.last_run_at ? new Date(syncSchedule.last_run_at).toLocaleString('zh-CN') : '暂无'}
              </Text>
              <br />
              <Text type="secondary">
                下次同步：{syncSchedule.next_run_at ? new Date(syncSchedule.next_run_at).toLocaleString('zh-CN') : '暂无'}
              </Text>
            </div>
          )}
        </Space>
      </Modal>
    </div>
  );
}
```

**Step 3: 提交**

```bash
git add frontend/src/app/\(dashboard\)/products/page.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "feat: add product management page with sync controls"
```

---

### Task 10: 集成测试与验证

**Step 1: 后端 API 验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot && docker compose build api celery-worker && docker compose up -d api celery-worker`

Run: `docker compose exec api alembic upgrade head`

Run: `curl -s http://localhost:8000/api/v1/products -H "Authorization: Bearer <test-token>" | python -m json.tool`
Expected: 返回 `{"success": true, "data": {"items": [], "total": 0, ...}}`

**Step 2: 前端验证**

Run: `cd /Users/zhulang/work/ecom-chat-bot && docker compose build frontend && docker compose up -d frontend`

验证：浏览器访问 `/products` 页面，应显示商品管理界面。

**Step 3: 提交**

```bash
git add -A
git commit -m "feat: complete stage 1 - product sync and knowledge base integration"
```

---

## 阶段 2：AI 内容生成 + 一键上传（功能 1, 2, 3）

### Task 11: 扩展 ModelType 枚举

**Files:**
- Modify: `backend/models/model_config.py` — 在 ModelType 中添加 `IMAGE_GENERATION = "image_generation"` 和 `VIDEO_GENERATION = "video_generation"`
- Create: `backend/migrations/versions/014_add_generation_model_types.py` — 更新 model_type 的注释
- Modify: `frontend/src/types/index.ts` — ModelType 添加 `'image_generation' | 'video_generation'`
- Modify: `frontend/src/components/settings/ModelConfigForm.tsx` — PLATFORM_CATALOG 添加图像/视频生成支持

### Task 12: 创建 PromptTemplate 模型和迁移

**Files:**
- Create: `backend/models/prompt_template.py` — PromptTemplate ORM 模型
- Create: `backend/migrations/versions/015_add_prompt_templates.py`
- Create: `backend/schemas/prompt_template.py`
- Modify: `backend/models/__init__.py`

### Task 13: 创建 GenerationTask 和 GeneratedAsset 模型

**Files:**
- Create: `backend/models/generation.py` — GenerationTask + GeneratedAsset ORM 模型
- Create: `backend/migrations/versions/016_add_generation_tables.py`
- Create: `backend/schemas/generation.py`
- Modify: `backend/models/__init__.py`

### Task 14: 创建图像/视频模型路由器

**Files:**
- Create: `backend/services/content_generation/image_model_router.py` — 根据 provider 路由到不同图像生成 API
- Create: `backend/services/content_generation/video_model_router.py` — 根据 provider 路由到不同视频生成 API

### Task 15: 创建内容生成服务

**Files:**
- Create: `backend/services/content_generation/__init__.py`
- Create: `backend/services/content_generation/poster_service.py` — 海报生成（text_to_image, image_to_image）
- Create: `backend/services/content_generation/video_service.py` — 视频生成（text_to_video, image_to_video）
- Create: `backend/services/content_generation/prompt_template_service.py` — 模板 CRUD + 变量替换
- Create: `backend/services/content_generation/generation_service.py` — 统一任务管理（create/list/retry/cancel）

### Task 16: 创建内容生成 Celery 任务

**Files:**
- Create: `backend/tasks/generation_tasks.py` — 异步执行图像/视频生成
- Modify: `backend/tasks/celery_app.py` — 注册任务模块，配置长超时

### Task 17: 创建内容生成 API 路由

**Files:**
- Create: `backend/api/routers/content_generation.py` — 提示词模板 CRUD + 生成任务提交/查询
- Modify: `backend/main.py` — 注册路由

### Task 18: 创建素材上传到平台服务

**Files:**
- Create: `backend/services/content_generation/asset_upload_service.py` — 调用平台适配器上传图片/视频

### Task 19: 创建前端 API 函数和类型

**Files:**
- Modify: `frontend/src/types/index.ts` — PromptTemplate, GenerationTask, GeneratedAsset 类型
- Create: `frontend/src/lib/api/content.ts` — 内容生成相关 API 函数

### Task 20: 创建海报工作台页面

**Files:**
- Create: `frontend/src/app/(dashboard)/content/poster/page.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx` — 添加「内容创作」菜单组

### Task 21: 创建视频工作台页面

**Files:**
- Create: `frontend/src/app/(dashboard)/content/video/page.tsx`

### Task 22: 创建素材库页面

**Files:**
- Create: `frontend/src/app/(dashboard)/content/assets/page.tsx`

---

## 阶段 3：智能标题/描述生成 + 智能定价（功能 6）

### Task 23: 创建 CompetitorProduct 和 PricingAnalysis 模型

**Files:**
- Create: `backend/models/pricing.py`
- Create: `backend/migrations/versions/017_add_pricing_tables.py`
- Create: `backend/schemas/pricing.py`
- Modify: `backend/models/__init__.py`

### Task 24: 创建文案生成服务

**Files:**
- Create: `backend/services/content_generation/copywriting_service.py` — 标题/描述生成

### Task 25: 创建定价分析服务

**Files:**
- Create: `backend/services/pricing/pricing_service.py` — 定价分析逻辑
- Create: `backend/services/pricing/competitor_service.py` — 竞品数据管理（CRUD + CSV 导入）
- Create: `backend/services/pricing/__init__.py`

### Task 26: 创建定价 API 路由

**Files:**
- Create: `backend/api/routers/pricing.py`
- Modify: `backend/main.py`

### Task 27: 创建前端文案生成和定价组件

**Files:**
- Create: `frontend/src/components/product/CopywritingTab.tsx` — 嵌入商品详情的文案生成 Tab
- Create: `frontend/src/components/product/PricingTab.tsx` — 嵌入商品详情的定价分析 Tab
- Create: `frontend/src/lib/api/pricing.ts`
- Modify: `frontend/src/types/index.ts`

---

## 阶段 4：订单分析报告（功能 5）

### Task 28: 创建 Order 和 AnalysisReport 模型

**Files:**
- Create: `backend/models/order.py`
- Create: `backend/migrations/versions/018_add_order_tables.py`
- Create: `backend/schemas/order.py`
- Create: `backend/schemas/analysis_report.py`
- Modify: `backend/models/__init__.py`

### Task 29: 扩展商品同步服务支持订单同步

**Files:**
- Create: `backend/services/order_sync_service.py` — 订单同步逻辑
- Modify: `backend/tasks/product_sync_tasks.py` — 添加订单同步任务

### Task 30: 创建订单分析服务

**Files:**
- Create: `backend/services/order_analytics/__init__.py`
- Create: `backend/services/order_analytics/analytics_service.py` — SQL 统计 + 图表数据
- Create: `backend/services/order_analytics/report_service.py` — AI 分析 + PDF/Excel 生成

### Task 31: 创建分析报告 Celery 任务

**Files:**
- Create: `backend/tasks/analytics_tasks.py`
- Modify: `backend/tasks/celery_app.py`

### Task 32: 创建订单和分析 API 路由

**Files:**
- Create: `backend/api/routers/order.py`
- Create: `backend/api/routers/analysis_report.py`
- Modify: `backend/main.py`

### Task 33: 创建前端订单概览页面

**Files:**
- Create: `frontend/src/app/(dashboard)/analytics/orders/page.tsx`
- Create: `frontend/src/lib/api/analytics.ts`
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/layout/Sidebar.tsx`

### Task 34: 创建分析报告页面

**Files:**
- Create: `frontend/src/app/(dashboard)/analytics/reports/page.tsx`

### Task 35: 创建销售看板页面

**Files:**
- Create: `frontend/src/app/(dashboard)/analytics/dashboard/page.tsx` — 使用 @ant-design/charts 渲染图表
