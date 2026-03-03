"""support multiple platform connections per tenant

Revision ID: 020_support_multiple_platforms
Revises: 019_add_product_prompts
Create Date: 2026-03-03

Description:
    - 删除 platform_configs 表的唯一索引 (tenant_id, platform_type)
    - 添加新的复合索引 (tenant_id, platform_type, shop_id) 防止重复店铺
    - 允许一个租户对接多个电商平台（包括同一平台的多个店铺）
"""

from alembic import op

revision = "020_support_multiple_platforms"
down_revision = "019_add_product_prompts"
branch_labels = None
depends_on = None


def upgrade():
    # 删除旧的唯一索引
    op.execute("DROP INDEX IF EXISTS idx_platform_config_tenant_type")

    # 添加新的复合索引（防止同一店铺重复对接）
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_platform_config_tenant_type_shop "
        "ON platform_configs (tenant_id, platform_type, shop_id)"
    )


def downgrade():
    # 恢复旧的唯一索引
    op.execute("DROP INDEX IF EXISTS idx_platform_config_tenant_type_shop")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_platform_config_tenant_type "
        "ON platform_configs (tenant_id, platform_type)"
    )
