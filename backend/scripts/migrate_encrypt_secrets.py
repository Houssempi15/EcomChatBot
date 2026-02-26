"""
将 platform_configs.app_secret 从明文迁移为 Fernet 加密存储

使用方式：
    cd backend
    python scripts/migrate_encrypt_secrets.py
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def main():
    from db import get_db
    from models.platform import PlatformConfig
    from core.crypto import encrypt_field, decrypt_field
    from sqlalchemy import select

    encrypted = 0
    skipped = 0

    async for db in get_db():
        result = await db.execute(select(PlatformConfig))
        configs = result.scalars().all()

        for config in configs:
            if not config.app_secret:
                skipped += 1
                continue
            # 判断是否已加密（Fernet 密文以 gAAAAA 开头）
            if config.app_secret.startswith("gAAAAA"):
                skipped += 1
                continue
            try:
                config.app_secret = encrypt_field(config.app_secret)
                encrypted += 1
            except Exception as e:
                print(f"[ERROR] tenant={config.tenant_id}: {e}")

        await db.commit()

    print(f"完成：加密 {encrypted} 条，跳过 {skipped} 条")


if __name__ == "__main__":
    asyncio.run(main())
