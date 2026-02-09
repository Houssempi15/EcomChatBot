# Jenkins CI/CD测试问题排查指南

## 问题现象

1. **测试未执行** - 看不到测试运行的输出
2. **报告路径不正确** - 访问 `http://115.190.75.88:8080/job/EComChatBot/21/覆盖率报告/` 显示错误

---

## 已修复的问题

### 修复1: 测试脚本错误处理

**问题**: 测试脚本使用 `set -e`，遇到任何错误就退出  
**修复**: 移除 `set -e`，改为手动处理错误

### 修复2: 添加详细调试信息

**新增输出**:
- 当前工作目录
- Python版本
- 测试报告文件列表
- 测试退出码

### 修复3: 改进报告发布错误处理

**修复**: 所有 `publishHTML` 和 `junit` 调用都添加 try-catch

---

## 下一次构建的检查清单

### 步骤1: 触发新构建

1. 在Jenkins中点击 **"立即构建"**
2. 等待构建开始

### 步骤2: 查看构建日志

点击构建编号 → **Console Output**，查找以下关键输出：

#### ✅ 测试执行部分

应该看到类似输出：
```
>>> 当前工作目录: /opt/projects/ecom-chat-bot/backend
>>> Python版本: Python 3.x.x
>>> 检查测试脚本...
-rwxr-xr-x 1 jenkins jenkins ... tests/run_ci_tests.sh

>>> 开始执行测试...

╔════════════════════════════════════════════════════════╗
║   电商智能客服SaaS平台 - CI/CD自动化测试               ║
╚════════════════════════════════════════════════════════╝

[INFO] 检查Python环境...
[SUCCESS] Python环境: Python 3.x.x

[INFO] 安装测试依赖...
...

[INFO] 运行测试套件...
...

>>> 测试执行完成，退出码: 0
```

#### ✅ 报告生成部分

应该看到：
```
>>> 检查测试报告...
✓ test-reports 目录存在
test-reports/
  junit-report.xml
  test-report.html
  coverage.xml
  coverage-html/
  test-summary.txt
  ...
```

#### ✅ 报告发布部分

应该看到：
```
=== 当前目录 ===
/opt/projects/ecom-chat-bot/backend

=== test-reports 内容 ===
... test-reports/junit-report.xml
... test-reports/test-report.html
... test-reports/coverage-html/index.html

✓ JUnit报告已发布
✓ HTML测试报告已发布
✓ 覆盖率报告已发布
✓ 测试报告文件已归档
```

---

## 常见问题排查

### 问题1: 测试未执行

**检查点**:
```bash
# 在Jenkins服务器上检查
cd /opt/projects/ecom-chat-bot/backend

# 1. 检查脚本是否存在
ls -la tests/run_ci_tests.sh

# 2. 检查脚本权限
chmod +x tests/run_ci_tests.sh

# 3. 手动运行测试
./tests/run_ci_tests.sh

# 4. 检查Python环境
python3 --version
which python3

# 5. 检查测试依赖
pip3 list | grep -E "pytest|httpx|faker"
```

**可能原因**:
- Python环境未配置
- 测试依赖未安装
- 脚本权限问题
- 路径不正确

### 问题2: 报告路径404

**症状**: 访问 `http://...覆盖率报告/` 显示 "Error: no workspace"

**原因分析**:
1. 报告文件未生成
2. publishHTML 的 reportDir 路径不正确
3. Jenkins工作空间问题

**检查方法**:

1. **确认报告文件存在**:
```bash
cd /opt/projects/ecom-chat-bot/backend
ls -R test-reports/
```

应该看到：
```
test-reports/
  junit-report.xml
  test-report.html
  coverage.xml
  test-summary.txt
  test-summary.json
  
test-reports/coverage-html/:
  index.html
  ... (其他HTML文件)
```

2. **查看Jenkins构建产物**:
   - 构建详情页 → **Build Artifacts**
   - 应该能看到并下载 `test-reports/**/*` 文件

3. **检查publishHTML配置**:
   确保 Jenkinsfile 中的配置正确：
   ```groovy
   publishHTML([
       reportDir: 'test-reports/coverage-html',  // 相对于 DEPLOY_PATH/backend
       reportFiles: 'index.html',
       reportName: '覆盖率报告'
   ])
   ```

### 问题3: 报告发布失败

**检查Jenkins日志**，查找错误信息：

如果看到：
```
⚠ HTML测试报告发布失败: ...
⚠ 覆盖率报告发布失败: ...
```

**可能原因**:
1. 报告文件不存在（allowMissing: false 会报错）
2. reportDir 路径不正确
3. reportFiles 指定的文件不存在

**解决方法**:
1. 确认测试已运行并生成报告
2. 检查路径拼写
3. 查看构建日志中的文件列表

---

## 验证报告是否正确发布

### 方法1: 通过Jenkins界面

构建完成后，在构建详情页左侧菜单应该看到：

- ✅ **Test Result** - JUnit测试结果
- ✅ **测试报告** - HTML测试详情
- ✅ **覆盖率报告** - 代码覆盖率分析
- ✅ **Build Artifacts** - 所有报告文件下载

### 方法2: 直接访问URL

正确的URL格式：
```
# 测试报告
http://115.190.75.88:8080/job/EComChatBot/<构建编号>/测试报告/

# 覆盖率报告
http://115.190.75.88:8080/job/EComChatBot/<构建编号>/覆盖率报告/

# 注意: 如果URL中有中文，浏览器会自动编码
```

### 方法3: 下载构建产物

如果报告链接不工作，可以直接下载：
```
http://115.190.75.88:8080/job/EComChatBot/<构建编号>/artifact/
```

点击进入 `backend/test-reports/` 查看所有报告文件。

---

## 手动测试验证

如果想在构建前验证测试是否能正常运行：

```bash
# 1. SSH登录到Jenkins服务器
ssh user@115.190.75.88

# 2. 切换到项目目录
cd /opt/projects/ecom-chat-bot/backend

# 3. 手动运行测试
./tests/run_ci_tests.sh

# 4. 检查报告是否生成
ls -la test-reports/

# 5. 查看测试摘要
cat test-reports/test-summary.txt
```

---

## 预期的完整构建日志片段

```
[Pipeline] stage
[Pipeline] { (运行自动化测试)
[Pipeline] script
[Pipeline] {
[Pipeline] sh
>>> 当前工作目录: /opt/projects/ecom-chat-bot/backend
>>> Python版本: Python 3.11.x
>>> 检查测试脚本...
-rwxr-xr-x 1 jenkins jenkins 9544 ... tests/run_ci_tests.sh

>>> 开始执行测试...

╔════════════════════════════════════════════════════════╗
║   电商智能客服SaaS平台 - CI/CD自动化测试               ║
╚════════════════════════════════════════════════════════╝

[INFO] 检查Python环境...
[SUCCESS] Python环境: Python 3.11.x

[INFO] 安装测试依赖...
[SUCCESS] 测试依赖安装完成

[INFO] 准备测试报告目录...
[SUCCESS] 报告目录已准备

[INFO] 等待服务就绪...
[SUCCESS] API服务已就绪

========================================
  开始运行测试套件
========================================

[INFO] 执行测试...
tests/test_01_health.py::TestHealthCheckAPIs::test_health_basic PASSED
tests/test_01_health.py::TestHealthCheckAPIs::test_health_live_probe PASSED
... (更多测试输出)

======== 300 passed in 180.00s ========

[SUCCESS] 测试执行完成

========================================
  生成测试报告摘要
========================================

测试结果:
  总测试数: 300
  通过: 298
  失败: 2
  跳过: 0
  代码覆盖率: 91%

[SUCCESS] 测试摘要已生成

>>> 测试执行完成，退出码: 0

>>> 检查测试报告...
✓ test-reports 目录存在
test-reports/:
  junit-report.xml
  test-report.html
  coverage.xml
  coverage-html/
  test-summary.txt
  test-summary.json
  logs/

✓ 测试阶段完成
[Pipeline] }
[Pipeline] // script
[Pipeline] }
[Pipeline] // stage

[Pipeline] stage
[Pipeline] { (Declarative: Post Actions)
[Pipeline] script
[Pipeline] {
>>> 开始归档测试报告...
[Pipeline] dir

=== 当前目录 ===
/opt/projects/ecom-chat-bot/backend

=== test-reports 内容 ===
... junit-report.xml
... test-report.html
... coverage-html/index.html
... (更多文件)

[Pipeline] junit
Recording test results
✓ JUnit报告已发布

[Pipeline] publishHTML
✓ HTML测试报告已发布

[Pipeline] publishHTML
✓ 覆盖率报告已发布

[Pipeline] archiveArtifacts
Archiving artifacts
✓ 测试报告文件已归档

>>> 测试报告归档流程结束
```

---

## 成功标志

构建成功后，您应该能够：

1. ✅ 在Jenkins项目首页看到 **测试趋势图**
2. ✅ 点击构建详情，左侧菜单有 **"测试报告"** 和 **"覆盖率报告"** 链接
3. ✅ 点击链接能正常打开HTML报告
4. ✅ 在 **Build Artifacts** 中能下载所有测试报告
5. ✅ 测试结果显示在构建历史中（通过/失败数量）

---

## 需要帮助？

如果构建后仍有问题，请提供：

1. **完整的构建日志**（Console Output）
2. **测试阶段的输出**
3. **报告发布部分的输出**
4. **报告链接和错误截图**

这样可以更快定位问题！

---

**更新日期**: 2026-02-09  
**版本**: v1.1
