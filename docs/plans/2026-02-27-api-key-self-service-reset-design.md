# API 密钥自助重置功能设计

## 背景

租户登录后，设置页"API密钥"页签无法展示真正的 API Key（`eck_xxx...`）。
原因：API Key 在数据库中以哈希形式存储，注册时仅明文返回一次，之后无法反查。
当前页签只显示固定占位文本，对用户毫无价值。

## 目标

- 展示 API Key 前缀（`api_key_prefix` 字段），让用户确认当前 Key 的身份
- 提供租户自助重置入口，重置后弹窗展示新 Key（仅一次）
- 重置前有确认弹窗，防止误操作导致旧 Key 失效

---

## 架构设计

### 后端

新增租户自助重置端点，使用 JWT Token 认证（已登录即可调用）：

```
POST /api/v1/tenant/reset-api-key
Authorization: Bearer {access_token}
```

响应：
```json
{
  "api_key": "eck_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "message": "API Key 已重置，请妥善保存"
}
```

复用已有的 `TenantService.reset_api_key()` 方法（`backend/services/tenant_service.py`）。

新增 `ResetApiKeyResponse` schema（`backend/schemas/tenant.py`）。

### 前端

设置页 API 密钥页签重写，展示：
1. 租户 ID（只读可复制，保留现有逻辑）
2. API Key 前缀（从 `/tenant/info` 接口的 `api_key_prefix` 字段读取）
3. "重置 API Key" 按钮

交互流程：
- 点击重置 → 确认 Modal（警告旧 Key 立即失效）
- 确认 → 调用重置接口 → 结果 Modal 展示完整新 Key + 一键复制 + "仅显示一次"提示

---

## 涉及文件

| 文件 | 改动 |
|------|------|
| `backend/api/routers/tenant.py` | 新增 `POST /reset-api-key` 端点 |
| `backend/services/tenant_service.py` | 复用已有 `reset_api_key` 方法，无需修改 |
| `backend/schemas/tenant.py` | 新增 `ResetApiKeyResponse` schema |
| `frontend/src/lib/api/settings.ts` | 新增 `resetApiKey()` 调用函数 |
| `frontend/src/app/(dashboard)/settings/page.tsx` | 重写 API 密钥页签 UI |

---

## 验证方式

1. 登录后进入 `/settings?menu=api`，确认显示 API Key 前缀
2. 点击重置，确认弹窗出现
3. 确认重置，验证新 Key 弹窗展示且可复制
4. 用旧 Key 调用 API，确认返回 401
5. 用新 Key 调用 API，确认正常响应
