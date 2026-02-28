"""add product_prompts table and rename template_id to prompt_id

Revision ID: 019_add_product_prompts
Revises: 018_add_order_tables
Create Date: 2026-02-28

Description:
    - 创建 product_prompts 表（商品提示词）
    - generation_tasks 表 template_id 改名为 prompt_id
"""

from alembic import op

revision = "019_add_product_prompts"
down_revision = "018_add_order_tables"
branch_labels = None
depends_on = None


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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
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
