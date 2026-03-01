# Milvus 云服务迁移完成报告

## 迁移概述

已成功将项目从本地 Docker 部署的 Milvus Standalone 迁移到阿里云 Zilliz Cloud 的 Milvus Serverless 服务。

## 已完成的更改

### 1. Docker Compose 配置 (`docker-compose.yml`)

**移除的服务:**
- `milvus-etcd` - Milvus 元数据存储
- `milvus-minio` - Milvus 对象存储
- `milvus` - Milvus Standalone 主服务

**新增的服务:**
- `minio` - 独立的 MinIO 对象存储服务(用于应用资产存储)

**更新的配置:**
- API 服务不再依赖 `milvus` 服务
- 环境变量从 `MILVUS_HOST`/`MILVUS_PORT` 改为 `MILVUS_URI`/`MILVUS_TOKEN`
- MinIO 端点从 `milvus-minio:9000` 改为 `minio:9000`

**移除的数据卷:**
- `etcd_data`
- `milvus_data`

**保留的数据卷:**
- `minio_data` (用于应用资产存储)

### 2. 后端配置 (`backend/core/config.py`)

**移除的配置项:**
```python
milvus_host: str = "localhost"
milvus_port: int = 19530
milvus_user: str = ""
milvus_password: str = ""
```

**新增的配置项:**
```python
milvus_uri: str = ""
milvus_token: str = ""
```

### 3. 环境变量文件

**`backend/.env`:**
```bash
# 旧配置 (已移除)
MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_USER=
MILVUS_PASSWORD=

# 新配置
MILVUS_URI=https://in03-deb5691449f849a.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn
MILVUS_TOKEN=your-milvus-token-here
```

**`backend/.env.example`:**
```bash
MILVUS_URI=https://your-milvus-uri.cloud.zilliz.com
MILVUS_TOKEN=your-milvus-token
```

### 4. Milvus 服务连接逻辑 (`backend/services/milvus_service.py`)

**更新的 `_connect()` 方法:**
```python
connections.connect(
    alias="default",
    uri=settings.milvus_uri,
    token=settings.milvus_token,
)
```

### 5. 健康检查 (`backend/api/routers/health.py`)

**更新的 Milvus 健康检查:**
```python
connections.connect(
    alias="health_check",
    uri=settings.milvus_uri,
    token=settings.milvus_token,
    timeout=5,
)
```

## 云端 Milvus 信息

- **服务商**: 阿里云 Zilliz Cloud
- **服务类型**: Milvus Serverless
- **URI**: `https://in03-deb5691449f849a.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn`
- **版本**: Zilliz Cloud Vector Database (兼容 Milvus 2.6)
- **连接方式**: HTTPS (443 端口)
- **认证方式**: Token

## 连接测试结果

✓ 云端 Milvus 连接测试成功
- 服务器版本: Zilliz Cloud Vector Database (Compatible with Milvus 2.6)
- 当前 Collections: 无 (全新实例)

## 部署步骤

### 1. 停止现有服务
```bash
docker compose down
```

### 2. 清理旧的 Milvus 数据卷 (可选)
```bash
docker volume rm ecom-chat-bot_etcd_data
docker volume rm ecom-chat-bot_milvus_data
```

### 3. 重新构建并启动服务
```bash
docker compose build api celery-worker frontend
docker compose up -d
```

### 4. 验证服务状态
```bash
# 检查所有服务状态
docker compose ps

# 检查健康状态
curl http://localhost:8000/health/ready

# 查看 API 日志
docker compose logs api | grep Milvus
```

## 预期结果

✓ Docker Compose 不再包含 Milvus 相关服务 (milvus, milvus-etcd, milvus-minio)
✓ 后端通过 HTTPS 连接到阿里云 Milvus
✓ 独立的 MinIO 服务用于应用资产存储
✓ 系统启动更快 (减少 2 个容器: etcd, milvus)
✓ 降低本地资源占用

## 注意事项

### 1. 数据迁移
- 当前迁移不包含数据迁移
- 云端 Milvus 是全新的空实例
- 如需迁移现有数据,需要额外的导出/导入步骤

### 2. 网络访问
- 云端 Milvus 使用 HTTPS (443 端口)
- 确保后端容器可以访问外网

### 3. Token 安全
- Token 包含在环境变量中
- `.env` 文件已在 `.gitignore` 中,不会提交到版本控制

### 4. 成本考虑
- Zilliz Cloud Serverless 按使用量计费
- 建议监控使用情况

### 5. MinIO 服务
- 项目仍需要 MinIO 用于存储生成的图片、视频等资产
- 已添加独立的 MinIO 服务替代之前的 `milvus-minio`

## 回滚方案

如果迁移后出现问题,可以快速回滚:

1. 恢复 `docker-compose.yml` 中的 Milvus 服务配置
2. 恢复 `backend/core/config.py` 中的 host/port 配置
3. 恢复 `backend/.env` 中的环境变量
4. 重启服务: `docker compose up -d`

## 测试清单

- [x] 服务启动成功
- [x] 健康检查通过 (`/api/v1/health/ready`)
- [x] Milvus 连接正常 (状态: healthy)
- [x] 数据库连接正常 (延迟: 3.31ms)
- [x] Redis 连接正常 (延迟: 1.71ms)
- [ ] 知识库上传功能正常 (需要手动测试)
- [ ] RAG 对话功能正常 (需要手动测试)
- [ ] 向量检索功能正常 (需要手动测试)
- [ ] 多租户隔离正常工作 (需要手动测试)

## 验证结果

### 服务状态
```
NAME                         STATUS
ecom-chatbot-api             Up (健康)
ecom-chatbot-celery-worker   Up (健康)
ecom-chatbot-frontend        Up (健康)
ecom-chatbot-minio           Up (健康)
ecom-chatbot-postgres        Up (健康)
ecom-chatbot-redis           Up (健康)
```

### 健康检查结果
```json
{
    "status": "ready",
    "checks": {
        "database": {
            "status": "healthy",
            "latency_ms": 3.31
        },
        "redis": {
            "status": "healthy",
            "latency_ms": 1.71
        },
        "milvus": {
            "status": "healthy"
        }
    },
    "timestamp": "2026-03-01T09:42:54.727478"
}
```

### Milvus 连接测试
```
✓ 连接成功!
服务器版本: Zilliz Cloud Vector Database (Compatible with Milvus 2.6)
现有 Collections: (无)
✓ 测试完成
```

## 清理旧数据卷

可以安全删除以下数据卷:
- `ecom-chat-bot_etcd_data`
- `ecom-chat-bot_milvus_data`

运行清理脚本:
```bash
./cleanup_old_volumes.sh
```

或手动删除:
```bash
docker volume rm ecom-chat-bot_etcd_data
docker volume rm ecom-chat-bot_milvus_data
```

## 相关文件

- `docker-compose.yml` - Docker 服务配置
- `backend/core/config.py` - 应用配置
- `backend/.env` - 环境变量
- `backend/.env.example` - 环境变量示例
- `backend/services/milvus_service.py` - Milvus 服务
- `backend/api/routers/health.py` - 健康检查
- `test_milvus_connection.py` - 连接测试脚本

## 迁移日期

2026-03-01
