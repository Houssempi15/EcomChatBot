# Jenkins CI/CD 集成指南

## 📋 概述

本文档介绍如何将测试框架集成到Jenkins CI/CD流水线中。

## 🚀 快速开始

### 1. Jenkins环境要求

#### 必需组件
- Jenkins 2.300+
- Python 3.11+
- Conda (推荐) 或 venv
- Git

#### 推荐插件
- Pipeline
- Git Plugin
- HTML Publisher Plugin
- JUnit Plugin
- Email Extension Plugin
- AnsiColor Plugin

### 2. 创建Jenkins Job

#### 方法一：使用Pipeline（推荐）

1. 在Jenkins中创建新的Pipeline项目
2. 配置Git仓库URL
3. 指定Jenkinsfile路径：`Jenkinsfile`
4. 保存配置

#### 方法二：使用Freestyle Project

1. 创建Freestyle项目
2. 配置Git仓库
3. 添加构建步骤：Execute Shell
4. 输入构建脚本（见下文）

## 📝 Jenkinsfile 说明

### 主要功能

#### 1. 参数化构建

支持以下参数：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `TEST_LEVEL` | Choice | quick | 测试级别（quick/full/api/integration/performance/security） |
| `SKIP_SLOW_TESTS` | Boolean | true | 是否跳过慢速测试 |
| `RUN_PERFORMANCE_TESTS` | Boolean | false | 是否运行性能测试 |
| `RUN_SECURITY_TESTS` | Boolean | false | 是否运行安全测试 |
| `CLEANUP_TEST_DATA` | Boolean | true | 测试后是否清理数据 |

#### 2. 构建阶段

```
准备环境 → 检查环境 → 安装依赖 → 配置测试环境 
    ↓
运行测试 → 收集报告 → 分析结果
```

#### 3. 构建触发器

- **定时触发**: 每天凌晨2点执行完整测试
- **Git推送**: 可配置webhook自动触发
- **手动触发**: 通过Jenkins UI手动启动

#### 4. 测试报告

自动生成并发布：
- JUnit测试报告
- HTML测试报告
- 代码覆盖率报告

#### 5. 通知机制

支持：
- 邮件通知
- 钉钉通知
- 企业微信通知（需配置）

## ⚙️ 配置说明

### 1. 环境变量配置

在Jenkins中配置以下凭证：

#### Credentials配置

```
ID: notification-email
Type: Secret text
Value: your-email@example.com

ID: dingtalk-webhook
Type: Secret text
Value: https://oapi.dingtalk.com/robot/send?access_token=xxx
```

#### 全局环境变量

在Jenkins系统配置中设置：

```bash
CONDA_HOME=/opt/conda
PATH=$CONDA_HOME/bin:$PATH
```

### 2. Jenkins节点配置

#### 标签设置

为节点添加标签（可选）：
```
labels: python, conda, testing
```

#### 工具配置

在 "Global Tool Configuration" 中配置：

- **Git**: 配置Git安装路径
- **Python**: 配置Python 3.11+路径

## 🔧 初始化Jenkins节点

### 在Jenkins节点上首次运行

```bash
# 1. 克隆代码
git clone <repository-url>
cd ecom-chat-bot

# 2. 运行环境配置脚本
cd backend/tests
./jenkins-setup.sh

# 3. 验证环境
pytest --version
```

### 使用Docker（可选）

如果使用Docker运行Jenkins节点：

```dockerfile
# Dockerfile.jenkins-agent
FROM jenkins/jenkins:lts

USER root

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    curl \
    git

# 安装Miniconda
RUN curl -O https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/conda && \
    rm Miniconda3-latest-Linux-x86_64.sh

ENV PATH=/opt/conda/bin:$PATH

USER jenkins
```

构建和运行：

```bash
docker build -f Dockerfile.jenkins-agent -t jenkins-test-agent .
docker run -d --name jenkins-agent jenkins-test-agent
```

## 📊 查看测试报告

### 1. 在Jenkins UI中

构建完成后，在构建页面左侧菜单可以看到：

- **测试报告**: 点击查看HTML报告
- **覆盖率报告**: 点击查看代码覆盖率
- **构建产物**: 下载完整报告

### 2. 通过URL访问

```
# 测试报告
http://jenkins-server/job/{job-name}/{build-number}/测试报告/

# 覆盖率报告
http://jenkins-server/job/{job-name}/{build-number}/覆盖率报告/
```

## 🎯 使用场景

### 场景1：提交代码后自动测试

配置Git webhook触发：

```groovy
triggers {
    githubPush()
}
```

每次push代码后自动运行快速测试。

### 场景2：定时全量测试

配置定时任务：

```groovy
triggers {
    cron('0 2 * * *')  // 每天凌晨2点
}
```

### 场景3：发布前验证

在发布流水线中添加测试阶段：

```groovy
stage('测试验证') {
    steps {
        build job: 'ecom-chat-bot-tests',
            parameters: [
                string(name: 'TEST_LEVEL', value: 'full')
            ]
    }
}
```

### 场景4：性能监控

定期运行性能测试：

```groovy
pipeline {
    triggers {
        cron('0 3 * * 0')  // 每周日凌晨3点
    }
    stages {
        stage('性能测试') {
            steps {
                sh 'pytest -m performance'
            }
        }
    }
}
```

## 🔔 通知配置

### 邮件通知

```groovy
post {
    failure {
        emailext(
            subject: "测试失败 - Build #${env.BUILD_NUMBER}",
            body: "详情查看: ${env.BUILD_URL}",
            to: "dev-team@example.com"
        )
    }
}
```

### 钉钉通知

```bash
curl -X POST ${DINGTALK_WEBHOOK} \
-H 'Content-Type: application/json' \
-d '{
    "msgtype": "text",
    "text": {
        "content": "测试构建失败 #${BUILD_NUMBER}"
    }
}'
```

### 企业微信通知

```bash
curl -X POST ${WECHAT_WEBHOOK} \
-H 'Content-Type: application/json' \
-d '{
    "msgtype": "markdown",
    "markdown": {
        "content": "## 测试构建失败\n构建号: ${BUILD_NUMBER}"
    }
}'
```

## 📈 最佳实践

### 1. 测试策略

#### 快速测试（<5分钟）
- 代码提交时触发
- 只运行基础API测试
- 跳过慢速测试

```bash
pytest -m "not slow and not performance and not security"
```

#### 完整测试（<30分钟）
- 每天定时执行
- 运行所有测试
- 生成覆盖率报告

```bash
pytest --cov=. --cov-report=html
```

#### 专项测试（按需）
- 性能测试：每周执行
- 安全测试：发布前执行

### 2. 资源优化

#### 并行执行
```groovy
stage('测试') {
    parallel {
        stage('API测试') {
            steps {
                sh 'pytest api/'
            }
        }
        stage('集成测试') {
            steps {
                sh 'pytest integration/'
            }
        }
    }
}
```

#### 缓存依赖
```groovy
stage('安装依赖') {
    steps {
        cache(path: '.cache/pip', key: "pip-${hashFiles('requirements-test.txt')}") {
            sh 'pip install -r requirements-test.txt'
        }
    }
}
```

### 3. 失败处理

#### 重试机制
```groovy
stage('测试') {
    options {
        retry(2)
    }
    steps {
        sh 'pytest'
    }
}
```

#### 容错处理
```groovy
stage('测试') {
    steps {
        script {
            try {
                sh 'pytest'
            } catch (Exception e) {
                currentBuild.result = 'UNSTABLE'
                echo "测试失败但继续构建: ${e}"
            }
        }
    }
}
```

## 🐛 故障排查

### 常见问题

#### 1. Conda环境问题

**问题**: conda: command not found

**解决**:
```bash
# 检查conda路径
which conda

# 添加到PATH
export PATH=/opt/conda/bin:$PATH

# 或在Jenkinsfile中配置
environment {
    PATH = "/opt/conda/bin:${env.PATH}"
}
```

#### 2. 依赖安装失败

**问题**: pip install失败

**解决**:
```bash
# 使用国内镜像
pip install -r requirements-test.txt \
    -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 测试环境不可访问

**问题**: Connection refused

**解决**:
```bash
# 检查网络
curl -v http://115.190.75.88:8000/health

# 检查Jenkins节点网络配置
# 可能需要配置代理或网络白名单
```

#### 4. 报告发布失败

**问题**: HTML Publisher插件报错

**解决**:
```groovy
// 确保报告目录存在
sh 'mkdir -p reports/html'

// 使用绝对路径
publishHTML([
    reportDir: "${env.WORKSPACE}/backend/tests/reports/html",
    reportFiles: 'report.html',
    reportName: '测试报告'
])
```

## 📚 参考资源

### Jenkins官方文档
- [Pipeline Syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Using Credentials](https://www.jenkins.io/doc/book/using/using-credentials/)
- [HTML Publisher Plugin](https://plugins.jenkins.io/htmlpublisher/)

### 相关文件
- `Jenkinsfile` - Jenkins流水线配置
- `jenkins-setup.sh` - 环境初始化脚本
- `README.md` - 测试框架文档
- `QUICKSTART.md` - 快速开始指南

## 🔐 安全建议

1. **不要在Jenkinsfile中硬编码敏感信息**
   - 使用Jenkins Credentials管理
   - 使用环境变量

2. **限制Jenkins节点权限**
   - 使用专用账号运行Jenkins
   - 最小权限原则

3. **测试数据隔离**
   - 使用独立测试数据库
   - 测试后及时清理

4. **访问控制**
   - 配置Jenkins用户权限
   - 保护测试报告访问

## 📞 支持

如有问题，请查看：
- Jenkins日志: `/var/log/jenkins/jenkins.log`
- 构建日志: Jenkins UI中的Console Output
- 测试日志: `backend/tests/reports/`

---

✅ Jenkins CI/CD集成配置完成！
