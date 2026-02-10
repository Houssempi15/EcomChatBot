# Jenkins集成 - 5分钟快速配置

## 🚀 最简配置（3步完成）

### 步骤1：复制Jenkinsfile (30秒)

Jenkinsfile已经在项目根目录，无需额外操作。

```
ecom-chat-bot/
└── Jenkinsfile  ✅ 已存在
```

### 步骤2：创建Jenkins Job (2分钟)

1. **打开Jenkins** → 点击"新建任务"

2. **输入任务名称**: `ecom-chat-bot-tests`

3. **选择类型**: `流水线 (Pipeline)`

4. **点击"确定"**

5. **配置Pipeline**:
   ```
   Definition: Pipeline script from SCM
   SCM: Git
   Repository URL: <你的Git仓库URL>
   Credentials: <选择Git凭证>
   Branch: */develop (或你的分支)
   Script Path: Jenkinsfile
   ```

6. **点击"保存"**

### 步骤3：运行测试 (1分钟)

1. 点击"立即构建"
2. 等待构建完成
3. 查看测试报告

**完成！** ✅

---

## 📊 查看测试结果

构建完成后，左侧菜单会显示：

- 🔷 **测试报告** - HTML测试报告
- 🔷 **Test Result** - JUnit结果
- 🔷 **Build Artifacts** - 下载完整报告

---

## ⚙️ 可选配置（按需）

### 配置1：添加构建参数（可选）

在Job配置中勾选"参数化构建过程"，添加：

| 参数 | 类型 | 选项/默认值 |
|------|------|------------|
| TEST_LEVEL | Choice | quick, full, api, integration |

### 配置2：配置通知（可选）

**邮件通知**:
```
系统管理 → 系统配置 → 邮件通知
SMTP服务器: smtp.example.com
```

**钉钉通知**:
```
系统管理 → Manage Credentials → 添加凭证
ID: dingtalk-webhook
Secret: <钉钉webhook URL>
```

### 配置3：定时构建（可选）

在Job配置中添加：
```
构建触发器 → 定时构建
H 2 * * *  (每天凌晨2点)
```

---

## 🎯 测试级别选择

根据场景选择合适的测试级别：

### Quick (快速测试) - 推荐日常使用
```
耗时: 5-10分钟
覆盖: 基础API测试
适用: 代码提交后
```

### Full (完整测试) - 推荐定时执行
```
耗时: 20-30分钟
覆盖: 所有测试+覆盖率
适用: 每日构建
```

### API (API测试)
```
耗时: 10-15分钟
覆盖: 所有API端点
适用: API变更后
```

### Integration (集成测试)
```
耗时: 15-20分钟
覆盖: 完整业务流程
适用: 发布前验证
```

---

## 🐛 常见问题

### Q1: 构建失败，提示"conda: command not found"

**解决**：在Jenkins节点上安装Conda
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

### Q2: 测试环境连接失败

**解决**：检查Jenkins节点网络
```bash
# 在Jenkins节点上测试
curl http://115.190.75.88:8000/health
```

### Q3: 报告无法显示

**解决**：安装HTML Publisher插件
```
系统管理 → 插件管理 → 搜索"HTML Publisher" → 安装
```

### Q4: Git仓库访问失败

**解决**：配置Git凭证
```
Jenkins → Credentials → 添加 → Username with password
```

---

## 📱 移动端查看（可选）

安装Jenkins移动应用：
- iOS: Jenkins Mobile
- Android: Jenkins Dashboard

随时随地查看构建状态！

---

## 📞 需要帮助？

查看完整文档：
- 📘 [Jenkins完整配置](JENKINS.md)
- 📗 [测试框架文档](README.md)
- 📙 [故障排查指南](JENKINS.md#故障排查)

---

**🎉 完成！现在你可以：**
- ✅ 自动化测试代码
- ✅ 查看详细报告
- ✅ 接收测试通知
- ✅ 追踪测试趋势

**开始你的第一次构建吧！** 🚀
