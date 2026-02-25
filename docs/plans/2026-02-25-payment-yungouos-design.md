# YunGouOS 支付接入设计文档

**日期**: 2026-02-25
**状态**: 已批准
**作者**: Kiro

---

## 背景

项目现有支付宝直连（`alipay_client.py`）和微信支付官方 API v3（`wechat_pay.py`）两套实现，代码耦合在 `PaymentService` 内部。现需替换为 YunGouOS 聚合支付平台，同时重构支付层架构，引入抽象网关接口，提升可维护性。

---

## 目标

1. 接入 YunGouOS 平台，支持微信扫码支付（Native）和支付宝扫码支付（Native）
2. 重构 `PaymentService`，通过依赖注入使用抽象网关接口
3. 删除旧的 `alipay_client.py` 和 `wechat_pay.py`
4. 订阅等级按时长维度设计（月付/季付/半年付/年付）

---

## 订阅等级

| plan_type | 名称 | 价格 | 时长 |
|-----------|------|------|------|
| `trial` | 试用版 | ¥0 | 管理员手动开通 |
| `monthly` | 月付版 | ¥199 | 30 天 |
| `quarterly` | 季付版 | ¥499 | 90 天 |
| `semi_annual` | 半年付 | ¥899 | 180 天 |
| `annual` | 年付版 | ¥1699 | 365 天 |

价格逻辑：每个 `plan_type` 对应固定价格和固定天数，直接查表，不再使用 `duration_months × discount` 模式。

---

## 架构设计

### 文件变更

```
backend/services/
├── payment_gateway.py        # 新增：抽象网关 ABC
├── yungouos_client.py        # 新增：YunGouOS HTTP 客户端实现
├── payment_service.py        # 重构：依赖注入网关，移除旧客户端
├── alipay_client.py          # 删除
└── wechat_pay.py             # 删除

backend/core/config.py        # 新增 YunGouOS 配置项
backend/models/payment.py     # 微调：PaymentType 新增 NATIVE，PaymentOrder 新增 qr_code_url
backend/api/routers/payment.py # 简化：移除旧专用路由，新增统一回调路由
```

---

## YunGouOS 平台说明

### 签名规则（MD5）

1. 收集所有非空参数（排除 `sign` 本身）
2. 按 key 字母序升序排列
3. 拼接为 `key1=val1&key2=val2&...&key=商户密钥`
4. 对整个字符串做 MD5，取 32 位大写

### 微信扫码支付

- **接口**: `POST https://api.pay.yungouos.com/api/pay/wxpay/nativePay`
- **参数**: `out_trade_no`, `total_fee`（元，字符串）, `mch_id`, `body`, `notify_url`, `attach`（可选）, `sign`
- **返回**: `{"code": 0, "data": "weixin://wxpay/...", "img": "base64二维码"}`

### 支付宝扫码支付

- **接口**: `POST https://api.pay.yungouos.com/api/pay/alipay/nativePay`
- **参数**: 同上，`mch_id` 为支付宝商户号
- **返回**: `{"code": 0, "data": "https://qr.alipay.com/..."}`

### 回调通知

- 平台以 POST form 方式回调 `notify_url`
- 回调参数包含 `out_trade_no`, `pay_no`（平台交易号）, `money`（元）, `sign` 等
- 验签方式同签名规则
- 处理成功须返回字符串 `SUCCESS`

### 订单查询

- 微信: `GET https://api.pay.yungouos.com/api/pay/wxpay/queryOrder?out_trade_no=...&mch_id=...&sign=...`
- 支付宝: `GET https://api.pay.yungouos.com/api/pay/alipay/queryOrder?out_trade_no=...&mch_id=...&sign=...`

---

## 抽象网关接口

```python
class PaymentGateway(ABC):
    @abstractmethod
    async def create_native_pay(
        out_trade_no: str,
        total_fee: str,       # 元，字符串
        body: str,
        notify_url: str,
        channel: str,         # "wechat" | "alipay"
        attach: str = "",
    ) -> dict:
        # 返回: {"qr_url": str, "qr_base64": str | None}
        ...

    @abstractmethod
    async def query_order(out_trade_no: str, channel: str) -> dict:
        # 返回: {"paid": bool, "trade_no": str, "amount": str}
        ...

    @abstractmethod
    def verify_notify(params: dict) -> bool:
        ...

    @abstractmethod
    async def refund(
        out_trade_no: str,
        refund_amount: str,
        refund_reason: str,
        channel: str,
    ) -> dict:
        ...
```

---

## 数据库变更

### `payment_orders` 表新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `qr_code_url` | Text | 二维码 URL，用于前端展示 |

### `PaymentType` 枚举新增

```python
NATIVE = "native"  # 扫码支付
```

### Alembic 迁移

新增一条迁移文件，添加 `qr_code_url` 字段。

---

## API 路由变更

### 保留（兼容现有前端）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/payment/orders/create` | 创建订单，新增 `payment_channel` 参数 |
| GET | `/payment/orders/{order_number}` | 查询订单详情 |
| POST | `/payment/orders/{order_number}/sync` | 主动同步状态 |
| GET | `/payment/subscription` | 获取订阅详情 |
| POST | `/payment/subscription/subscribe` | 订阅套餐 |
| PUT | `/payment/subscription/change` | 变更套餐 |

### 新增

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/payment/callback/yungouos/notify` | YunGouOS 统一回调（微信+支付宝共用） |

### 删除

- `POST /payment/callback/alipay/notify`
- `GET /payment/callback/alipay/return`
- `POST /payment/callback/wechat/notify`
- `POST /payment/wechat/orders/create`
- `POST /payment/wechat/orders/{order_number}/refund`

---

## 配置项（`.env` 新增）

```env
# YunGouOS 微信支付
YUNGOUOS_WECHAT_MCH_ID=
YUNGOUOS_WECHAT_KEY=

# YunGouOS 支付宝
YUNGOUOS_ALIPAY_MCH_ID=
YUNGOUOS_ALIPAY_KEY=

# 回调地址
YUNGOUOS_NOTIFY_URL=https://yourdomain.com/api/v1/payment/callback/yungouos/notify
```

---

## 前端变更

`SubscriptionPanel.tsx` 需要：

1. 订阅套餐选择改为 `monthly / quarterly / semi_annual / annual`
2. 支付方式选择：微信扫码 / 支付宝扫码
3. 展示二维码（使用 `qr_code_url` 字段）
4. 轮询订单状态（每 3 秒调用 `/payment/orders/{order_number}/sync`，超时 10 分钟）
5. 支付成功后刷新订阅状态

---

## 不在本次范围内

- H5/WAP 支付
- 退款功能前端 UI（后端接口保留）
- 自动续费
