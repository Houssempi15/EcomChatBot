#!/bin/bash
# 清理旧的 Milvus 数据卷

echo "正在清理旧的 Milvus 相关数据卷..."

# 清理 ecom-chat-bot 项目的旧数据卷
docker volume rm ecom-chat-bot_etcd_data 2>/dev/null && echo "✓ 已删除 ecom-chat-bot_etcd_data" || echo "✗ ecom-chat-bot_etcd_data 不存在或无法删除"
docker volume rm ecom-chat-bot_milvus_data 2>/dev/null && echo "✓ 已删除 ecom-chat-bot_milvus_data" || echo "✗ ecom-chat-bot_milvus_data 不存在或无法删除"

echo ""
echo "清理完成!"
echo ""
echo "注意: minio_data 数据卷已保留,因为应用仍需要 MinIO 存储资产文件。"
