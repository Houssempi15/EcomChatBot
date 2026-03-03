# 域名部署检查清单

使用本清单确保域名部署的每个步骤都正确完成。

## 📋 部署前准备

### 域名和服务器
- [ ] 域名 ecomchat.cn 已申请并完成 ICP 备案
- [ ] 服务器已准备就绪（推荐 2 核 4GB 以上）
- [ ] 服务器已安装 Docker（版本 20.10+）
- [ ] 服务器已安装 Docker Compose（版本 2.0+）
- [ ] 服务器公网 IP 已知：________________

### DNS 配置
- [ ] 已在域名服务商处添加 A 记录：@ → 服务器 IP
- [ ] 已在域名服务商处添加 A 记录：www → 服务器 IP
- [ ] DNS 记录已生效（使用 `nslookup ecomchat.cn` 验证）

### 防火墙配置
- [ ] 已开放 80 端口（HTTP）
- [ ] 已开放 443 端口（HTTPS）
- [ ] 已验证端口开放：`sudo ufw status` 或 `sudo firewall-cmd --list-all`

## 📦 代码和配置

### 代码部署
- [ ] 已将代码上传到服务器
- [ ] 代码位置：________________
- [ ] 已切换到正确的分支（master 或 main）

### 配置文件检查
- [ ] `nginx/conf.d/ecomchat.conf` 已存在
- [ ] `docker-compose.yml` 包含 nginx 服务
- [ ] `frontend/.env.production` WebSocket URL 正确
- [ ] `backend/.env` 已手动更新为生产环境配置：
  - [ ] DEBUG=false
  - [ ] ENVIRONMENT=production
  - [ ] CORS_ORIGINS 包含 https://ecomchat.cn
  - [ ] ALIPAY_RETURN_URL 使用 https://ecomchat.cn
  - [ ] ALIPAY_NOTIFY_URL 使用 https://ecomchat.cn
  - [ ] SMTP_FROM=noreply@ecomchat.cn

## 🔐 SSL 证书

### 证书获取
- [ ] 已安装 certbot：`certbot --version`
- [ ] 已停止占用 80 端口的服务
- [ ] 已运行：`sudo ./scripts/get-ssl-cert.sh`
- [ ] 证书获取成功
- [ ] 证书文件存在：`ls -la /etc/letsencrypt/live/ecomchat.cn/`
- [ ] 证书有效期充足（> 30 天）

## 🚀 部署执行

### 构建和启动
- [ ] 已运行：`sudo ./scripts/deploy-domain.sh`
- [ ] 所有容器启动成功：`docker compose ps`
- [ ] 没有容器处于 Exited 状态

### 容器状态检查
- [ ] ecom-chatbot-nginx 运行中
- [ ] ecom-chatbot-api 运行中
- [ ] ecom-chatbot-frontend 运行中
- [ ] ecom-chatbot-postgres 运行中
- [ ] ecom-chatbot-redis 运行中
- [ ] ecom-chatbot-celery-worker 运行中

## ✅ 功能验证

### HTTP/HTTPS 访问
- [ ] HTTP 自动重定向：`curl -I http://ecomchat.cn` 返回 301
- [ ] HTTPS 访问正常：`curl -I https://ecomchat.cn` 返回 200
- [ ] www 子域名正常：`curl -I https://www.ecomchat.cn` 返回 200

### 页面和 API
- [ ] 前端页面加载：浏览器访问 https://ecomchat.cn
- [ ] API 文档访问：https://ecomchat.cn/docs
- [ ] 健康检查：`curl https://ecomchat.cn/health` 返回 OK
- [ ] API 请求正常（浏览器 Network 面板无错误）

### WebSocket
- [ ] WebSocket 连接成功（浏览器控制台无 WebSocket 错误）
- [ ] 实时对话功能正常

### 文件上传
- [ ] 文件上传功能正常
- [ ] 上传的文件可以访问

## 🔒 安全检查

### SSL/TLS
- [ ] SSL Labs 测试：https://www.ssllabs.com/ssltest/analyze.html?d=ecomchat.cn
  - [ ] 评分 A 或 A+
- [ ] 证书链完整
- [ ] 支持 TLS 1.2 和 TLS 1.3
- [ ] 不支持弱加密套件

### 安全头部
- [ ] Security Headers 测试：https://securityheaders.com/?q=ecomchat.cn
- [ ] HSTS 头部存在
- [ ] X-Frame-Options 头部存在
- [ ] X-Content-Type-Options 头部存在
- [ ] X-XSS-Protection 头部存在

### 其他安全
- [ ] 不暴露服务器版本信息
- [ ] 不暴露内部路径
- [ ] 错误页面不泄露敏感信息

## 📊 性能检查

### 缓存和压缩
- [ ] Gzip 压缩启用（检查 Response Headers）
- [ ] 静态资源缓存生效（Cache-Control 头部）
- [ ] HTTP/2 启用

### 加载性能
- [ ] 首页加载时间 < 3 秒
- [ ] API 响应时间 < 500ms
- [ ] 静态资源加载快速

## 🔧 后续配置

### SSL 证书自动续期
- [ ] 已配置 crontab 自动续期
- [ ] 测试续期命令：`sudo certbot renew --dry-run`

### 监控和告警
- [ ] 配置证书过期监控（可选）
- [ ] 配置服务健康检查监控（可选）
- [ ] 配置日志分析（可选）

### 备份
- [ ] 数据库备份策略已制定
- [ ] 配置文件已备份
- [ ] SSL 证书已备份

## 📝 文档和记录

### 部署记录
- [ ] 部署日期：________________
- [ ] 部署人员：________________
- [ ] 服务器 IP：________________
- [ ] SSL 证书过期日期：________________

### 访问信息
- [ ] 前端地址：https://ecomchat.cn
- [ ] API 文档：https://ecomchat.cn/docs
- [ ] 健康检查：https://ecomchat.cn/health

### 问题记录
如果遇到问题，记录在此：

```
问题描述：


解决方案：


```

## 🎉 部署完成

- [ ] 所有检查项已完成
- [ ] 系统运行正常
- [ ] 已通知相关人员

---

**参考文档：**
- 完整部署指南：[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 快速参考：[docs/DEPLOYMENT_QUICK_REF.md](docs/DEPLOYMENT_QUICK_REF.md)
- 实施总结：[docs/DEPLOYMENT_SUMMARY.md](docs/DEPLOYMENT_SUMMARY.md)

**常用命令：**
```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f nginx
docker compose logs -f api

# 重启服务
docker compose restart nginx

# 查看证书
sudo certbot certificates
```
