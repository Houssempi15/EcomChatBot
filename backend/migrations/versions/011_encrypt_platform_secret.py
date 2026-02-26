"""encrypt platform app_secret field

Revision ID: 011
Revises: 010
Create Date: 2026-02-26
"""
from alembic import op
import sqlalchemy as sa


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 扩展字段长度以容纳 Fernet 密文（明文 ~40 字节 → 密文 ~120 字节）
    op.alter_column(
        "platform_configs",
        "app_secret",
        existing_type=sa.String(255),
        type_=sa.String(512),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "platform_configs",
        "app_secret",
        existing_type=sa.String(512),
        type_=sa.String(255),
        existing_nullable=True,
    )
