# API Key 自助重置功能实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让已登录租户可以在设置页查看 API Key 前缀并自助重置，重置后弹窗展示新 Key（仅一次），重置前有确认弹窗防止误操作。

**Architecture:** 后端新增 `POST /api/v1/tenant/reset-api-key` 端点（JWT 认证），复用已有 `TenantService.reset_api_key()` 方法；前端重写设置页 API 密钥页签，展示前缀 + 重置按钮 + 确认弹窗 + 结果弹窗。

**Tech Stack:** FastAPI + Pydantic v2（后端）、Next.js 14 + Ant Design v6 + TypeScript（前端）

---

### Task 1: 后端 — 新增 ResetApiKeyResponse schema

**Files:**
- Modify: `backend/schemas/tenant.py`（在 TenantRegisterResponse 之后追加）
- Modify: `backend/schemas/__init__.py`（导出新 schema）

**Step 1: 在 `backend/schemas/tenant.py` 末尾的注册 schema 区块后追加**

在文件第 195 行（TenantRegisterResponse 类结束后）追加：

```python
class ResetApiKeyResponse(BaseSchema):
    """重置 API Key 响应"""

    api_key: str = Field(..., description="新的 API Key（明文，仅此一次）")
    api_key_prefix: str = Field(..., description="API Key 前缀")
    message: str = "API Key 已重置，请妥善保存"
```

**Step 2: 在 `backend/schemas/__init__.py` 中导出**

在第 56 行 `from schemas.tenant import (` 块内，`TenantWithAPIKey,` 后追加：
```python
    ResetApiKeyResponse,
```

在第 118 行 `"TenantWithAPIKey",` 后的 `__all__` 列表中追加：
```python
    "ResetApiKeyResponse",
```

**Step 3: 提交**

```bash
git add backend/schemas/tenant.py backend/schemas/__init__.py
git commit -m "feat: add ResetApiKeyResponse schema"
```

---

### Task 2: 后端 — 新增租户自助重置端点

**Files:**
- Modify: `backend/api/routers/tenant.py`

**Step 1: 在 `backend/api/routers/tenant.py` 第 26 行的 imports 中追加 ResetApiKeyResponse**

将：
```python
from schemas import (
    ApiResponse,
    PaginatedResponse,
    SubscriptionResponse,
    TenantLoginRequest,
    TenantLoginResponse,
    TenantRegisterRequest,
    TenantRegisterResponse,
    TenantResponse,
    UsageRecordResponse,
    SubscribePlanRequest,
    ChangePlanRequest,
    SubscriptionDetail,
    ProratedPriceDetail,
    SubscriptionOperationResponse,
)
```

改为：
```python
from schemas import (
    ApiResponse,
    PaginatedResponse,
    ResetApiKeyResponse,
    SubscriptionResponse,
    TenantLoginRequest,
    TenantLoginResponse,
    TenantRegisterRequest,
    TenantRegisterResponse,
    TenantResponse,
    UsageRecordResponse,
    SubscribePlanRequest,
    ChangePlanRequest,
    SubscriptionDetail,
    ProratedPriceDetail,
    SubscriptionOperationResponse,
)
```

**Step 2: 在 `backend/api/routers/tenant.py` 中找到 `get_tenant_info` 端点后，追加新端点**

在 `/info` 端点之后追加：

```python
@router.post("/reset-api-key", response_model=ApiResponse[ResetApiKeyResponse])
async def reset_api_key(
    tenant_id: TenantTokenDep,
    db: DBDep,
):
    """
    租户自助重置 API Key

    重置后旧 Key 立即失效，新 Key 仅在响应中返回一次，请妥善保存。
    需要 JWT Token 认证（登录后可用）。
    """
    service = TenantService(db)
    tenant, new_api_key = await service.reset_api_key(tenant_id)
    return ApiResponse(
        data=ResetApiKeyResponse(
            api_key=new_api_key,
            api_key_prefix=tenant.api_key_prefix or new_api_key[:12],
        )
    )
```

**Step 3: 提交**

```bash
git add backend/api/routers/tenant.py
git commit -m "feat: add tenant self-service reset-api-key endpoint"
```

---

### Task 3: 前端 — 新增 resetApiKey API 函数 & TenantInfo 补充 api_key_prefix

**Files:**
- Modify: `frontend/src/lib/api/settings.ts`

**Step 1: 在 `TenantInfo` interface（第 39 行）中追加 `api_key_prefix` 字段**

将：
```typescript
export interface TenantInfo {
  id: number;
  tenant_id: string;
  company_name: string;
  contact_name: string | null;
  contact_email: string;
  contact_phone: string | null;
  status: string;
  current_plan: string;
}
```

改为：
```typescript
export interface TenantInfo {
  id: number;
  tenant_id: string;
  company_name: string;
  contact_name: string | null;
  contact_email: string;
  contact_phone: string | null;
  status: string;
  current_plan: string;
  api_key_prefix: string | null;
}
```

**Step 2: 在 `settingsApi` 对象末尾（第 214 行 `};` 之前）追加两个方法**

```typescript
  // Get tenant info (includes api_key_prefix)
  getTenantInfo: async (): Promise<ApiResponse<TenantInfo>> => {
    const response = await apiClient.get<ApiResponse<TenantInfo>>('/tenant/info-token');
    return response.data;
  },

  // Reset tenant API Key (returns new key once)
  resetApiKey: async (): Promise<ApiResponse<{ api_key: string; api_key_prefix: string; message: string }>> => {
    const response = await apiClient.post<ApiResponse<{ api_key: string; api_key_prefix: string; message: string }>>('/tenant/reset-api-key');
    return response.data;
  },
```

**Step 3: 提交**

```bash
git add frontend/src/lib/api/settings.ts
git commit -m "feat: add getTenantInfo and resetApiKey API functions"
```

---

### Task 4: 前端 — 重写设置页 API 密钥页签

**Files:**
- Modify: `frontend/src/app/(dashboard)/settings/page.tsx`

**Step 1: 在文件顶部 imports 中追加 Modal 和 KeyOutlined（Modal 已在 antd import 中，追加 KeyOutlined）**

将第 7 行：
```typescript
import { CopyOutlined, LinkOutlined, DisconnectOutlined, CheckCircleOutlined } from '@ant-design/icons';
```
改为：
```typescript
import { CopyOutlined, LinkOutlined, DisconnectOutlined, CheckCircleOutlined, KeyOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
```

将第 5 行 antd import 中的 `Modal` 确认已存在（当前已有），同时追加 `Paragraph`：
```typescript
import { useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';
import { Row, Col, Card, Typography, message, Alert, Form, Input, Button, Slider, Spin, Steps, Modal } from 'antd';
```

**Step 2: 在 `settingsApi` import 中追加**

将第 9 行：
```typescript
import { platformApi, PlatformConfig } from '@/lib/api/platform';
```
改为：
```typescript
import { platformApi, PlatformConfig } from '@/lib/api/platform';
import { settingsApi } from '@/lib/api/settings';
```

**Step 3: 在组件内（`const { tenantId } = useAuthStore();` 之后）追加 API 密钥相关 state**

```typescript
  const [apiKeyPrefix, setApiKeyPrefix] = useState<string | null>(null);
  const [apiKeyLoading, setApiKeyLoading] = useState(false);
  const [resetConfirmOpen, setResetConfirmOpen] = useState(false);
  const [newApiKeyModal, setNewApiKeyModal] = useState(false);
  const [newApiKey, setNewApiKey] = useState('');
```

**Step 4: 追加加载 api_key_prefix 的 useEffect**

在现有 `useEffect`（platform 那个）之后追加：

```typescript
  useEffect(() => {
    if (selectedMenu === 'api') {
      settingsApi.getTenantInfo().then((res) => {
        if (res.success && res.data) {
          setApiKeyPrefix(res.data.api_key_prefix);
        }
      });
    }
  }, [selectedMenu]);
```

**Step 5: 追加重置处理函数**

在 `renderContent` 函数之前追加：

```typescript
  const handleResetApiKey = async () => {
    setApiKeyLoading(true);
    setResetConfirmOpen(false);
    try {
      const res = await settingsApi.resetApiKey();
      if (res.success && res.data) {
        setNewApiKey(res.data.api_key);
        setApiKeyPrefix(res.data.api_key_prefix);
        setNewApiKeyModal(true);
      } else {
        message.error('重置失败，请重试');
      }
    } catch {
      message.error('重置失败，请重试');
    } finally {
      setApiKeyLoading(false);
    }
  };
```

**Step 6: 替换 `case 'api':` 的整个 return 块**

将原来第 54-102 行的 `case 'api':` 块替换为：

```typescript
      case 'api':
        return (
          <>
            <Card>
              <Title level={5} className="mb-4">API 密钥管理</Title>
              <Alert
                message="API 密钥用于外部系统接入"
                description="您可以使用此 API 密钥将智能客服集成到您的应用中。请妥善保管，不要泄露给他人。"
                type="info"
                showIcon
                className="mb-6"
              />
              <div className="bg-gray-100 p-4 rounded-lg">
                <Text type="secondary" className="block mb-2">租户 ID:</Text>
                <div className="flex items-center gap-2 mb-4">
                  <Input
                    value={tenantId || ''}
                    readOnly
                    style={{ flex: 1, fontFamily: 'monospace' }}
                  />
                  <Button
                    icon={<CopyOutlined />}
                    onClick={() => {
                      if (tenantId) {
                        navigator.clipboard.writeText(tenantId);
                        message.success('已复制到剪贴板');
                      }
                    }}
                  >
                    复制
                  </Button>
                </div>
                <Text type="secondary" className="block mb-2">API Key 前缀:</Text>
                <div className="flex items-center gap-2">
                  <Input
                    value={apiKeyPrefix ? `${apiKeyPrefix}...` : '（未知，请重置获取新 Key）'}
                    readOnly
                    style={{ flex: 1, fontFamily: 'monospace' }}
                    prefix={<KeyOutlined />}
                  />
                  <Button
                    danger
                    loading={apiKeyLoading}
                    onClick={() => setResetConfirmOpen(true)}
                  >
                    重置 API Key
                  </Button>
                </div>
              </div>
              <Alert
                message="认证方式"
                description="外部 API 请求在 Header 中添加 X-API-Key: {api_key}；Dashboard 使用 Authorization: Bearer {access_token}"
                type="info"
                showIcon
                className="mt-4"
              />
            </Card>

            {/* 确认重置弹窗 */}
            <Modal
              title={<span><ExclamationCircleOutlined className="text-yellow-500 mr-2" />确认重置 API Key</span>}
              open={resetConfirmOpen}
              onOk={handleResetApiKey}
              onCancel={() => setResetConfirmOpen(false)}
              okText="确认重置"
              cancelText="取消"
              okButtonProps={{ danger: true }}
            >
              <p>重置后，旧的 API Key 将<strong>立即失效</strong>，所有使用旧 Key 的集成需要同步更新。</p>
              <p>确认继续？</p>
            </Modal>

            {/* 新 Key 展示弹窗 */}
            <Modal
              title="API Key 已重置"
              open={newApiKeyModal}
              onOk={() => setNewApiKeyModal(false)}
              onCancel={() => setNewApiKeyModal(false)}
              okText="我已保存"
              cancelButtonProps={{ style: { display: 'none' } }}
            >
              <Alert
                message="请立即复制保存，此 Key 仅显示一次"
                type="warning"
                showIcon
                className="mb-4"
              />
              <Input.Password
                value={newApiKey}
                readOnly
                style={{ fontFamily: 'monospace' }}
                addonAfter={
                  <CopyOutlined
                    style={{ cursor: 'pointer' }}
                    onClick={() => {
                      navigator.clipboard.writeText(newApiKey);
                      message.success('已复制到剪贴板');
                    }}
                  />
                }
              />
            </Modal>
          </>
        );
```

**Step 7: 提交**

```bash
git add frontend/src/app/(dashboard)/settings/page.tsx
git commit -m "feat: rewrite API key tab with prefix display and self-service reset"
```

---

### Task 5: 验证

**Step 1: 重新构建并部署**

```bash
docker compose build api frontend && docker compose up -d api frontend
```

**Step 2: 功能验证**

1. 登录后访问 `/settings?menu=api`
2. 确认显示 API Key 前缀（`eck_xxx...`）
3. 点击"重置 API Key" → 确认弹窗出现，内容包含"立即失效"警告
4. 点击"确认重置" → 新 Key 弹窗出现，显示完整 Key，可复制
5. 关闭弹窗后，前缀更新为新 Key 的前缀
6. 用旧 Key 调用 `GET /api/v1/tenant/info`（Header: `X-API-Key: 旧key`）→ 应返回 401
7. 用新 Key 调用同一接口 → 应返回 200
