# Milvus 云服务迁移 - 快速参考

## 迁移状态: ✅ 完成

迁移日期: 2026-03-01

## 关键变更

### 配置变更
```bash
# 旧配置 (已移除)
MILVUS_HOST=milvus
MILVUS_PORT=19530

# 新配置
MILVUS_URI=https://in03-deb5691449f849a.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn
MILVUS_TOKEN=your-milvus-token-here
```

### 服务变更
- ❌ 移除: `milvus`, `milvus-etcd`, `milvus-minio`
- ✅ 新增: `minio` (独立的对象存储服务)
- ✅ 保留: `postgres`, `redis`, `api`, `celery-worker`, `frontend`

## 验证命令

```bash
# 查看服务状态
docker compose ps

# 健康检查
curl http://localhost:8000/api/v1/health/ready | python3 -m json.tool

# 查看日志
docker compose logs api --tail 50

# 测试 Milvus 连接
python test_milvus_connection.py
```

## 常用命令

```bash
# ���启服务
docker compose restart api celery-worker

# 查看 API 日志
docker compose logs -f api

# 重新构建并部署
docker compose build api celery-worker frontend
docker compose up -d api celery-worker frontend

# 清理旧数据卷
./cleanup_old_volumes.sh
```

## 故障排查

### Milvus 连接失败
1. 检查网络连接: `curl -I https://in03-deb5691449f849a.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn`
2. 验证 Token 是否正确
3. 检查防火墙设置

### MinIO 连接失败
1. 确认 MinIO 服务运行: `docker compose ps minio`
2. 检查端口占用: `lsof -i :9000`
3. 查看 MinIO 日志: `docker compose logs minio`

## 重要提示

⚠️ **数据迁移**: 当前迁移不包含数据迁移,云端 Milvus 是全新实例
⚠️ **Token 安全**: 不要将 Token 提交到版本控制
⚠️ **成本监控**: Zilliz Cloud 按使用量计费,建议定期检查

## 相关文件

- `MILVUS_MIGRATION_REPORT.md` - 完整迁移报告
- `test_milvus_connection.py` - 连接测试脚本
- `cleanup_old_volumes.sh` - 数据卷清理脚本
- `docker-compose.yml` - Docker 服务配置
- `backend/.env` - 环境变量配置

## 支持

如有问题,请查看完整迁移报告: `MILVUS_MIGRATION_REPORT.md`
