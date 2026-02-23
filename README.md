# 电商智能客服 SaaS 平台

基于大模型的多租户电商智能客服 SaaS 平台，提供完整的前后端解决方案。

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

## 📖 项目简介

本项目是一个**生产级**多租户电商智能客服 SaaS 平台，包含完整的前后端实现，支持：

- ✅ **多租户架构**：`tenant_id` 逻辑隔离，支持海量租户接入
- ✅ **完整管理后台**：Next.js 前端，覆盖租户管理、计费、统计分析
- ✅ **模块化计费**：基础对话、订单查询、商品推荐等可选计费模块
- ✅ **灵活认证**：API Key（对外服务）+ JWT Token（管理后台）双认证
- ✅ **多 LLM 支持**：DeepSeek（默认）、OpenAI、智谱 AI、Anthropic
- ✅ **RAG 检索增强**：Milvus 向量数据库 + 知识库问答
- ✅ **意图识别**：规则 + LLM 混合意图识别与实体提取
- ✅ **订阅与支付**：支付宝、微信支付集成，支持套餐升降级与发票
- ✅ **监控与质量评估**：对话统计、响应时间、满意度、质量自动评分
- ✅ **Webhook 通知**：事件驱动的外部系统集成
- ✅ **安全审计**：完善的操作审计日志与敏感词过滤
- ✅ **一键部署**：Docker Compose 全自动编排

## 🛠️ 技术栈

### 后端

| 类别 | 技术 |
|------|------|
| 框架 | FastAPI 0.109、Uvicorn（ASGI） |
| ORM | SQLAlchemy 2.0（异步）、Alembic（迁移） |
| 数据验证 | Pydantic v2 |
| AI 框架 | LangChain 0.1、LangGraph、Sentence Transformers |
| LLM 提供商 | DeepSeek（默认）、OpenAI、智谱 AI、Anthropic |
| 后台任务 | Celery 5.3 + Flower 监控界面 |
| 消息队列 | RabbitMQ（任务分发）、Redis（Broker/Result） |

### 前端

| 类别 | 技术 |
|------|------|
| 框架 | Next.js 14（App Router）、React 18、TypeScript |
| UI 组件库 | Ant Design 6、@ant-design/charts |
| 状态管理 | Zustand 5 |
| HTTP 客户端 | Axios |
| 样式 | Tailwind CSS 3 |
| E2E 测试 | Playwright |

### 数据存储

| 组件 | 用途 |
|------|------|
| PostgreSQL 14+ | 主关系数据库 |
| Redis 7+ | 缓存、会话、Celery Broker |
| Milvus 2.3+ | 向量数据库（RAG 检索） |
| MinIO | 对象存储（Milvus 依赖） |
| RabbitMQ | 异步任务消息队列 |

### 运维

- **反向代理**：Nginx
- **容器化**：Docker + Docker Compose（开发 & 生产两套配置）
- **CI/CD**：Jenkins Pipeline + GitHub Actions
- **监控**：Prometheus 指标采集、Sentry 错误追踪、Flower 任务监控

## 🚀 快速开始

### 前置要求

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **操作系统**：Linux / macOS / Windows（WSL2）
- **硬件**：CPU 4 核+ / 内存 8GB+ / 磁盘 20GB+

### 一键部署（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd ecom-chat-bot

# 2. 一键启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps
```

部署完成后访问：

| 地址 | 说明 |
|------|------|
| http://localhost:3000 | 前端管理后台 |
| http://localhost:8000/docs | 后端 API 文档（Swagger UI） |
| http://localhost:8000/health | 健康检查 |
| http://localhost:15672 | RabbitMQ 管理界面（guest/guest） |

### 快速验证

```bash
# 1. 租户注册
curl -X POST "http://localhost:8000/api/v1/tenant/register" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "测试公司",
    "contact_name": "张三",
    "contact_email": "test@example.com",
    "password": "test123456"
  }'

# 2. 创建会话（使用注册返回的 API Key）
curl -X POST "http://localhost:8000/api/v1/conversation/create" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user123", "channel": "web"}'

# 3. 发起 AI 对话
curl -X POST "http://localhost:8000/api/v1/ai-chat/chat" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "CONV_ID",
    "message": "你好，我想查一下我的订单",
    "use_rag": false
  }'

# 4. 超级管理员登录（默认账号: admin / admin123456）
curl -X POST "http://localhost:8000/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123456"}'
```

### 本地开发

```bash
# 启动依赖服务
docker-compose up -d postgres redis milvus rabbitmq

# ── 后端 ──────────────────────────────
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python init_db.py              # 初始化数据库 & 创建默认超管
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# ── 前端（新终端）────────────────────
cd frontend
npm install
npm run dev                    # 访问 http://localhost:3000
```

详细部署说明：

- [快速开始指南](./docs/QUICKSTART.md)
- [生产部署指南](./docs/README-DEPLOYMENT.md)
- [Jenkins CI/CD](./docs/JENKINS_SETUP.md)

## 📁 项目结构

```
ecom-chat-bot/
├── backend/                    # FastAPI 后端
│   ├── api/
│   │   ├── main.py            # 应用入口
│   │   ├── dependencies.py    # 依赖注入（认证、DB）
│   │   ├── middleware/        # 配额检查、限流、日志中间件
│   │   └── routers/           # 路由模块（18 个）
│   │       ├── admin.py       # 平台管理
│   │       ├── tenant.py      # 租户自服务
│   │       ├── auth.py        # 认证
│   │       ├── ai_chat.py     # AI 对话
│   │       ├── conversation.py# 会话管理
│   │       ├── knowledge.py   # 知识库
│   │       ├── rag.py         # RAG 检索
│   │       ├── intent.py      # 意图识别
│   │       ├── monitor.py     # 监控统计
│   │       ├── quality.py     # 质量评估
│   │       ├── webhook.py     # Webhook
│   │       ├── model_config.py# 模型配置
│   │       ├── payment.py     # 支付
│   │       ├── analytics.py   # 数据分析
│   │       ├── audit.py       # 审计日志
│   │       ├── sensitive_word.py # 敏感词
│   │       ├── setup.py       # 初始化引导
│   │       └── health.py      # 健康检查
│   ├── core/                  # 核心配置
│   │   ├── config.py          # 配置管理
│   │   ├── security.py        # JWT、API Key、密码哈希
│   │   ├── permissions.py     # RBAC 权限
│   │   └── exceptions.py      # 自定义异常（25+ 类型）
│   ├── models/                # SQLAlchemy ORM 模型
│   ├── schemas/               # Pydantic 请求/响应模型
│   ├── services/              # 业务逻辑层（48+ 服务）
│   ├── tasks/                 # Celery 后台任务
│   │   ├── celery_app.py
│   │   ├── billing_tasks.py
│   │   ├── notification_tasks.py
│   │   ├── webhook_tasks.py
│   │   └── data_tasks.py
│   ├── db/                    # 数据库工具（session、redis、RLS）
│   ├── migrations/            # Alembic 数据库迁移
│   ├── tests/                 # 测试套件
│   ├── init_db.py             # 数据库初始化脚本
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # Next.js 14 前端
│   ├── src/
│   │   ├── app/
│   │   │   ├── (auth)/        # 登录 / 注册
│   │   │   ├── (dashboard)/   # 租户工作台
│   │   │   │   ├── dashboard/ # 概览
│   │   │   │   ├── chat/      # 对话界面
│   │   │   │   ├── knowledge/ # 知识库管理
│   │   │   │   └── settings/  # 租户设置
│   │   │   └── (admin)/       # 超管后台
│   │   │       ├── admins/    # 管理员管理
│   │   │       ├── tenants/   # 租户管理
│   │   │       ├── payments/  # 支付 & 账单
│   │   │       ├── statistics/# 数据统计
│   │   │       └── platform/  # 平台配置
│   │   ├── components/        # 复用组件
│   │   ├── store/             # Zustand 状态
│   │   ├── lib/api/           # API 客户端
│   │   └── types/             # TypeScript 类型
│   ├── e2e/                   # Playwright E2E 测试
│   ├── next.config.mjs
│   └── Dockerfile
├── nginx/                     # Nginx 反向代理配置
├── docs/                      # 项目文档
├── scripts/                   # 部署 & 工具脚本
├── docker-compose.yml         # 开发环境编排
├── docker-compose.prod.yml    # 生产环境编排
├── Jenkinsfile                # Jenkins CI/CD
└── run_all_tests.sh           # 完整测试入口
```

## 📡 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| Nginx | 80 | 反向代理（开发环境入口） |
| Next.js 前端 | 3000 | 管理后台 Web UI |
| FastAPI 后端 | 8000 | REST API |
| PostgreSQL | 5432 | 主数据库 |
| Redis | 6379 | 缓存 & Celery Broker |
| Milvus | 19530 | 向量数据库 |
| MinIO | 9000 | 对象存储 |
| RabbitMQ AMQP | 5672 | 消息队列 |
| RabbitMQ 管理 | 15672 | 管理界面（guest/guest） |

## 📚 核心功能

### 多租户与认证

- 租户注册、登录，API Key 自助获取
- 双认证模式：`X-API-Key`（对外）、`Authorization: Bearer`（Web 后台）
- RBAC 权限体系：超级管理员（SUPER_ADMIN）/ 管理员（ADMIN）/ 运营（OPERATOR）
- 租户数据严格隔离（`tenant_id` 级别）

### AI 对话系统

- 多 LLM 提供商支持，运行时可切换（DeepSeek 默认）
- 规则 + LLM 混合意图识别与实体提取
- 上下文记忆管理，支持多轮对话摘要
- RAG 检索增强：Milvus 向量检索 + 知识库重排序

### 知识库管理

- 知识条目 CRUD、关键词搜索、批量导入
- 向量化索引，支持语义检索（Sentence Transformers）
- 知识使用日志追踪

### 订阅与计费

- 模块化套餐：可按对话、订单查询、商品推荐等功能独立计费
- 实时配额检查（Redis），支持超额付费
- 支付宝 / 微信支付集成，发票生成与管理
- 套餐升降级支持按比例计算费用

### 监控与质量

- 对话统计、响应时间、满意度、每小时趋势分析
- 对话质量自动评分（规则 + LLM）
- Prometheus 指标采集，Sentry 错误追踪

### 平台管理（超管后台）

- 租户管理（启用 / 停用 / 查看用量）
- 管理员账号与权限模板管理
- 全平台收入与用量统计报表
- 操作审计日志（完整安全事件记录）
- 敏感词过滤配置

### 扩展与集成

- Webhook 事件通知，支持自定义事件订阅与测试
- 邮件 / 短信 / 站内通知
- 灵活的 LLM 模型配置管理（多 Provider、多 Model）

## 🔐 认证方式

```bash
# 租户 API Key 认证（推荐用于服务端集成）
curl -H "X-API-Key: eck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" \
  http://localhost:8000/api/v1/tenant/info

# JWT Token 认证（用于前端登录态）
curl -H "Authorization: Bearer <jwt_token>" \
  http://localhost:8000/api/v1/tenant/info-token

# 超级管理员认证（默认账号: admin / admin123456）
curl -X POST http://localhost:8000/api/v1/admin/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123456"}'
```

## 📖 API 文档

启动服务后访问 **http://localhost:8000/docs** 查看完整的交互式 Swagger 文档。

### 主要端点概览

| 模块 | 端点前缀 | 说明 |
|------|---------|------|
| 认证 | `/api/v1/auth` | 登录、Token 刷新 |
| 租户 | `/api/v1/tenant` | 注册、订阅、配额、用量 |
| 对话 | `/api/v1/conversation` | 会话 CRUD、消息管理 |
| AI 对话 | `/api/v1/ai-chat` | 智能对话、意图分类、实体提取 |
| 知识库 | `/api/v1/knowledge` | CRUD、搜索、批量导入 |
| RAG | `/api/v1/rag` | 检索、生成、索引 |
| 意图 | `/api/v1/intent` | 意图分类、实体提取 |
| 监控 | `/api/v1/monitor` | 统计、趋势、Dashboard |
| 质量 | `/api/v1/quality` | 对话质量评估 |
| 模型配置 | `/api/v1/models` | LLM Provider 配置 |
| Webhook | `/api/v1/webhooks` | 创建、测试、列表 |
| 支付 | `/api/v1/payment` | 订单、回调 |
| 管理员 | `/api/v1/admin` | 租户管理、统计报表 |

## 🔧 配置说明

核心环境变量（`docker-compose.yml` / `.env`）：

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://ecom_user:ecom_password@postgres:5432/ecom_chatbot

# Redis
REDIS_URL=redis://redis:6379/0

# 向量数据库
MILVUS_HOST=milvus
MILVUS_PORT=19530

# LLM（默认 DeepSeek）
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 其他 LLM Provider（可选）
OPENAI_API_KEY=sk-xxx
ZHIPUAI_API_KEY=xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# JWT
JWT_SECRET=change-this-in-production
JWT_ACCESS_TOKEN_EXPIRE_HOURS=8
JWT_REFRESH_TOKEN_EXPIRE_DAYS=30

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2
```

### 通过 API 动态配置 LLM 模型

```bash
curl -X POST "http://localhost:8000/api/v1/models" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "zhipuai",
    "model_name": "glm-4-flash",
    "api_key": "YOUR_ZHIPUAI_API_KEY",
    "temperature": 0.7,
    "max_tokens": 2000,
    "use_case": "chat",
    "is_default": true
  }'
```

## 🧪 测试

```bash
# 运行全部测试（后端 + 前端 E2E）
./run_all_tests.sh

# 仅后端测试
./scripts/run-tests.sh

# 冒烟测试（快速验证核心流程）
./scripts/smoke-test.sh

# 前端 E2E 测试
cd frontend && npm run test:e2e
```

测试覆盖：

- 后端 API 单元测试 & 集成测试
- 性能基准测试 & 安全测试
- 前端 Playwright E2E 测试

## 📊 监控与日志

```bash
# 查看所有服务日志
docker-compose logs

# 实时跟踪 API 日志
docker-compose logs -f api

# Celery Worker 日志
docker-compose logs -f celery-worker

# 所有服务状态
docker-compose ps
```

Flower（Celery 任务监控）默认随 `docker-compose up` 启动，可通过配置端口访问。

## 🛡️ 生产安全建议

1. **修改默认密码**：数据库密码、管理员密码、JWT Secret
2. **配置 HTTPS**：通过 Nginx 反向代理挂载 SSL 证书
3. **收紧防火墙**：只对外暴露 80/443，其余端口仅内网可访问
4. **定期数据备份**：
   ```bash
   docker-compose exec postgres pg_dump -U ecom_user ecom_chatbot > backup_$(date +%Y%m%d).sql
   ```
5. **密钥管理**：通过环境变量或 Secrets Manager 注入敏感配置，禁止提交到 Git

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交更改：`git commit -m 'feat: add your feature'`
4. 推送分支：`git push origin feature/your-feature`
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 📞 资源链接

- **交互式 API 文档**：http://localhost:8000/docs
- **设计方案**：[docs/设计方案.md](./docs/设计方案.md)
- **快速开始**：[docs/QUICKSTART.md](./docs/QUICKSTART.md)
- **部署指南**：[docs/README-DEPLOYMENT.md](./docs/README-DEPLOYMENT.md)
- **支付集成**：[docs/alipay-integration-guide.md](./docs/alipay-integration-guide.md)
- **性能优化**：[docs/performance-optimization-guide.md](./docs/performance-optimization-guide.md)
- **问题反馈**：GitHub Issues

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/)
- [Next.js](https://nextjs.org/)
- [LangChain](https://python.langchain.com/)
- [Milvus](https://milvus.io/)
- [Ant Design](https://ant.design/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [PostgreSQL](https://www.postgresql.org/)
- [Redis](https://redis.io/)

---

⭐ 如果这个项目对你有帮助，请给个 Star！
