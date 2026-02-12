# 快速开始指南

## 🚀 5分钟快速上手

### 步骤1: 安装依赖 (1分钟)

```bash
cd backend/tests
pip install -r requirements-test.txt
```

### 步骤2: 配置环境 (2分钟)

创建 `.env.test.local` 文件：

```bash
# 测试环境URL（必填）
TEST_BASE_URL=http://115.190.75.88:8000

# 如果需要测试AI对话功能（可选）
TEST_LLM_PROVIDER=zhipuai
TEST_ZHIPUAI_API_KEY=your_zhipuai_api_key

# 如果有管理员账号（可选）
TEST_ADMIN_USERNAME=admin
TEST_ADMIN_PASSWORD=admin123
```

### 步骤3: 运行测试 (2分钟)

```bash
# 快速测试（推荐首次使用）
./run_tests.sh --quick

# 或使用pytest直接运行
pytest -m "not slow"
```

## 📋 测试结果

测试完成后查看报告：

```bash
# macOS
open reports/html/report.html

# Linux
xdg-open reports/html/report.html

# Windows
start reports/html/report.html
```

## 🎯 常用命令

```bash
# 快速测试（跳过慢速、性能、安全测试）
./run_tests.sh --quick

# 只测试API功能
./run_tests.sh --api

# 运行集成测试
./run_tests.sh --integration

# 运行指定模块
pytest api/test_tenant.py

# 运行指定测试
pytest api/test_tenant.py::TestTenant::test_register_tenant

# 详细输出
pytest -v -s
```

## 📊 测试分类

### 快速测试 (约2-5分钟)
- 健康检查
- 租户管理
- 认证授权
- 对话管理
- 知识库管理

### 完整测试 (约10-20分钟)
包含快速测试 + 以下内容：
- AI对话测试（需要LLM配置）
- 集成测试
- 性能测试
- 安全测试

## ⚙️ 可选配置

### 跳过特定测试

在 `.env.test.local` 中：

```bash
# 跳过性能测试
TEST_SKIP_PERFORMANCE=true

# 跳过安全测试
TEST_SKIP_SECURITY=true

# 不自动清理测试数据
TEST_CLEANUP_AFTER_TEST=false
```

### LLM配置

如果要测试AI对话功能，需要配置LLM：

```bash
# 使用智谱AI
TEST_LLM_PROVIDER=zhipuai
TEST_ZHIPUAI_API_KEY=your_key_here
TEST_ZHIPUAI_MODEL=glm-4-flash

# 或使用OpenAI
TEST_LLM_PROVIDER=openai
TEST_OPENAI_API_KEY=your_key_here
TEST_OPENAI_MODEL=gpt-3.5-turbo
```

## 🐛 遇到问题？

### 问题1: 连接失败

检查测试环境URL是否正确：
```bash
curl http://115.190.75.88:8000/health
```

### 问题2: 认证失败

确认API Key或Token是否有效

### 问题3: 超时

增加超时时间：
```bash
TEST_REQUEST_TIMEOUT=60
TEST_LLM_REQUEST_TIMEOUT=120
```

### 问题4: 依赖安装失败

使用国内镜像：
```bash
pip install -r requirements-test.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 📖 详细文档

查看完整文档：[README.md](README.md)

## 💡 提示

1. **首次运行**建议使用 `--quick` 模式
2. **AI测试**需要配置LLM API Key
3. **性能测试**可能影响服务，谨慎运行
4. **测试数据**会自动清理，无需担心

## ✅ 下一步

- 查看 [README.md](README.md) 了解详细信息
- 查看测试报告分析失败原因
- 根据需要添加自定义测试用例
