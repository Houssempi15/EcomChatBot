"""添加 ISV 平台对接相关表和字段

Migration: 005
Date: 2026-03-06
Description: 创建 platform_apps, after_sale_records, webhook_events 表；
             扩展 platform_configs 表增加 ISV 授权相关字段。
"""

import asyncio
import sys
import os

# 让脚本能找到 backend 包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import text
from database import get_async_engine


async def upgrade():
    """正向迁移：创建新表、新索引、新字段"""
    engine = get_async_engine()

    async with engine.begin() as conn:
        # 创建 platform_apps 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS platform_apps (
                id SERIAL PRIMARY KEY,
                platform_type VARCHAR(32) UNIQUE NOT NULL,
                app_name VARCHAR(128) NOT NULL,
                app_key VARCHAR(128) NOT NULL,
                app_secret VARCHAR(512) NOT NULL,
                callback_url TEXT,
                webhook_url TEXT,
                scopes JSON,
                status VARCHAR(16) DEFAULT 'active',
                extra_config JSON,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))

        # 创建 after_sale_records 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS after_sale_records (
                id SERIAL PRIMARY KEY,
                tenant_id VARCHAR(64) NOT NULL,
                platform_config_id INTEGER NOT NULL,
                platform_aftersale_id VARCHAR(128) NOT NULL,
                order_id INTEGER,
                aftersale_type VARCHAR(32) DEFAULT 'refund_only',
                status VARCHAR(32) DEFAULT 'pending',
                reason TEXT,
                refund_amount FLOAT DEFAULT 0.0,
                buyer_id VARCHAR(128),
                platform_data JSON,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_aftersale_tenant_config
                ON after_sale_records(tenant_id, platform_config_id);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_aftersale_platform_id
                ON after_sale_records(platform_aftersale_id);
        """))

        # 创建 webhook_events 表
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS webhook_events (
                id SERIAL PRIMARY KEY,
                tenant_id VARCHAR(64) NOT NULL,
                event_id VARCHAR(128) NOT NULL,
                platform_type VARCHAR(32) NOT NULL,
                platform_config_id INTEGER,
                event_type VARCHAR(32) NOT NULL,
                payload JSON,
                status VARCHAR(16) DEFAULT 'received',
                retry_count INTEGER DEFAULT 0,
                error_message TEXT,
                processed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """))
        await conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_webhook_event_id
                ON webhook_events(event_id);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_webhook_event_status
                ON webhook_events(status);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_webhook_event_platform
                ON webhook_events(platform_type, platform_config_id);
        """))

        # 扩展 platform_configs 表
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS authorization_status VARCHAR(16) DEFAULT 'pending';
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS token_expires_at TIMESTAMP;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS refresh_expires_at TIMESTAMP;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS last_token_refresh TIMESTAMP;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS platform_app_id INTEGER;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS scopes JSON;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS webhook_secret VARCHAR(256);
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs ADD COLUMN IF NOT EXISTS extra_config JSON;
        """))

    print("✓ Migration 005 upgrade completed successfully.")


async def downgrade():
    """回滚迁移：删除新表、新字段"""
    engine = get_async_engine()

    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS webhook_events;"))
        await conn.execute(text("DROP TABLE IF EXISTS after_sale_records;"))
        await conn.execute(text("DROP TABLE IF EXISTS platform_apps;"))

        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS authorization_status;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS token_expires_at;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS refresh_expires_at;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS last_token_refresh;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS platform_app_id;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS scopes;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS webhook_secret;
        """))
        await conn.execute(text("""
            ALTER TABLE platform_configs DROP COLUMN IF EXISTS extra_config;
        """))

    print("✓ Migration 005 downgrade completed successfully.")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "upgrade"
    if action == "downgrade":
        asyncio.run(downgrade())
    else:
        asyncio.run(upgrade())
