# 任务状态轮询优化实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 优化海报和视频生成任务的状态刷新机制，确保任务提交后状态能够实时自动更新

**Architecture:** 通过在任务创建成功后立即更新本地 tasks 状态，确保轮询机制能够立即启动。同时优化轮询逻辑，在检测到 pending 任务时立即执行一次数据加载。

**Tech Stack:** React, TypeScript, Next.js 14, Ant Design

---

## Task 1: 优化视频生成页面的任务状态刷新

**Files:**
- Modify: `frontend/src/app/(dashboard)/content/video/page.tsx:115-133`
- Modify: `frontend/src/app/(dashboard)/content/video/page.tsx:84-89`

**Step 1: 修改 handleGenerate 函数，立即更新 tasks 状态**

在 `handleGenerate` 函数中，当任务创建成功后，立即将新任务添加到 tasks 状态：

```typescript
const handleGenerate = async () => {
  if (!prompt.trim()) { message.warning('请输入生成提示词'); return; }
  setGenerating(true);
  try {
    const params: Record<string, unknown> = { duration };
    if (imageUrl) params.image_url = imageUrl;
    const resp = await contentApi.createGeneration({
      task_type: 'video',
      prompt: prompt.trim(),
      product_id: selectedProduct,
      prompt_id: selectedPrompt,
      model_config_id: selectedModel,
      params,
    });
    if (resp.success && resp.data) {
      message.success('视频生成任务已创建');
      setPrompt('');
      setImageUrl('');
      // 关键改动：立即将新任务添加到 tasks 状态
      setTasks(prev => [resp.data, ...prev]);
      // 仍然调用 loadData 以获取完整数据
      loadData();
    }
    else { message.error(resp.error?.message || '创建失败'); }
  } catch { message.error('创建任务失败'); }
  finally { setGenerating(false); }
};
```

**Step 2: 优化轮询逻辑，立即执行一次 loadData**

修改轮询的 useEffect，在检测到 pending 任务时立即执行一次 loadData：

```typescript
useEffect(() => {
  const hasPending = tasks.some(t => ['pending', 'processing'].includes(t.status));
  if (!hasPending) return;
  // 立即执行一次，不等待5秒
  loadData();
  const timer = setInterval(loadData, 5000);
  return () => clearInterval(timer);
}, [tasks, loadData]);
```

**Step 3: 测试视频生成功能**

手动测试：
1. 启动前端开发服务器
2. 访问视频生成页面 `/dashboard/content/video`
3. 填写提示词并点击"生成视频"
4. 验证任务立即出现在"最近任务"列表中
5. 观察任务状态是否自动从"等待中"变为"生成中"再到"已完成"
6. 验证生成结果是否自动出现在右侧

**Step 4: 提交代码**

```bash
git add frontend/src/app/(dashboard)/content/video/page.tsx
git commit -m "fix: optimize video task status polling

立即更新本地 tasks 状态，确保轮询机制能够启动。
在检测到 pending 任务时立即执行一次 loadData。

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: 优化海报生成页面的任务状态刷新

**Files:**
- Modify: `frontend/src/app/(dashboard)/content/poster/page.tsx:127-145`
- Modify: `frontend/src/app/(dashboard)/content/poster/page.tsx:93-98`

**Step 1: 修改 handleGenerate 函数，立即更新 tasks 状态**

在 `handleGenerate` 函数中，当任务创建成功后，立即将新任务添加到 tasks 状态：

```typescript
const handleGenerate = async () => {
  if (!prompt.trim()) { message.warning('请输入生成提示词'); return; }
  setGenerating(true);
  try {
    const params: Record<string, unknown> = { size: imageSize };
    if (supportsBatch) params.n = imageCount;
    const resp = await contentApi.createGeneration({
      task_type: 'poster',
      prompt: prompt.trim(),
      product_id: selectedProduct,
      prompt_id: selectedPrompt,
      model_config_id: selectedModel,
      params,
    });
    if (resp.success && resp.data) {
      message.success('海报生成任务已创建');
      setPrompt('');
      // 关键改动：立即将新任务添加到 tasks 状态
      setTasks(prev => [resp.data, ...prev]);
      // 仍然调用 loadData 以获取完整数据
      loadData();
    }
    else { message.error(resp.error?.message || '创建失败'); }
  } catch { message.error('创建任务失败'); }
  finally { setGenerating(false); }
};
```

**Step 2: 优化轮询逻辑，立即执行一次 loadData**

修改轮询的 useEffect，在检测到 pending 任务时立即执行一次 loadData：

```typescript
useEffect(() => {
  const hasPending = tasks.some(t => ['pending', 'processing'].includes(t.status));
  if (!hasPending) return;
  // 立即执行一次，不等待5秒
  loadData();
  const timer = setInterval(loadData, 5000);
  return () => clearInterval(timer);
}, [tasks, loadData]);
```

**Step 3: 测试海报生成功能**

手动测试：
1. 访问海报生成页面 `/dashboard/content/poster`
2. 填写提示词并点击"生成海报"
3. 验证任务立即出现在"最近任务"列表中
4. 观察任务状态是否自动从"等待中"变为"生成中"再到"已完成"
5. 验证生成结果是否自动出现在右侧
6. 测试生成多张海报的场景

**Step 4: 提交代码**

```bash
git add frontend/src/app/(dashboard)/content/poster/page.tsx
git commit -m "fix: optimize poster task status polling

立即更新本地 tasks 状态，确保轮询机制能够启动。
在检测到 pending 任务时立即执行一次 loadData。

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: 端到端测试

**Step 1: 测试视频生成完整流程**

1. 清空浏览器缓存
2. 访问视频生成页面
3. 提交一个视频生成任务
4. 验证任务立即出现在列表中（状态：等待中）
5. 等待5秒内，验证状态自动更新为"生成中"
6. 等待任务完成，验证状态自动更新为"已完成"
7. 验证生成的视频自动出现在右侧结果区域
8. 点击视频链接，验证可以正常播放

**Step 2: 测试海报生成完整流程**

1. 访问海报生成页面
2. 提交一个海报生成任务（生成1张）
3. 验证任务立即出现在列表中
4. 验证状态自动更新
5. 验证生成的海报自动出现在右侧
6. 提交一个生成多张海报的任务（生成4张）
7. 验证所有海报都能正常显示

**Step 3: 测试失败场景**

1. 提交一个会失败的任务（例如：使用无效的 API Key）
2. 验证任务状态自动更新为"失败"
3. 验证错误信息正确显示
4. 点击"重试"按钮
5. 验证任务状态重新变为"等待中"并开始轮询

**Step 4: 测试并发场景**

1. 快速连续提交3个视频生成任务
2. 验证所有任务都立即出现在列表中
3. 验证所有任务的状态都能正确自动更新
4. 验证轮询在所有任务完成后自动停止

**Step 5: 记录测试结果**

创建测试报告，记录：
- 所有测试场景的结果
- 发现的问题（如果有）
- 性能观察（轮询频率、网络请求数量等）

---

## Task 4: 部署和验证

**Step 1: 构建前端**

```bash
cd frontend
npm run build
```

预期：构建成功，无错误

**Step 2: 重新部署前端服务**

```bash
cd ..
docker compose build frontend
docker compose up -d frontend
```

预期：容器成功重启

**Step 3: 生产环境验证**

1. 访问生产环境的视频生成页面
2. 提交测试任务
3. 验证任务状态实时刷新功能正常
4. 访问海报生成页面
5. 提交测试任务
6. 验证任务状态实时刷新功能正常

**Step 4: 监控和观察**

观察以下指标：
- 前端控制台是否有错误
- 网络请求是否正常
- 任务状态更新是否及时
- 用户体验是否改善

**Step 5: 最终提交**

如果一切正常，创建最终的总结提交：

```bash
git add .
git commit -m "fix: complete task status polling optimization

优化海报和视频生成任务的状态刷新机制：
- 任务创建后立即更新本地状态
- 优化轮询逻辑，确保及时启动
- 改善用户体验，无需手动刷新页面

测试通过：
- 视频生成任务状态实时刷新
- 海报生成任务状态实时刷新
- 失败场景和重试功能正常
- 并发任务场景正常

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## 注意事项

1. **DRY 原则**：两个页面的改动几乎相同，但由于它们是独立的页面组件，暂不提取公共逻辑
2. **YAGNI 原则**：只实现必要的功能，不添加额外的复杂性
3. **测试优先**：虽然这是前端 UI 改动，但仍需要充分的手动测试
4. **频繁提交**：每完成一个页面就提交一次，便于回滚

## 后续优化建议

1. 考虑提取公共的轮询逻辑到自定义 Hook
2. 添加单元测试和集成测试
3. 考虑引入 WebSocket 实现真正的实时推送
4. 添加任务进度显示功能

