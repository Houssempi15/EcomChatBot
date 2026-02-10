# Jenkins CI/CD 配置文件

## 📁 目录结构

```
.jenkins/
├── Dockerfile              # Jenkins测试Agent镜像
├── docker-compose.yml      # Docker Compose配置
└── README.md              # 本文档
```

## 🚀 快速开始

### 方法一：使用现有Jenkins

1. **在Jenkins中创建Pipeline项目**

```
新建任务 → 输入任务名称 → 选择"流水线" → 确定
```

2. **配置Pipeline**

```
Pipeline → Definition: Pipeline script from SCM
SCM: Git
Repository URL: <your-git-repo>
Script Path: Jenkinsfile
```

3. **保存并构建**

```
点击"保存" → 点击"立即构建"
```

### 方法二：使用Docker运行测试Agent

1. **构建Docker镜像**

```bash
cd .jenkins
docker-compose build
```

2. **启动容器**

```bash
docker-compose up -d
```

3. **进入容器运行测试**

```bash
# 进入容器
docker exec -it ecom-chat-bot-test-agent bash

# 激活环境
source activate ecom-chat-bot

# 运行测试
cd /workspace/backend/tests
pytest -v
```

4. **查看报告**

```bash
# 报告在宿主机的 .jenkins/reports 目录
open .jenkins/reports/html/report.html
```

## ⚙️ Jenkins配置步骤

### 1. 配置Jenkins凭证

在Jenkins中添加以下凭证：

#### 通知邮箱
```
ID: notification-email
类型: Secret text
值: your-email@example.com
```

#### 钉钉Webhook
```
ID: dingtalk-webhook
类型: Secret text
值: https://oapi.dingtalk.com/robot/send?access_token=xxx
```

### 2. 安装Jenkins插件

必需插件：
- Pipeline
- Git Plugin
- HTML Publisher Plugin
- JUnit Plugin
- Email Extension Plugin
- AnsiColor Plugin

安装方式：
```
系统管理 → 插件管理 → 可选插件 → 搜索并安装
```

### 3. 配置全局工具

```
系统管理 → Global Tool Configuration

Git:
  Name: Default
  Path: git

Python:
  Name: Python 3.11
  Install automatically: 勾选
```

### 4. 配置系统

```
系统管理 → 系统配置

Jenkins Location:
  Jenkins URL: http://your-jenkins-server

Email Notification:
  SMTP server: smtp.example.com
  Default user e-mail suffix: @example.com
```

## 🎯 Pipeline参数说明

### 构建参数

| 参数名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| TEST_LEVEL | Choice | quick | 测试级别<br>- quick: 快速测试<br>- full: 完整测试<br>- api: API测试<br>- integration: 集成测试<br>- performance: 性能测试<br>- security: 安全测试 |
| SKIP_SLOW_TESTS | Boolean | true | 是否跳过慢速测试 |
| RUN_PERFORMANCE_TESTS | Boolean | false | 是否运行性能测试 |
| RUN_SECURITY_TESTS | Boolean | false | 是否运行安全测试 |
| CLEANUP_TEST_DATA | Boolean | true | 测试后是否清理数据 |

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| TEST_BASE_URL | 测试环境URL | http://115.190.75.88:8000 |
| CONDA_ENV | Conda环境名称 | ecom-chat-bot |
| PYTHON_VERSION | Python版本 | 3.11 |

## 📊 查看测试报告

### 在Jenkins中查看

构建完成后，在构建页面左侧菜单：

1. **测试报告** - 点击查看HTML测试报告
2. **覆盖率报告** - 点击查看代码覆盖率
3. **Test Result** - 查看JUnit测试结果
4. **Artifacts** - 下载完整报告

### 通过URL访问

```
# 测试报告
http://jenkins-server/job/{job-name}/{build-number}/测试报告/

# 覆盖率报告  
http://jenkins-server/job/{job-name}/{build-number}/覆盖率报告/

# JUnit结果
http://jenkins-server/job/{job-name}/{build-number}/testReport/
```

## 🔔 配置通知

### 邮件通知

1. 在Jenkins中配置SMTP服务器
2. 在Jenkinsfile中已配置，会自动发送

### 钉钉通知

1. 创建钉钉机器人获取webhook
2. 在Jenkins中添加凭证（ID: dingtalk-webhook）
3. Pipeline会自动发送通知

### 企业微信通知

在Jenkinsfile中添加：

```groovy
environment {
    WECHAT_WEBHOOK = credentials('wechat-webhook')
}

// 在sendNotification函数中添加
if (env.WECHAT_WEBHOOK) {
    sh """
        curl -X POST ${env.WECHAT_WEBHOOK} \
        -H 'Content-Type: application/json' \
        -d '{"msgtype":"markdown","markdown":{"content":"${message}"}}'
    """
}
```

## 🔧 故障排查

### 问题1：Pipeline执行失败

**检查步骤：**
```bash
# 查看Jenkins日志
tail -f /var/log/jenkins/jenkins.log

# 查看构建日志
# 在Jenkins UI中点击构建号 → Console Output
```

### 问题2：测试环境不可访问

**解决方案：**
```bash
# 在Jenkins节点上测试
curl -v http://115.190.75.88:8000/health

# 检查网络配置
ping 115.190.75.88

# 检查防火墙规则
```

### 问题3：依赖安装失败

**解决方案：**
```bash
# 使用国内镜像
pip install -r requirements-test.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple

# 或在Dockerfile中配置
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题4：报告发布失败

**解决方案：**
```groovy
// 确保目录存在
sh 'mkdir -p backend/tests/reports/html'

// 使用正确的路径
publishHTML([
    reportDir: 'backend/tests/reports/html',
    reportFiles: 'report.html',
    reportName: '测试报告'
])
```

## 📚 相关文档

- [Jenkins完整配置指南](../backend/tests/JENKINS.md)
- [测试框架文档](../backend/tests/README.md)
- [快速开始指南](../backend/tests/QUICKSTART.md)

## 🎉 完成检查清单

- [ ] Jenkins服务器已安装并运行
- [ ] 必需插件已安装
- [ ] Git仓库已配置
- [ ] 凭证已添加（邮箱、Webhook等）
- [ ] Pipeline项目已创建
- [ ] Jenkinsfile已提交到代码仓库
- [ ] 首次构建成功
- [ ] 测试报告可以正常查看
- [ ] 通知功能正常工作

---

✅ Jenkins CI/CD集成配置完成！
