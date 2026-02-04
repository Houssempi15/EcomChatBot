# 电商智能客服 SaaS 平台 - 代码详细说明文档

## 项目概述

本项目是一个基于 FastAPI 的电商智能客服 SaaS 平台，提供多租户、AI 对话、知识库管理、RAG 检索、支付订阅等完整功能。

### 技术栈

- **后端框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 14+ (SQLAlchemy 2.0 Async)
- **缓存**: Redis 7+
- **向量数据库**: Milvus 2.3+
- **消息队列**: RabbitMQ + Celery
- **AI/LLM**: OpenAI GPT-4 / Anthropic Claude
- **容器化**: Docker + Docker Compose

---

## 项目架构

### 目录结构

```
ecom-chat-bot/
├── backend/                    # 后端服务目录
│   ├── api/                   # API 层
│   │   ├── main.py           # FastAPI 应用入口
│   │   ├── dependencies.py   # 依赖注入
│   │   └── routers/          # 路由模块
│   │       ├── admin.py      # 管理员接口
│   │       ├── tenant.py     # 租户接口
│   │       ├── conversation.py  # 对话管理
│   │       ├── knowledge.py  # 知识库管理
│   │       ├── payment.py    # 支付管理
│   │       ├── ai_chat.py    # AI 对话
│   │       ├── websocket.py  # WebSocket
│   │       ├── intent.py     # 意图识别
│   │       └── rag.py        # RAG 检索
│   ├── core/                 # 核心模块
│   │   ├── config.py         # 配置管理
│   │   ├── security.py       # 安全认证
│   │   ├── exceptions.py     # 自定义异常
│   │   └── permissions.py    # 权限管理
│   ├── models/               # 数据模型
│   │   ├── base.py           # 基础模型
│   │   ├── tenant.py         # 租户模型
│   │   ├── conversation.py   # 对话模型
│   │   ├── knowledge.py      # 知识库模型
│   │   ├── payment.py        # 支付模型
│   │   └── admin.py          # 管理员模型
│   ├── schemas/              # Pydantic Schema
│   │   ├── base.py           # 基础 Schema
│   │   ├── tenant.py         # 租户 Schema
│   │   ├── conversation.py   # 对话 Schema
│   │   ├── knowledge.py      # 知识库 Schema
│   │   └── payment.py        # 支付 Schema
│   ├── services/             # 业务逻辑层
│   │   ├── tenant_service.py
│   │   ├── conversation_service.py
│   │   ├── rag_service.py
│   │   ├── payment_service.py
│   │   └── ...
│   ├── db/                   # 数据库
│   │   ├── session.py        # 数据库会话
│   │   └── redis.py          # Redis 连接
│   ├── migrations/           # 数据库迁移 (Alembic)
│   ├── requirements.txt      # Python 依赖
│   └── Dockerfile            # Docker 镜像
├── docs/                     # 文档目录
├── deploy.sh                 # 一键部署脚本
├── docker-compose.yml        # Docker Compose 配置
├── QUICKSTART.md            # 快速开始指南
└── README.md                # 项目说明
```

---

## 核心模块详解

### 1. API 层 (backend/api/)

#### 1.1 应用入口 - main.py

```python
# backend/api/main.py:16-28
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    await init_db()          # 启动时初始化数据库
    yield
    await close_db()         # 关闭时清理资源
    await close_redis()
```

**主要功能**:
- 应用生命周期管理（启动初始化、关闭清理）
- 全局异常处理
- CORS 跨域配置
- 路由注册
- 健康检查接口

**关键接口**:
- `GET /health` - 健康检查
- `GET /` - 根路径
- `GET /docs` - Swagger UI 文档

#### 1.2 依赖注入 - dependencies.py

```python
# 依赖注入模式
DBDep = AsyncSession  # 数据库会话依赖
TenantDep = str       # 租户 ID 依赖
```

**用途**:
- 统一管理数据库会话
- 自动提取租户 ID
- 权限验证

---

### 2. 数据模型层 (backend/models/)

#### 2.1 基础模型 - base.py

```python
# BaseModel - 所有表的基类
class BaseModel(Base):
    """基础模型"""
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default="CURRENT_TIMESTAMP")
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default="CURRENT_TIMESTAMP", onupdate="CURRENT_TIMESTAMP")

# TenantBaseModel - 租户相关表的基类
class TenantBaseModel(BaseModel):
    """租户基础模型"""
    __abstract__ = True
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True, comment="租户ID")
```

**特点**:
- 统一的主键和时间戳
- 租户隔离支持
- 自动维护创建/更新时间

#### 2.2 租户模型 - tenant.py

**核心表结构**:

1. **Tenant (租户表)**
   ```python
   # backend/models/tenant.py:12-81
   class Tenant(BaseModel):
       tenant_id: str              # 租户唯一标识
       company_name: str           # 公司名称
       contact_email: str          # 联系邮箱（唯一）
       api_key_hash: str           # API 密钥（加密）
       status: str                 # 状态 (active/suspended/deleted)
       current_plan: str           # 当前套餐
       config: dict                # 租户配置（JSON）
       total_conversations: int    # 总对话次数
       total_spent: float          # 总消费金额
   ```

   **关联关系**:
   - `subscriptions` - 订阅记录（一对多）

2. **Subscription (套餐订阅表)**
   ```python
   # backend/models/tenant.py:83-150
   class Subscription(BaseModel):
       tenant_id: str                  # 租户 ID
       plan_type: str                  # 套餐类型
       enabled_features: list          # 开通的功能模块（JSON）
       conversation_quota: int         # 对话次数配额
       concurrent_quota: int           # 并发会话配额
       storage_quota: int              # 存储空间配额
       api_quota: int                  # API 调用配额
       start_date: datetime            # 订阅开始时间
       expire_at: datetime             # 过期时间
       auto_renew: bool                # 是否自动续费
   ```

3. **UsageRecord (用量记录表)**
   ```python
   # backend/models/tenant.py:152-184
   class UsageRecord(BaseModel):
       tenant_id: str
       record_date: datetime
       conversation_count: int         # 对话次数
       input_tokens: int               # 输入 Token 数
       output_tokens: int              # 输出 Token 数
       storage_used: float             # 存储使用（GB）
       api_calls: int                  # API 调用次数
       overage_fee: float              # 超额费用
   ```

4. **Bill (账单表)**
   ```python
   # backend/models/tenant.py:187-244
   class Bill(BaseModel):
       bill_id: str
       tenant_id: str
       billing_period: str             # 账期 (格式: 2024-01)
       base_fee: float                 # 基础套餐费
       overage_fee: float              # 超额费用
       total_amount: float             # 总金额
       status: str                     # 支付状态
       payment_method: str             # 支付方式
       payment_time: datetime          # 支付时间
   ```

#### 2.3 对话模型 - conversation.py

1. **User (用户表)**
   ```python
   # backend/models/conversation.py:12-55
   class User(TenantBaseModel):
       user_external_id: str          # 用户外部 ID（租户内唯一）
       nickname: str                  # 昵称
       phone: str                     # 手机号
       email: str                     # 邮箱
       vip_level: int                 # VIP 等级
       profile: dict                  # 用户画像（JSON）
       total_conversations: int       # 总对话次数
   ```

2. **Conversation (会话表)**
   ```python
   # backend/models/conversation.py:58-117
   class Conversation(TenantBaseModel):
       conversation_id: str           # 会话 ID
       user_id: int                   # 用户 ID
       channel: str                   # 渠道 (web/mobile/api)
       status: str                    # 状态 (active/closed)
       start_time: datetime           # 开始时间
       end_time: datetime             # 结束时间
       satisfaction_score: int        # 满意度评分 (1-5)
       feedback: str                  # 用户反馈
       message_count: int             # 消息数
       token_usage: int               # Token 消耗
       context: dict                  # 会话上下文（JSON）
   ```

3. **Message (消息表)**
   ```python
   # backend/models/conversation.py:120-165
   class Message(TenantBaseModel):
       message_id: str                # 消息 ID
       conversation_id: str           # 会话 ID
       role: str                      # 角色 (user/assistant/system)
       content: str                   # 消息内容
       intent: str                    # 识别到的意图
       intent_confidence: float       # 意图置信度
       entities: dict                 # 提取的实体（JSON）
       response_time: int             # 响应时间 (ms)
       input_tokens: int              # 输入 Token 数
       output_tokens: int             # 输出 Token 数
   ```

---

### 3. 业务逻辑层 (backend/services/)

#### 3.1 RAG 服务 - rag_service.py

```python
# backend/services/rag_service.py:14-28
class RAGService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.knowledge_service = KnowledgeService(db, tenant_id)
        self.embedding_service = EmbeddingService(tenant_id)
        self.milvus_service = MilvusService(tenant_id)
```

**核心功能**:

1. **向量检索** (`retrieve`)
   ```python
   # backend/services/rag_service.py:24-99
   async def retrieve(
       self,
       query: str,
       top_k: int = 5,
       knowledge_type: str | None = None,
       use_vector_search: bool = True,
   ) -> list[dict]:
       """
       检索流程:
       1. 将查询向量化
       2. 在 Milvus 中搜索
       3. 从数据库获取完整信息
       4. 合并结果返回
       """
   ```

2. **RAG 完整流程** (`retrieve_and_generate`)
   ```python
   # backend/services/rag_service.py:140-186
   async def retrieve_and_generate(
       self,
       query: str,
       conversation_history: list[dict] | None = None,
       use_vector_search: bool = True,
   ) -> dict:
       """
       完整 RAG 流程:
       1. 检索相关知识
       2. 构建上下文
       3. 使用对话链生成回复
       """
   ```

3. **知识索引** (`index_knowledge`)
   ```python
   # backend/services/rag_service.py:188-226
   async def index_knowledge(self, knowledge_id: str) -> dict[str, Any]:
       """
       索引流程:
       1. 获取知识库内容
       2. 生成向量
       3. 插入 Milvus
       """
   ```

#### 3.2 其他核心服务

- **ConversationService**: 对话管理、消息记录
- **KnowledgeService**: 知识库 CRUD、搜索
- **TenantService**: 租户管理、API Key 生成
- **SubscriptionService**: 订阅管理、套餐变更
- **PaymentService**: 支付对接（支付宝）、账单生成
- **QuotaService**: 配额检查、用量统计
- **EmbeddingService**: 文本向量化（OpenAI Embedding）
- **MilvusService**: 向量数据库操作
- **WebSocketService**: 实时消息推送

---

### 4. API 路由层 (backend/api/routers/)

#### 4.1 租户接口 - tenant.py

```python
# backend/api/routers/tenant.py:20-28
@router.get("/info", response_model=ApiResponse[TenantResponse])
async def get_tenant_info(
    tenant_id: TenantDep,
    db: DBDep,
):
    """获取租户信息"""
    service = TenantService(db)
    tenant = await service.get_tenant(tenant_id)
    return ApiResponse(data=tenant)
```

**主要接口**:
- `GET /api/v1/tenant/info` - 获取租户信息
- `GET /api/v1/tenant/subscription` - 获取订阅信息
- `GET /api/v1/tenant/usage` - 获取用量统计
- `GET /api/v1/tenant/quota` - 获取配额使用情况

#### 4.2 管理员接口 - admin.py

**主要接口**:
- `POST /api/v1/admin/login` - 管理员登录
- `GET /api/v1/admin/me` - 获取当前管理员信息
- `PUT /api/v1/admin/me/password` - 修改密码
- `GET /api/v1/admin/tenants` - 获取租户列表
- `POST /api/v1/admin/tenants` - 创建租户
- `PUT /api/v1/admin/tenants/{tenant_id}` - 更新租户
- `DELETE /api/v1/admin/tenants/{tenant_id}` - 删除租户
- `GET /api/v1/admin/statistics` - 获取平台统计

#### 4.3 AI 对话接口 - ai_chat.py

**主要接口**:
- `POST /api/v1/chat/completions` - 对话补全（兼容 OpenAI API）
- `POST /api/v1/chat/stream` - 流式对话
- `POST /api/v1/chat/rag` - RAG 对话

#### 4.4 知识库接口 - knowledge.py

**主要接口**:
- `GET /api/v1/knowledge` - 获取知识库列表
- `POST /api/v1/knowledge` - 创建知识
- `GET /api/v1/knowledge/{knowledge_id}` - 获取知识详情
- `PUT /api/v1/knowledge/{knowledge_id}` - 更新知识
- `DELETE /api/v1/knowledge/{knowledge_id}` - 删除知识
- `POST /api/v1/knowledge/{knowledge_id}/index` - 索引知识到向量库
- `POST /api/v1/knowledge/batch/index` - 批量索引

#### 4.5 支付接口 - payment.py

**主要接口**:
- `GET /api/v1/payment/subscribe/plans` - 获取套餐列表
- `POST /api/v1/payment/subscribe/subscribe` - 订阅套餐
- `POST /api/v1/payment/alipay/create` - 创建支付宝支付
- `POST /api/v1/payment/alipay/notify` - 支付宝异步通知
- `GET /api/v1/payment/bills` - 获取账单列表

#### 4.6 WebSocket 接口 - websocket.py

```python
@router.websocket("/ws/{tenant_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """WebSocket 实时对话"""
```

**功能**: 实时对话、消息推送

---

### 5. 核心配置 (backend/core/)

#### 5.1 配置管理 - config.py

```python
# backend/core/config.py:11-154
class Settings(BaseSettings):
    # 应用配置
    app_name: str = "电商智能客服系统"
    app_version: str = "1.0.0"
    debug: bool = False

    # 数据库
    database_url: PostgresDsn
    database_pool_size: int = 20

    # Redis
    redis_url: RedisDsn

    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_temperature: float = 0.7

    # Milvus
    milvus_host: str = "localhost"
    milvus_port: int = 19530

    # 支付宝
    alipay_appid: str
    alipay_gateway_url: str
    alipay_sandbox: bool = True
```

**配置加载**:
- 使用 `pydantic-settings` 从 `.env` 文件加载
- 单例模式（`@lru_cache()`）
- 类型验证和转换

#### 5.2 安全认证 - security.py

**主要功能**:
- JWT Token 生成和验证
- 密码哈希（bcrypt）
- API Key 生成和验证
- 权限检查

```python
def create_access_token(data: dict) -> str:
    """生成 JWT Token"""

def verify_token(token: str) -> dict | None:
    """验证 JWT Token"""

def hash_password(password: str) -> str:
    """哈希密码"""

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""

def generate_api_key() -> str:
    """生成 API Key"""
```

#### 5.3 异常处理 - exceptions.py

```python
class AppException(Exception):
    """自定义应用异常"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
```

**全局异常处理器**:
- `AppException` - 业务异常
- `RequestValidationError` - 数据验证异常
- `Exception` - 未捕获异常

---

### 6. 数据库层 (backend/db/)

#### 6.1 数据库会话 - session.py

```python
# 异步数据库引擎
engine = create_async_engine(
    settings.database_url_str,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.database_echo,
)

# AsyncSession
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """依赖注入：获取数据库会话"""
    async with async_session() as session:
        yield session
```

#### 6.2 Redis 连接 - redis.py

```python
# Redis 连接池
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url_str,
    max_connections=settings.redis_max_connections,
    decode_responses=True,
)

async def get_redis() -> redis.Redis:
    """依赖注入：获取 Redis 连接"""
```

---

## 数据流程

### 1. 用户认证流程

```
1. 管理员登录
   POST /api/v1/admin/login
   ↓
   验证用户名密码
   ↓
   生成 JWT Token
   ↓
   返回 Token

2. 租户 API 调用
   请求头: X-API-Key: eck_xxx
   ↓
   验证 API Key
   ↓
   提取 tenant_id
   ↓
   执行业务逻辑
```

### 2. AI 对话流程

```
用户发送消息
   ↓
POST /api/v1/chat/completions
   ↓
1. 检查配额
2. 记录消息
3. 意图识别（可选）
4. 检索知识库（RAG）
5. 调用 LLM
6. 记录回复
7. 更新配额
   ↓
返回 AI 回复
```

### 3. 知识库索引流程

```
创建/更新知识
   ↓
POST /api/v1/knowledge/{id}/index
   ↓
1. 获取知识内容
2. 文本分块
3. 生成向量 (Embedding)
4. 存储到 Milvus
   ↓
返回索引结果
```

### 4. 支付流程

```
用户订阅套餐
   ↓
POST /api/v1/payment/subscribe/subscribe
   ↓
1. 创建订阅记录
2. 创建账单
3. 调用支付宝支付
   ↓
用户完成支付
   ↓
支付宝异步通知
   ↓
1. 验证签名
2. 更新账单状态
3. 更新订阅信息
4. 增加配额
```

---

## 关键技术点

### 1. 多租户架构

**租户隔离**:
- 数据隔离：所有租户相关表都有 `tenant_id` 字段
- API 隔离：每个租户有独立的 API Key
- 配额隔离：每个租户有独立的配额限制

**实现方式**:
```python
# 依赖注入自动提取 tenant_id
async def get_tenant_id(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> str:
    api_key = authorization.replace("Bearer ", "")
    tenant = await verify_api_key(db, api_key)
    return tenant.tenant_id
```

### 2. 向量检索 (RAG)

**技术栈**:
- **Embedding**: OpenAI `text-embedding-3-small` (1536 维)
- **向量数据库**: Milvus 2.3+
- **检索算法**: 余弦相似度

**检索流程**:
```python
# 1. 向量化查询
query_vector = await embedding_service.embed_text(query)

# 2. Milvus 搜索
results = await milvus_service.search_vectors(
    query_vector=query_vector,
    top_k=5,
    filter_expr="knowledge_type == 'FAQ'"
)

# 3. 从 PostgreSQL 获取完整信息
knowledge_items = await knowledge_service.get_knowledge_by_ids(
    [r["knowledge_id"] for r in results]
)
```

### 3. 异步编程

**全面使用 AsyncIO**:
- FastAPI 异步路由
- SQLAlchemy 2.0 AsyncSession
- 异步 Redis 客户端
- 异步 HTTP 客户端 (httpx)

**优势**:
- 高并发处理能力
- 非阻塞 I/O
- 更好的资源利用率

### 4. 缓存策略

**Redis 缓存**:
- API Key 验证结果
- 租户配置信息
- 对话上下文
- 向量检索结果

**缓存失效**:
- TTL 过期
- 数据更新时主动失效
- LRU 淘汰

### 5. 安全机制

**认证与授权**:
- JWT Token 认证（管理员）
- API Key 认证（租户）
- 密码哈希存储（bcrypt）
- API Key 哈希 + 盐值

**数据安全**:
- HTTPS 加密传输
- 敏感字段加密存储
- SQL 注入防护（ORM）
- XSS 防护（FastAPI 自动转义）

**访问控制**:
- 租户数据隔离
- 管理员权限分级
- API 限流（可扩展）

---

## 部署架构

### Docker Compose 服务

```yaml
services:
  api:          # FastAPI 应用
  postgres:     # PostgreSQL 数据库
  redis:        # Redis 缓存
  milvus:       # Milvus 向量数据库
  etcd:         # Milvus 元数据存储
  minio:        # Milvus 对象存储
  rabbitmq:     # 消息队列
```

### 部署流程

1. **环境准备**
   - 安装 Docker 和 Docker Compose
   - 克隆项目代码

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件
   ```

3. **一键部署**
   ```bash
   ./deploy.sh
   ```

4. **验证部署**
   ```bash
   ./test.sh
   ```

---

## API 调用示例

### 1. 管理员登录

```bash
curl -X POST "http://localhost:8000/api/v1/admin/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123456"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "admin": {
      "id": 1,
      "username": "admin"
    }
  }
}
```

### 2. 创建租户

```bash
curl -X POST "http://localhost:8000/api/v1/admin/tenants" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "测试公司",
    "contact_name": "张三",
    "contact_email": "zhangsan@example.com",
    "contact_phone": "13800138000"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "tenant_id": "tenant_abc123",
    "company_name": "测试公司",
    "api_key": "eck_xxxxxxxxxxxxx",
    "status": "active",
    "current_plan": "free"
  }
}
```

### 3. AI 对话

```bash
curl -X POST "http://localhost:8000/api/v1/chat/completions" \
  -H "X-API-Key: eck_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_123",
    "user_external_id": "user_456",
    "message": "你好，我想查询订单",
    "use_rag": true
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "message_id": "msg_789",
    "content": "您好！请提供订单号，我帮您查询。",
    "role": "assistant",
    "intent": "order_query",
    "token_usage": {
      "input_tokens": 50,
      "output_tokens": 30
    }
  }
}
```

### 4. 创建知识

```bash
curl -X POST "http://localhost:8000/api/v1/knowledge" \
  -H "X-API-Key: eck_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "如何退换货",
    "content": "您可以在订单详情页申请退换货...",
    "category": "FAQ",
    "tags": ["退换货", "售后"]
  }'
```

### 5. 订阅套餐

```bash
curl -X POST "http://localhost:8000/api/v1/payment/subscribe/subscribe" \
  -H "X-API-Key: eck_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_type": "basic",
    "billing_cycle": "monthly"
  }'
```

---

## 开发指南

### 1. 本地开发

```bash
# 1. 创建虚拟环境
cd backend
python -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env

# 4. 启动开发服务器
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 数据库迁移

```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

### 3. 测试

```bash
# 运行测试
pytest

# 测试覆盖率
pytest --cov=. --cov-report=html
```

### 4. 代码规范

- 使用 **Black** 格式化代码
- 使用 **isort** 排序导入
- 使用 **mypy** 类型检查
- 遵循 **PEP 8** 规范

---

## 性能优化

### 1. 数据库优化

- **索引优化**: 为常用查询字段添加索引
- **连接池**: 配置合适的连接池大小
- **查询优化**: 使用 `selectin`/`joined` 预加载
- **读写分离**: 支持主从复制

### 2. 缓存优化

- **多级缓存**: Redis + 应用内存缓存
- **缓存预热**: 系统启动时加载热点数据
- **缓存更新**: 数据变更时主动更新缓存

### 3. API 优化

- **分页**: 所有列表接口支持分页
- **字段过滤**: 支持只返回指定字段
- **批量操作**: 支持批量创建、更新
- **流式响应**: LLM 对话支持流式输出

### 4. 向量检索优化

- **索引优化**: Milvus IVF_FLAT 索引
- **分片策略**: 按租户分片
- **缓存策略**: 热点查询缓存

---

## 监控与日志

### 1. 日志规范

```python
import logging

logger = logging.getLogger(__name__)

logger.info("用户登录", extra={"user_id": 123})
logger.error("支付失败", extra={"order_id": 456, "error": str(e)})
```

### 2. 性能监控

- **API 响应时间**: 记录每个接口的响应时间
- **数据库查询**: 记录慢查询
- **Token 使用**: 统计 LLM Token 消耗
- **配额使用**: 实时监控租户配额

### 3. 错误追踪

- **Sentry 集成**: 自动捕获未处理异常
- **错误日志**: 记录详细错误堆栈
- **错误统计**: 统计错误类型和频率

---

## 扩展功能

### 1. 微服务拆分

可将单体应用拆分为：
- **用户服务**: 用户、会话管理
- **知识服务**: 知识库、向量检索
- **对话服务**: LLM 对话、RAG
- **支付服务**: 订阅、账单、支付
- **管理服务**: 管理员、租户管理

### 2. 消息队列

使用 Celery + RabbitMQ 实现异步任务：
- **知识索引**: 批量索引到 Milvus
- **账单生成**: 定时生成月度账单
- **邮件通知**: 异步发送邮件
- **数据统计**: 定时统计用量

### 3. 实时通信

- **WebSocket**: 实时对话推送
- **Server-Sent Events (SSE)**: 服务端推送
- **Webhook**: 事件通知

### 4. 多模型支持

支持多种 LLM：
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- 阿里云 (通义千问)
- 百度 (文心一言)

---

## 常见问题

### 1. 如何添加新的 API 路由？

```python
# 1. 在 backend/api/routers/ 创建新文件
# backend/api/routers/my_feature.py

router = APIRouter(prefix="/my-feature", tags=["我的功能"])

@router.get("/")
async def get_items():
    return {"items": []}

# 2. 在 backend/api/main.py 注册
app.include_router(my_feature.router, prefix=settings.api_v1_prefix)
```

### 2. 如何添加新的数据模型？

```python
# 1. 在 backend/models/ 创建模型
# backend/models/my_model.py

class MyModel(TenantBaseModel):
    __tablename__ = "my_models"

    name: Mapped[str] = mapped_column(String(128))
    # ... 其他字段

# 2. 创建数据库迁移
alembic revision --autogenerate -m "添加 MyModel"
alembic upgrade head
```

### 3. 如何调用 LLM？

```python
from services import LLMService

service = LLMService(tenant_id="tenant_123")
response = await service.chat(
    messages=[{"role": "user", "content": "你好"}],
    model="gpt-4"
)
```

### 4.如何配置支付宝？

```bash
# .env 文件
ALIPAY_APPID=你的APPID
ALIPAY_GATEWAY_URL=https://openapi.alipay.com/gateway.do
ALIPAY_SANDBOX=false
```

---

## 技术支持

- **GitHub Issues**: 提交问题和建议
- **文档中心**: `/docs` 目录
- **API 文档**: http://localhost:8000/docs

---

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](./LICENSE) 文件。

---

**最后更新**: 2025-02-04
