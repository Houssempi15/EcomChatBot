#!/usr/bin/env python3
"""
测试 Milvus 云端连接
"""
import sys
from pymilvus import connections, utility

# 云端 Milvus 配置
MILVUS_URI = "https://in03-deb5691449f849a.serverless.ali-cn-hangzhou.cloud.zilliz.com.cn"
MILVUS_TOKEN = "your-milvus-token-here"

def test_connection():
    """测试连接"""
    try:
        print("正在连接到 Milvus 云端...")
        connections.connect(
            alias="default",
            uri=MILVUS_URI,
            token=MILVUS_TOKEN,
        )
        print("✓ 连接成功!")

        # 获取版本信息
        print(f"\n服务器版本: {utility.get_server_version()}")

        # 列出所有 collections
        collections = utility.list_collections()
        print(f"\n现有 Collections: {collections if collections else '(无)'}")

        # 断开连接
        connections.disconnect("default")
        print("\n✓ 测试完成")
        return True

    except Exception as e:
        print(f"\n✗ 连接失败: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
