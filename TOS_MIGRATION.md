# TOS 迁移部署指南

## 概述

本次更新将对象存储从 MinIO 迁移到火山引擎 TOS (Volcengine TOS)。

## 迁移前准备

### 1. 创建 TOS Bucket

1. 登录火山引擎控制台
2. 进入 TOS 服务
3. 创建一个新的 Bucket（建议名称：`ecom-chatbot`）
4. 记录以下信息：
   - Access Key
   - Secret Key
   - Endpoint（如：`tos-cn-beijing.volces.com`）
   - Region（如：`cn-beijing`）
   - Bucket 名称

### 2. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的 TOS 凭证：

```bash
TOS_ACCESS_KEY=your-actual-access-key
TOS_SECRET_KEY=your-actual-secret-key
TOS_ENDPOINT=tos-cn-beijing.volces.com
TOS_REGION=cn-beijing
TOS_BUCKET=ecom-chatbot
```

## 部署步骤

### 1. 停止现有服务

```bash
docker compose down
```

### 2. 清理 MinIO 数据（可选）

如果不再需要 MinIO 数据：

```bash
docker volume rm ecom-chat-bot_minio_data
```

### 3. 重新构建并启动服务

```bash
# 重新构建镜像
docker compose build api celery-worker frontend

# 启动服务
docker compose up -d
```

### 4. 验证部署

检查服务状态：

```bash
docker compose ps
docker compose logs api | grep -i "TOS"
```

应该看到类似的日志：

```
INFO: Initialized TOS storage backend
INFO: TOS bucket exists: ecom-chatbot
```

## 数据迁移（如果需要）

如果你有现有的 MinIO 数据需要迁移到 TOS：

### 方案 1: 使用 MinIO Client (mc)

```bash
# 配置 MinIO 源
mc alias set minio-source http://localhost:9000 minioadmin minioadmin

# 配置 TOS 目标（TOS 兼容 S3 协议）
mc alias set tos-target https://your-bucket.tos-cn-beijing.volces.com your-access-key your-secret-key

# 同步数据
mc mirror minio-source/ecom-chatbot tos-target/
```

### 方案 2: 使用 Python 脚本

创建 `migrate_storage.py`：

```python
import os
from minio import Minio
import tos

# MinIO 配置
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin",
    secure=False
)

# TOS 配置
tos_client = tos.TosClientV2(
    ak=os.getenv("TOS_ACCESS_KEY"),
    sk=os.getenv("TOS_SECRET_KEY"),
    endpoint=os.getenv("TOS_ENDPOINT"),
    region=os.getenv("TOS_REGION")
)

bucket = "ecom-chatbot"

# 列出所有对象
objects = minio_client.list_objects(bucket, recursive=True)

for obj in objects:
    print(f"Migrating: {obj.object_name}")

    # 从 MinIO 下载
    data = minio_client.get_object(bucket, obj.object_name)
    content = data.read()

    # 上传到 TOS
    tos_client.put_object(
        bucket=bucket,
        key=obj.object_name,
        content=content
    )

    print(f"✓ Migrated: {obj.object_name}")

print("Migration completed!")
```

运行迁移：

```bash
python migrate_storage.py
```

## 回滚方案

如果需要回滚到 MinIO：

1. 恢复 `docker-compose.yml` 中的 MinIO 服务配置
2. 恢复 `backend/requirements.txt` 中的 `minio>=7.2.0`
3. 恢复 `backend/services/storage_service.py` 的旧版本
4. 重新构建并部署

```bash
git revert HEAD
docker compose build api celery-worker
docker compose up -d
```

## 注意事项

1. **URL 格式变化**：TOS 使用预签名 URL（有效期 7 天），而 MinIO 使用永久公开 URL
2. **成本**：TOS 按使用量计费，请关注存储和流量成本
3. **性能**：TOS 是云服务，网络延迟可能比本地 MinIO 稍高
4. **安全**：确保 `.env` 文件不要提交到 Git（已在 `.gitignore` 中）

## 故障排查

### 问题 1: TOS 连接失败

检查：
- Access Key 和 Secret Key 是否正确
- Endpoint 和 Region 是否匹配
- 网络是否可以访问火山引擎服务

### 问题 2: Bucket 不存在

TOS 后端会自动创建 Bucket，如果失败：
- 检查账号权限
- 手动在控制台创建 Bucket

### 问题 3: 文件上传失败

检查日志：

```bash
docker compose logs api | grep -i "error\|failed"
```

常见原因：
- 文件大小超限
- 网络超时
- 权限不足

## 技术支持

如有问题，请查看：
- 火山引擎 TOS 文档：https://www.volcengine.com/docs/6349
- 项目 Issue：https://github.com/your-repo/issues
