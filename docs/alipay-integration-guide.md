# 支付宝支付系统接入方案

> 文档版本：v1.0
> 更新日期：2026-02-09
> 适用项目：电商智能客服系统

---

## 目录

- [一、概述](#一概述)
- [二、当前实现现状](#二当前实现现状)
- [三、支付宝开放平台申请步骤](#三支付宝开放平台申请步骤)
- [四、密钥配置](#四密钥配置)
- [五、环境变量配置](#五环境变量配置)
- [六、API 接口说明](#六api-接口说明)
- [七、回调接口](#七回调接口)
- [八、支付流程](#八支付流程)
- [九、套餐价格配置](#九套餐价格配置)
- [十、接入测试流程](#十接入测试流程)
- [十一、上线检查清单](#十一上线检查清单)
- [十二、常见问题](#十二常见问题)

---

## 一、概述

本文档描述电商智能客服系统接入支付宝支付的完整方案，包括：

- **支持的支付方式**：PC网站支付、手机网站支付
- **支持的业务场景**：新订阅、续费、升级、退款
- **使用的SDK**：python-alipay-sdk 3.4.0

### 1.1 技术架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端应用   │────>│   后端API   │────>│  支付宝平台  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │             │
              ┌─────┴─────┐ ┌─────┴─────┐
              │  PostgreSQL │ │   Redis   │
              └───────────┘ └───────────┘
```

### 1.2 相关文件

| 文件路径 | 说明 |
|---------|------|
| `backend/services/alipay_client.py` | 支付宝客户端封装 |
| `backend/services/payment_service.py` | 支付业务逻辑 |
| `backend/api/routers/payment.py` | 支付API接口 |
| `backend/models/payment.py` | 支付数据模型 |
| `backend/schemas/payment.py` | 请求/响应模型 |
| `backend/core/config.py` | 配置管理 |

---

## 二、当前实现现状

### 2.1 功能实现状态

| 功能模块 | 状态 | 说明 |
|---------|------|------|
| PC网站支付 | ✅ 已实现 | alipay.trade.page.pay |
| 手机网站支付 | ✅ 已实现 | alipay.trade.wap.pay |
| 订单查询 | ✅ 已实现 | alipay.trade.query |
| 退款 | ✅ 已实现 | alipay.trade.refund |
| 异步回调验签 | ✅ 已实现 | RSA2签名验证 |
| 订阅激活 | ✅ 已实现 | 支付成功后自动激活 |

### 2.2 数据模型

#### PaymentOrder（支付订单表）

| 字段 | 类型 | 说明 |
|------|------|------|
| order_number | String(64) | 订单编号（唯一） |
| tenant_id | Integer | 租户ID |
| amount | Decimal(10,2) | 订单金额（元） |
| currency | String(10) | 货币类型（默认CNY） |
| payment_channel | Enum | 支付渠道（alipay） |
| payment_type | Enum | 支付类型（pc/mobile） |
| status | Enum | 订单状态 |
| subscription_type | Enum | 订阅类型（new/renewal/upgrade） |
| plan_type | String(50) | 套餐类型 |
| duration_months | Integer | 订阅时长（月） |
| trade_no | String(128) | 支付宝交易号 |
| paid_at | DateTime | 支付时间 |
| expired_at | DateTime | 订单过期时间 |

#### 订单状态枚举

| 状态 | 值 | 说明 |
|------|-----|------|
| PENDING | pending | 待支付 |
| PAID | paid | 已支付 |
| FAILED | failed | 支付失败 |
| CANCELLED | cancelled | 已取消 |
| REFUNDING | refunding | 退款中 |
| REFUNDED | refunded | 已退款 |
| EXPIRED | expired | 已过期 |

---

## 三、支付宝开放平台申请步骤

### 3.1 注册与认证

1. **注册支付宝开放平台账号**
   - 访问：https://open.alipay.com
   - 使用企业支付宝账号登录
   - 完成企业实名认证

2. **创建应用**
   - 进入「开放平台控制台」→「我的应用」
   - 点击「创建应用」→ 选择「网页&移动应用」
   - 填写应用信息：
     - 应用名称：电商智能客服系统
     - 应用图标：上传应用Logo
     - 应用类型：网页应用

3. **添加产品能力**

   在应用详情页，添加以下产品：

   | 产品名称 | API接口 | 用途 |
   |---------|--------|------|
   | 电脑网站支付 | alipay.trade.page.pay | PC端支付 |
   | 手机网站支付 | alipay.trade.wap.pay | 移动端支付 |
   | 统一收单交易查询 | alipay.trade.query | 查询订单状态 |
   | 统一收单交易退款 | alipay.trade.refund | 退款处理 |

4. **提交审核**
   - 填写应用简介、使用场景
   - 提交审核（通常1-3个工作日）

### 3.2 获取关键信息

审核通过后，记录以下信息：

| 信息项 | 获取位置 | 用途 |
|-------|---------|------|
| APPID | 应用详情页 | 应用唯一标识 |
| 支付宝公钥 | 开发设置 | 验证支付宝回调签名 |

---

## 四、密钥配置

### 4.1 生成 RSA2 密钥对

使用 OpenSSL 生成密钥：

```bash
# 1. 生成私钥（2048位）
openssl genrsa -out alipay_private_key.pem 2048

# 2. 从私钥导出公钥
openssl rsa -in alipay_private_key.pem -pubout -out alipay_app_public_key.pem

# 3. 查看公钥内容（用于上传到支付宝）
cat alipay_app_public_key.pem
```

### 4.2 配置支付宝公钥

1. 登录支付宝开放平台
2. 进入「应用详情」→「开发设置」→「接口加签方式」
3. 选择「公钥」模式，加签算法选择「RSA2(SHA256)」
4. 将 `alipay_app_public_key.pem` 的内容上传
5. 保存后，复制「支付宝公钥」
6. 将支付宝公钥保存为 `alipay_platform_public_key.pem`

### 4.3 密钥文件格式

**私钥文件格式（alipay_private_key.pem）：**
```
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA...
...
-----END RSA PRIVATE KEY-----
```

**支付宝公钥文件格式（alipay_platform_public_key.pem）：**
```
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8A...
...
-----END PUBLIC KEY-----
```

### 4.4 密钥文件存放

```
项目根目录/
├── keys/                              # 本地开发
│   ├── alipay_private_key.pem
│   └── alipay_platform_public_key.pem
│
└── docker/keys/                       # Docker部署
    ├── alipay_private_key.pem
    └── alipay_platform_public_key.pem
```

> **安全提示**：
> - 私钥文件必须妥善保管，切勿泄露
> - 建议将密钥文件加入 `.gitignore`
> - 生产环境建议使用密钥管理服务（如 Vault）

---

## 五、环境变量配置

### 5.1 配置项说明

在 `.env` 文件中配置以下参数：

```bash
# ============ 支付宝配置 ============

# 应用ID（必填）
# 在支付宝开放平台「应用详情」页获取
ALIPAY_APPID=2021000000000000

# 应用私钥路径（必填）
# 用于生成请求签名
ALIPAY_PRIVATE_KEY_PATH=/app/keys/alipay_private_key.pem

# 支付宝平台公钥路径（必填）
# 用于验证支付宝回调签名
ALIPAY_PUBLIC_KEY_PATH=/app/keys/alipay_platform_public_key.pem

# 同步回调地址（必填）
# 用户支付完成后跳转的页面
ALIPAY_RETURN_URL=https://yourdomain.com/api/v1/payment/callback/alipay/return

# 异步回调地址（必填）
# 支付宝服务器通知的地址
ALIPAY_NOTIFY_URL=https://yourdomain.com/api/v1/payment/callback/alipay/notify

# 沙箱模式开关（必填）
# true: 使用沙箱环境（开发测试）
# false: 使用生产环境（正式上线）
ALIPAY_SANDBOX=true

# 正式环境网关地址（无需修改）
ALIPAY_GATEWAY_URL=https://openapi.alipay.com/gateway.do

# 沙箱环境网关地址（无需修改）
ALIPAY_SANDBOX_GATEWAY=https://openapi-sandbox.dl.alipaydev.com/gateway.do
```

### 5.2 不同环境配置示例

**开发环境（.env.development）：**
```bash
ALIPAY_APPID=9021000000000001
ALIPAY_PRIVATE_KEY_PATH=./keys/alipay_private_key.pem
ALIPAY_PUBLIC_KEY_PATH=./keys/alipay_platform_public_key.pem
ALIPAY_RETURN_URL=http://localhost:8000/api/v1/payment/callback/alipay/return
ALIPAY_NOTIFY_URL=https://your-ngrok-url.ngrok.io/api/v1/payment/callback/alipay/notify
ALIPAY_SANDBOX=true
```

**生产环境（.env.production）：**
```bash
ALIPAY_APPID=2021000000000000
ALIPAY_PRIVATE_KEY_PATH=/app/keys/alipay_private_key.pem
ALIPAY_PUBLIC_KEY_PATH=/app/keys/alipay_platform_public_key.pem
ALIPAY_RETURN_URL=https://api.yourdomain.com/api/v1/payment/callback/alipay/return
ALIPAY_NOTIFY_URL=https://api.yourdomain.com/api/v1/payment/callback/alipay/notify
ALIPAY_SANDBOX=false
```

---

## 六、API 接口说明

### 6.1 创建支付订单

**接口地址：** `POST /api/v1/payment/orders/create`

**请求头：**
```
Authorization: Bearer <access_token>
Content-Type: application/json
```

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| plan_type | string | 是 | 套餐类型：basic/professional/enterprise |
| duration_months | integer | 是 | 订阅时长：1/3/6/12 |
| payment_type | string | 是 | 支付类型：pc/mobile |
| subscription_type | string | 是 | 订阅类型：new/renewal/upgrade |
| description | string | 否 | 订单描述 |

**请求示例：**
```json
{
  "plan_type": "professional",
  "duration_months": 3,
  "payment_type": "pc",
  "subscription_type": "new",
  "description": "专业版套餐3个月"
}
```

**响应示例：**
```json
{
  "order_id": 1,
  "order_number": "ORDER20260209143000ABCD1234",
  "amount": 1704.30,
  "currency": "CNY",
  "payment_html": "<!DOCTYPE html><html>...(自动跳转支付宝页面)...</html>",
  "expires_at": "2026-02-10T14:30:00"
}
```

**前端处理：**
```javascript
// 收到响应后，将 payment_html 渲染到页面
document.body.innerHTML = response.payment_html;
// 页面会自动跳转到支付宝
```

### 6.2 查询订单详情

**接口地址：** `GET /api/v1/payment/orders/{order_number}`

**请求示例：**
```
GET /api/v1/payment/orders/ORDER20260209143000ABCD1234
```

**响应示例：**
```json
{
  "order_number": "ORDER20260209143000ABCD1234",
  "status": "paid",
  "amount": 1704.30,
  "trade_no": "2026020922001400001234567890",
  "paid_at": "2026-02-09T14:35:00",
  "expired_at": "2026-02-10T14:30:00",
  "created_at": "2026-02-09T14:30:00"
}
```

### 6.3 同步订单状态

**接口地址：** `POST /api/v1/payment/orders/{order_number}/sync`

**说明：** 主动从支付宝查询订单最新状态并更新本地记录

**响应示例：**
```json
{
  "success": true,
  "message": "订单状态已同步",
  "order": {
    "order_number": "ORDER20260209143000ABCD1234",
    "status": "paid",
    "amount": 1704.30,
    "trade_no": "2026020922001400001234567890",
    "paid_at": "2026-02-09T14:35:00"
  }
}
```

### 6.4 申请退款

**接口地址：** `POST /api/v1/payment/orders/{order_number}/refund`

**请求参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| refund_amount | decimal | 否 | 退款金额（不填则全额退款） |
| refund_reason | string | 否 | 退款原因（默认：用户申请退款） |

**请求示例：**
```json
{
  "refund_amount": 500.00,
  "refund_reason": "用户申请部分退款"
}
```

**响应示例：**
```json
{
  "refund_id": 0,
  "refund_status": "success",
  "refund_amount": 500.00,
  "refund_time": "2026-02-09T15:00:00",
  "message": "退款成功"
}
```

---

## 七、回调接口

### 7.1 同步回调（Return URL）

**接口地址：** `GET /api/v1/payment/callback/alipay/return`

**说明：**
- 用户在支付宝完成支付后，浏览器会跳转到此地址
- 仅用于展示支付结果页面
- **不在此处理业务逻辑**（业务逻辑在异步回调处理）

**支付宝返回参数：**

| 参数 | 说明 |
|------|------|
| out_trade_no | 商户订单号 |
| trade_no | 支付宝交易号 |
| total_amount | 支付金额 |
| sign | 签名 |

### 7.2 异步回调（Notify URL）

**接口地址：** `POST /api/v1/payment/callback/alipay/notify`

**说明：**
- 支付宝服务器主动发送的通知
- 用于处理核心业务逻辑
- 必须返回 `success` 字符串表示处理成功
- 支付宝会重试最多 8 次（间隔：4m, 10m, 10m, 1h, 2h, 6h, 15h）

**处理流程：**

```
1. 验证签名
   ↓
2. 验证订单是否存在
   ↓
3. 验证金额是否匹配
   ↓
4. 检查订单状态（幂等性）
   ↓
5. 更新订单状态为已支付
   ↓
6. 创建交易记录
   ↓
7. 激活订阅
   ↓
8. 返回 "success"
```

**支付宝通知参数：**

| 参数 | 说明 |
|------|------|
| out_trade_no | 商户订单号 |
| trade_no | 支付宝交易号 |
| trade_status | 交易状态：TRADE_SUCCESS |
| total_amount | 订单金额 |
| gmt_payment | 支付时间 |
| sign | 签名 |

---

## 八、支付流程

### 8.1 时序图

```
用户                前端                 后端                 支付宝
 │                   │                    │                     │
 │──选择套餐────────>│                    │                     │
 │                   │                    │                     │
 │                   │──创建订单(POST)───>│                     │
 │                   │                    │──生成支付参数──────>│
 │                   │                    │<─────────────────────
 │                   │<──返回payment_html─│                     │
 │                   │                    │                     │
 │                   │──渲染HTML并跳转────│────────────────────>│
 │                   │                    │                     │
 │<──────────────────│<───支付页面────────│<─────────────────────│
 │                   │                    │                     │
 │──完成支付────────>│────────────────────│────────────────────>│
 │                   │                    │                     │
 │                   │                    │<──异步通知(POST)────│
 │                   │                    │──验签+处理业务──────│
 │                   │                    │──返回success───────>│
 │                   │                    │                     │
 │<──同步跳转────────│<───结果页面────────│<─────────────────────│
 │                   │                    │                     │
 │                   │──轮询订单状态─────>│                     │
 │                   │<──返回支付成功─────│                     │
 │<──显示成功────────│                    │                     │
```

### 8.2 关键代码说明

#### 创建支付订单

```python
# backend/services/payment_service.py

async def create_payment_order(
    self,
    tenant_id: int,
    plan_type: str,
    duration_months: int,
    payment_type: PaymentType,
    subscription_type: SubscriptionType,
    description: Optional[str] = None,
) -> tuple[PaymentOrder, str]:
    """创建支付订单"""

    # 1. 验证租户
    # 2. 计算订单金额（含折扣）
    amount = self.calculate_amount(plan_type, duration_months)

    # 3. 生成订单号
    order_number = self.generate_order_number()

    # 4. 创建订单记录
    order = PaymentOrder(...)

    # 5. 调用支付宝生成支付HTML
    if payment_type == PaymentType.PC:
        payment_html = self.alipay_client.create_page_pay(...)
    else:
        payment_html = self.alipay_client.create_wap_pay(...)

    return order, payment_html
```

#### 处理异步回调

```python
# backend/services/payment_service.py

async def handle_alipay_notify(self, notify_data: Dict[str, str]) -> bool:
    """处理支付宝异步回调"""

    # 1. 验证签名
    if not self.alipay_client.verify_notify(notify_data):
        return False

    # 2. 查询订单
    order = await self.get_order(notify_data["out_trade_no"])

    # 3. 幂等性检查
    if order.status == OrderStatus.PAID:
        return True

    # 4. 验证金额
    if order.amount != Decimal(notify_data["total_amount"]):
        return False

    # 5. 处理支付成功
    if notify_data["trade_status"] == "TRADE_SUCCESS":
        order.status = OrderStatus.PAID
        order.trade_no = notify_data["trade_no"]
        order.paid_at = datetime.now()

        # 6. 激活订阅
        await self._activate_subscription(order)

        return True

    return False
```

---

## 九、套餐价格配置

### 9.1 基础价格

| 套餐类型 | 标识 | 月费（元） |
|---------|------|-----------|
| 基础版 | basic | 198.00 |
| 专业版 | professional | 598.00 |
| 企业版 | enterprise | 1998.00 |

### 9.2 时长折扣

| 订阅时长 | 折扣 |
|---------|------|
| 1个月 | 无折扣（100%） |
| 3个月 | 95折 |
| 6个月 | 90折 |
| 12个月 | 85折 |

### 9.3 价格计算公式

```
最终价格 = 月费 × 订阅月数 × 折扣率
```

### 9.4 价格表

| 套餐 | 1个月 | 3个月 | 6个月 | 12个月 |
|------|-------|-------|-------|--------|
| 基础版 | ¥198.00 | ¥564.30 | ¥1,069.20 | ¥2,019.60 |
| 专业版 | ¥598.00 | ¥1,704.30 | ¥3,229.20 | ¥6,099.60 |
| 企业版 | ¥1,998.00 | ¥5,694.30 | ¥10,789.20 | ¥20,379.60 |

### 9.5 修改价格配置

价格配置在 `backend/services/payment_service.py` 中：

```python
# 套餐价格配置（元/月）
PLAN_PRICES = {
    "basic": Decimal("198.00"),
    "professional": Decimal("598.00"),
    "enterprise": Decimal("1998.00"),
}

# 折扣配置
DURATION_DISCOUNTS = {
    1: Decimal("1.0"),    # 1个月：无折扣
    3: Decimal("0.95"),   # 3个月：95折
    6: Decimal("0.90"),   # 6个月：90折
    12: Decimal("0.85"),  # 12个月：85折
}
```

---

## 十、接入测试流程

### 10.1 沙箱环境配置

1. **启用沙箱模式**
   ```bash
   ALIPAY_SANDBOX=true
   ```

2. **获取沙箱应用信息**
   - 登录支付宝开放平台
   - 进入「开发服务」→「沙箱环境」
   - 获取沙箱应用APPID和密钥

3. **获取沙箱测试账号**

   | 账号类型 | 用途 |
   |---------|------|
   | 商家账号 | 收款方 |
   | 买家账号 | 付款测试 |

4. **下载沙箱版支付宝APP**
   - 用于扫码支付测试
   - 在沙箱环境页面获取下载链接

### 10.2 本地开发调试

由于支付宝回调需要公网地址，本地开发时可使用内网穿透工具：

**使用 ngrok：**
```bash
# 1. 启动本地服务
uvicorn main:app --reload --port 8000

# 2. 启动 ngrok
ngrok http 8000

# 3. 获取公网地址
# Forwarding: https://xxxx.ngrok.io -> http://localhost:8000

# 4. 配置回调地址
ALIPAY_NOTIFY_URL=https://xxxx.ngrok.io/api/v1/payment/callback/alipay/notify
```

### 10.3 测试用例

| 序号 | 测试场景 | 操作步骤 | 预期结果 |
|------|---------|---------|---------|
| 1 | PC端创建订单 | 调用创建订单接口，payment_type=pc | 返回支付HTML，可跳转支付宝 |
| 2 | 移动端创建订单 | 调用创建订单接口，payment_type=mobile | 返回WAP支付HTML |
| 3 | 支付成功 | 完成支付宝支付 | 订单状态更新为paid，订阅激活 |
| 4 | 查询订单 | 调用订单查询接口 | 返回正确的订单信息 |
| 5 | 同步订单状态 | 调用同步接口 | 从支付宝获取最新状态 |
| 6 | 全额退款 | 调用退款接口，不传金额 | 订单状态更新为refunded |
| 7 | 部分退款 | 调用退款接口，传入部分金额 | 订单状态更新为refunding |
| 8 | 订单超时 | 等待24小时不支付 | 订单状态更新为expired |
| 9 | 重复回调 | 模拟支付宝重复发送回调 | 幂等处理，返回success |
| 10 | 签名验证失败 | 篡改回调参数 | 返回failure |

### 10.4 测试命令示例

```bash
# 创建订单
curl -X POST "http://localhost:8000/api/v1/payment/orders/create" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_type": "professional",
    "duration_months": 1,
    "payment_type": "pc",
    "subscription_type": "new"
  }'

# 查询订单
curl -X GET "http://localhost:8000/api/v1/payment/orders/ORDER20260209143000ABCD1234" \
  -H "Authorization: Bearer <token>"

# 同步订单状态
curl -X POST "http://localhost:8000/api/v1/payment/orders/ORDER20260209143000ABCD1234/sync" \
  -H "Authorization: Bearer <token>"

# 申请退款
curl -X POST "http://localhost:8000/api/v1/payment/orders/ORDER20260209143000ABCD1234/refund" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refund_reason": "测试退款"
  }'
```

---

## 十一、上线检查清单

### 11.1 支付宝平台配置

- [ ] 应用已通过审核
- [ ] 「电脑网站支付」已签约
- [ ] 「手机网站支付」已签约
- [ ] 「统一收单交易退款」已签约
- [ ] 「统一收单交易查询」已签约
- [ ] 生产环境密钥已配置
- [ ] 应用网关地址已配置
- [ ] 授权回调地址已配置

### 11.2 服务端配置

- [ ] `ALIPAY_SANDBOX=false` 已设置
- [ ] 生产环境 APPID 已配置
- [ ] 生产环境密钥文件已部署
- [ ] 回调地址为 HTTPS
- [ ] 回调地址可公网访问
- [ ] 数据库表已迁移
- [ ] Redis 已配置

### 11.3 安全检查

- [ ] 私钥文件权限为 600
- [ ] 私钥文件不在代码仓库中
- [ ] 回调接口有签名验证
- [ ] 金额校验已实现
- [ ] 幂等性处理已实现

### 11.4 监控告警

- [ ] 支付成功率监控
- [ ] 回调失败告警
- [ ] 退款失败告警
- [ ] 异常订单告警
- [ ] 日志收集已配置

### 11.5 容灾备份

- [ ] 数据库定期备份
- [ ] 交易记录保留策略
- [ ] 异常订单处理流程

---

## 十二、常见问题

### Q1: 支付宝回调收不到怎么办？

**可能原因：**
1. 回调地址不可公网访问
2. 回调地址不是 HTTPS（生产环境）
3. 服务器防火墙阻止了请求
4. Nginx 配置问题

**解决方案：**
1. 使用公网可访问的地址
2. 配置 SSL 证书
3. 开放服务器 80/443 端口
4. 检查 Nginx 代理配置

### Q2: 签名验证失败怎么办？

**可能原因：**
1. 使用了错误的公钥（应用公钥 vs 支付宝公钥）
2. 密钥格式不正确
3. 签名类型不匹配（RSA vs RSA2）

**解决方案：**
1. 确认使用「支付宝公钥」而非「应用公钥」
2. 检查密钥文件格式（包含 BEGIN/END 标记）
3. 确认使用 RSA2(SHA256) 签名

### Q3: 沙箱环境支付成功但回调失败？

**可能原因：**
1. 沙箱环境对回调地址要求较严格
2. 回调处理超时

**解决方案：**
1. 确保回调处理在 5 秒内完成
2. 异步处理耗时操作
3. 查看服务器日志定位问题

### Q4: 如何处理订单超时？

**建议方案：**
1. 创建定时任务，定期检查过期订单
2. 将超过 24 小时未支付的订单标记为 expired
3. 可配合支付宝订单查询接口确认最终状态

```python
# 定时任务示例
async def check_expired_orders():
    """检查并处理过期订单"""
    expired_orders = await db.execute(
        select(PaymentOrder).where(
            PaymentOrder.status == OrderStatus.PENDING,
            PaymentOrder.expired_at < datetime.now()
        )
    )
    for order in expired_orders.scalars():
        order.status = OrderStatus.EXPIRED
    await db.commit()
```

### Q5: 如何测试异步回调？

**方法一：使用支付宝沙箱**
- 完成真实支付流程，支付宝会发送回调

**方法二：模拟回调请求**
```bash
# 注意：生产环境无法模拟，因为无法生成有效签名
curl -X POST "http://localhost:8000/api/v1/payment/callback/alipay/notify" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "out_trade_no=ORDER20260209143000ABCD1234&trade_no=2026020922001400001234567890&trade_status=TRADE_SUCCESS&total_amount=598.00&sign=xxx"
```

---

## 附录

### A. 相关链接

| 资源 | 链接 |
|------|------|
| 支付宝开放平台 | https://open.alipay.com |
| 开发文档 | https://opendocs.alipay.com |
| 沙箱环境 | https://open.alipay.com/develop/sandbox/app |
| python-alipay-sdk | https://github.com/fzlee/alipay |

### B. 错误码参考

| 错误码 | 说明 | 处理建议 |
|-------|------|---------|
| ACQ.SYSTEM_ERROR | 系统错误 | 重试 |
| ACQ.INVALID_PARAMETER | 参数无效 | 检查请求参数 |
| ACQ.TRADE_NOT_EXIST | 交易不存在 | 检查订单号 |
| ACQ.TRADE_STATUS_ERROR | 交易状态错误 | 检查订单状态 |
| ACQ.REFUND_AMT_NOT_EQUAL_TOTAL | 退款金额超限 | 检查退款金额 |

### C. 修订历史

| 版本 | 日期 | 修订内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-02-09 | 初始版本 | - |
