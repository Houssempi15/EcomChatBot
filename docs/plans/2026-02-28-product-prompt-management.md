# 商品提示词管理模块 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将全局提示词模板改造为商品维度的提示词管理，新建 product_prompts 表，废弃旧 prompt_templates。

**Architecture:** 新建 ProductPrompt 模型和 ProductPromptService，替换旧的 PromptTemplate 体系。后端提供 CRUD API，前端新增独立管理页面，改造海报/视频生成页面的提示词选择逻辑。

**Tech Stack:** FastAPI + SQLAlchemy (async) + Alembic / Next.js 14 + Ant Design + TypeScript

---

## Task 1: 新建 ProductPrompt 数据模型

**Files:**
- Create: `backend/models/product_prompt.py`
- Modify: `backend/models/__init__.py:31,98-99`

**Step 1: 创建模型文件**

```python
# backend/models/product_prompt.py
"""商品提示词模型"""
from enum import Enum
from sqlalchemy import String, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from models.base import TenantBaseModel


class PromptType(str, Enum):
    """提示词类型"""
    IMAGE = "image"
    VIDEO = "video"
    TITLE = "title"
    DESCRIPTION = "description"


class ProductPrompt(TenantBaseModel):
    """商品提示词表"""
    __tablename__ = "product_prompts"
    __table_args__ = (
        Index("idx_product_prompt_tenant", "tenant_id"),
        Index("idx_product_prompt_product", "product_id"),
        Index("idx_product_prompt_product_type", "product_id", "prompt_type"),
        {"comment": "商品提示词表"},
    )

    product_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="关联商品ID"
    )
    prompt_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="提示词类型(image/video/title/description)"
    )
    name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="提示词名称"
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False, comment="提示词内容"
    )
    usage_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="使用次数"
    )

    def __repr__(self) -> str:
        return f"<ProductPrompt {self.name} ({self.prompt_type})>"
```

**Step 2: 在 `__init__.py` 中注册模型**

- 第31行附近：添加 `from models.product_prompt import ProductPrompt, PromptType`
- 第98-99行附近：将 `PromptTemplate, TemplateType` 替换为 `ProductPrompt, PromptType`

**Step 3: 提交**

```bash
git add backend/models/product_prompt.py backend/models/__init__.py
git commit -m "feat: add ProductPrompt model"
```

---

## Task 2: 数据库迁移

**Files:**
- Create: `backend/migrations/versions/019_add_product_prompts.py`

**Step 1: 创建迁移文件**

```python
# backend/migrations/versions/019_add_product_prompts.py
"""add product_prompts table and rename template_id to prompt_id

Revision ID: 019
Revises: 018
"""
from alembic import op

revision = "019"
down_revision = "018"


def upgrade():
    # 创建 product_prompts 表
    op.execute("""
        CREATE TABLE IF NOT EXISTS product_prompts (
            id SERIAL PRIMARY KEY,
            tenant_id VARCHAR(64) NOT NULL,
            product_id INTEGER NOT NULL,
            prompt_type VARCHAR(32) NOT NULL,
            name VARCHAR(128) NOT NULL,
            content TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_product_prompt_tenant ON product_prompts (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_product_prompt_product ON product_prompts (product_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_product_prompt_product_type ON product_prompts (product_id, prompt_type)")

    # GenerationTask: template_id → prompt_id
    op.execute("ALTER TABLE generation_tasks RENAME COLUMN template_id TO prompt_id")


def downgrade():
    op.execute("ALTER TABLE generation_tasks RENAME COLUMN prompt_id TO template_id")
    op.execute("DROP TABLE IF EXISTS product_prompts")
```

**Step 2: 提交**

```bash
git add backend/migrations/versions/019_add_product_prompts.py
git commit -m "migration: add product_prompts table, rename template_id to prompt_id"
```

---

## Task 3: 后端 ProductPromptService

**Files:**
- Create: `backend/services/content_generation/product_prompt_service.py`

**Step 1: 创建服务文件**

```python
# backend/services/content_generation/product_prompt_service.py
"""商品提示词管理服务"""
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.product_prompt import ProductPrompt


class ProductPromptService:
    """商品提示词 CRUD"""

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def create_prompt(
        self, product_id: int, prompt_type: str, name: str, content: str,
    ) -> ProductPrompt:
        prompt = ProductPrompt(
            tenant_id=self.tenant_id,
            product_id=product_id,
            prompt_type=prompt_type,
            name=name,
            content=content,
        )
        self.db.add(prompt)
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def get_prompt(self, prompt_id: int) -> ProductPrompt | None:
        stmt = select(ProductPrompt).where(
            and_(ProductPrompt.id == prompt_id, ProductPrompt.tenant_id == self.tenant_id)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def list_prompts(
        self,
        product_id: int | None = None,
        prompt_type: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> tuple[list[ProductPrompt], int]:
        conditions = [ProductPrompt.tenant_id == self.tenant_id]
        if product_id:
            conditions.append(ProductPrompt.product_id == product_id)
        if prompt_type:
            conditions.append(ProductPrompt.prompt_type == prompt_type)

        total = (await self.db.execute(
            select(func.count(ProductPrompt.id)).where(and_(*conditions))
        )).scalar() or 0

        stmt = (
            select(ProductPrompt)
            .where(and_(*conditions))
            .order_by(ProductPrompt.updated_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        items = list((await self.db.execute(stmt)).scalars().all())
        return items, total

    async def update_prompt(self, prompt_id: int, **kwargs) -> ProductPrompt | None:
        prompt = await self.get_prompt(prompt_id)
        if not prompt:
            return None
        for key, value in kwargs.items():
            if hasattr(prompt, key) and value is not None:
                setattr(prompt, key, value)
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def delete_prompt(self, prompt_id: int) -> bool:
        prompt = await self.get_prompt(prompt_id)
        if not prompt:
            return False
        await self.db.delete(prompt)
        await self.db.commit()
        return True

    async def increment_usage(self, prompt_id: int) -> None:
        prompt = await self.get_prompt(prompt_id)
        if prompt:
            prompt.usage_count += 1
            await self.db.commit()
```

**Step 2: 提交**

```bash
git add backend/services/content_generation/product_prompt_service.py
git commit -m "feat: add ProductPromptService"
```

---

## Task 4: 后端 API — 提示词 CRUD 端点

**Files:**
- Modify: `backend/api/routers/content_generation.py:21-107` (替换旧模板端点)
- Modify: `backend/schemas/` (如有模板相关 schema 需更新)

**Step 1: 在 content_generation.py 中替换旧模板端点（第21-107行）为新的提示词端点**

替换为以下端点：
- `GET /content/prompts` — 查询提示词列表（支持 product_id, prompt_type, page, size）
- `POST /content/prompts` — 创建提示词（body: product_id, prompt_type, name, content）
- `PUT /content/prompts/{prompt_id}` — 更新提示词（body: name?, content?）
- `DELETE /content/prompts/{prompt_id}` — 删除提示词

导入改为 `from services.content_generation.product_prompt_service import ProductPromptService`

**Step 2: 修改生成任务端点**

- `POST /content/generate` 中 `template_id` 参数改为 `prompt_id`
- 对应的 request schema 也需更新

**Step 3: 提交**

```bash
git add backend/api/routers/content_generation.py
git commit -m "feat: replace template endpoints with product prompt CRUD"
```

---

## Task 5: 后端 — 改造 GenerationService

**Files:**
- Modify: `backend/services/content_generation/generation_service.py:69-96`
- Modify: `backend/models/generation.py:61-63`

**Step 1: 修改 GenerationTask 模型**

`backend/models/generation.py` 第61-63行：`template_id` 改为 `prompt_id`

**Step 2: 修改 generation_service.py 的 create_task 方法**

- 删除旧的模板渲染逻辑（第69-96行的 PromptTemplateService 调用和变量替换）
- 替换为：如果传了 `prompt_id`，从 `ProductPromptService` 获取提示词内容作为 `final_prompt`
- 如果同时传了手动 `prompt`，追加到后面
- 调用 `increment_usage`
- 方法签名中 `template_id` 改为 `prompt_id`

**Step 3: 删除旧的 import**

删除 `from services.content_generation.prompt_template_service import PromptTemplateService`

**Step 4: 提交**

```bash
git add backend/services/content_generation/generation_service.py backend/models/generation.py
git commit -m "refactor: replace template rendering with product prompt in GenerationService"
```

---

## Task 6: 后端 — 清理旧代码

**Files:**
- Delete: `backend/models/prompt_template.py`
- Delete: `backend/services/content_generation/prompt_template_service.py`
- Modify: `backend/models/__init__.py` (移除旧导入)

**Step 1: 删除旧文件**

```bash
rm backend/models/prompt_template.py
rm backend/services/content_generation/prompt_template_service.py
```

**Step 2: 清理 `__init__.py` 中的旧导入**

**Step 3: 提交**

```bash
git add -A
git commit -m "chore: remove deprecated PromptTemplate and PromptTemplateService"
```

---

## Task 7: 前端 — API 层改造

**Files:**
- Modify: `frontend/src/lib/api/content.ts:6-17,27,58-96`

**Step 1: 替换类型定义**

将 `PromptTemplate` 类型替换为 `ProductPrompt`：
```typescript
export interface ProductPrompt {
  id: number;
  product_id: number;
  prompt_type: 'image' | 'video' | 'title' | 'description';
  name: string;
  content: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
}
```

`GenerationTask` 中 `template_id` 改为 `prompt_id`。

**Step 2: 替换 API 方法**

删除旧的 `listTemplates/createTemplate/getTemplate/updateTemplate/deleteTemplate`，替换为：
```typescript
listPrompts(params?: { product_id?: number; prompt_type?: string; page?: number; size?: number })
createPrompt(body: { product_id: number; prompt_type: string; name: string; content: string })
updatePrompt(promptId: number, body: { name?: string; content?: string })
deletePrompt(promptId: number)
```

`createGeneration` 中 `template_id` 改为 `prompt_id`。

**Step 3: 提交**

```bash
git add frontend/src/lib/api/content.ts
git commit -m "refactor: replace template API with product prompt API"
```

---

## Task 8: 前端 — 独立提示词管理页面

**Files:**
- Create: `frontend/src/app/(dashboard)/content/prompts/page.tsx`
- Modify: `frontend/src/components/layout/Sidebar.tsx:57` (添加菜单项)

**Step 1: 创建提示词管理页面**

页面结构：
- 顶部筛选栏：商品下拉 + 类型筛选 Tag（image/video/title/description）
- 主体：Ant Design Table（列：名称、类型 Tag、关联商品、使用次数、创建时间、操作）
- 操作：编辑（Modal）、删除（Popconfirm）
- 新增按钮：打开 Modal（选择商品、类型、名称、内容）

**Step 2: 在 Sidebar.tsx 第57行后添加菜单项**

```typescript
{ key: '/content/prompts', icon: <FormOutlined />, label: '提示词管理' },
```

**Step 3: 提交**

```bash
git add frontend/src/app/\(dashboard\)/content/prompts/page.tsx frontend/src/components/layout/Sidebar.tsx
git commit -m "feat: add product prompt management page"
```

---

## Task 9: 前端 — 改造海报生成页面

**Files:**
- Modify: `frontend/src/app/(dashboard)/content/poster/page.tsx`

**Step 1: 清理旧模板代码**

- 删除 `selectedTemplate` state（第24行）
- 删除 `templates` state（第30行）
- 删除模板弹窗 state（第35-38行）
- 删除 `handleCreateTemplate` 方法（第92-110行）
- 删除模板选择 UI（第162-181行）
- 删除新建模板弹窗（第314-335行）
- 删除 `loadData` 中的 `contentApi.listTemplates` 调用

**Step 2: 添加提示词选择逻辑**

- 新增 `prompts` state 和 `selectedPrompt` state
- 当 `selectedProduct` 变化时，调用 `contentApi.listPrompts({ product_id, prompt_type: 'image' })` 加载提示词
- 在商品选择器下方添加提示词 Select（仅当选了商品时显示）
- 选中提示词后自动填充 content 到 prompt 输入框
- `handleGenerate` 中传递 `prompt_id` 替代 `template_id`

**Step 3: 提交**

```bash
git add frontend/src/app/\(dashboard\)/content/poster/page.tsx
git commit -m "refactor: replace template selector with product prompt in poster page"
```

---

## Task 10: 前端 — 改造视频生成页面

**Files:**
- Modify: `frontend/src/app/(dashboard)/content/video/page.tsx`

**Step 1: 同 Task 9 模式改造**

- 删除 `selectedTemplate`、`templates` state
- 删除 `loadData` 中的 `contentApi.listTemplates` 调用
- 删除模板选择 UI（第148-164行）
- 新增 `prompts`、`selectedPrompt` state
- 选择商品后加载 `prompt_type: 'video'` 的提示词
- 提示词 Select 仅当选了商品时显示
- `handleGenerate` 中传递 `prompt_id`

**Step 2: 提交**

```bash
git add frontend/src/app/\(dashboard\)/content/video/page.tsx
git commit -m "refactor: replace template selector with product prompt in video page"
```

---

## Task 11: 前端 — 商品列表页添加"管理提示词"入口

**Files:**
- Modify: `frontend/src/app/(dashboard)/products/page.tsx:186-192`

**Step 1: 在商品表格操作列添加按钮**

在第186-192行的操作列中添加"管理提示词"按钮，点击后弹出 Modal 展示该商品的提示词列表，支持快速新增/编辑/删除。

**Step 2: 提交**

```bash
git add frontend/src/app/\(dashboard\)/products/page.tsx
git commit -m "feat: add prompt management entry in product list"
```

---

## Task 12: 部署验证

**Step 1: 重新部署**

```bash
docker compose build api celery-worker frontend && docker compose up -d api celery-worker frontend
```

**Step 2: 验证清单**

1. 访问提示词管理页面，确认能按商品和类型筛选
2. 为某商品创建一条 image 类型提示词
3. 进入海报生成页面，选择该商品，确认提示词下拉框出现
4. 选择提示词后生成海报，确认任务正常执行
5. 不选商品直接手动输入提示词生成，确认也能正常工作
6. 视频生成页面同理验证
7. 商品列表页"管理提示词"按钮功能正常
