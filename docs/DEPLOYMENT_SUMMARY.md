# 域名部署实施总结

## 已完成的配置

### 1. Nginx HTTPS 配置
✅ 创建 `nginx/conf.d/ecomchat.conf`
- HTTP → HTTPS 自动重定向
- SSL/TLS 安全配置（TLS 1.2/1.3）
- 安全头部（HSTS、X-Frame-Options 等）
- API 代理配置
- WebSocket 支持
- 静态资源缓存优化

### 2. Nginx 主配置更新
✅ 修改 `nginx/nginx.conf`
- 移除内联的 server 块
- 保留 upstream 定义
- 通过 conf.d/*.conf 加载具体配置

### 3. Docker Compose 配置
✅ 修改 `docker-compose.yml`
- 添加 nginx 服务（监听 80/443 端口）
- 移除 frontend 的端口暴露（改为内网访问）
- 移除 api 的端口暴露（改为内网访问）
- 挂载 SSL 证书目录
- 添加 nginx_logs volume

### 4. 前端环境配置
✅ 修改 `frontend/.env.production`
- 更新 WebSocket URL 为 wss://ecomchat.cn/api/v1/ws

### 5. 部署脚本
✅ 创建 `scripts/get-ssl-cert.sh`
- 自动安装 certbot
- 获取 Let's Encrypt SSL 证书
- 支持交互式输入邮箱

✅ 创建 `scripts/deploy-domain.sh`
- 检查 SSL 证书
- 构建并启动服务
- 自动验证部署状态
- 测试 HTTP/HTTPS 访问

### 6. 文档
✅ 创建 `docs/DEPLOYMENT.md`
- 完整的部署步骤说明
- DNS 配置指南
- SSL 证书获取流程
- 故障排查指南
- 安全检查清单

✅ 创建 `docs/DEPLOYMENT_QUICK_REF.md`
- 常用命令快速参考
- 服务管理命令
- SSL 证书管理
- 故障排查命令

✅ 更新 `README.md`
- 添加域名部署章节
- 添加文档链接

## 需要手动配置的内容

### ⚠️ 重要：backend/.env 配置

由于 `backend/.env` 不在 git 版本控制中，需要手动修改以下配置：

```bash
# 1. 修改环境为生产环境
DEBUG=false
ENVIRONMENT=production

# 2. 更新 CORS 配置
CORS_ORIGINS=["https://ecomchat.cn","https://www.ecomchat.cn"]

# 3. 更新支付回调 URL
ALIPAY_RETURN_URL=https://ecomchat.cn/payment/alipay/return
ALIPAY_NOTIFY_URL=https://ecomchat.cn/api/v1/payment/callback/alipay/notify

# 4. 更新邮件发送地址
SMTP_FROM=noreply@ecomchat.cn
```

**操作命令：**
```bash
# 编辑 backend/.env 文件
vim backend/.env

# 或使用 sed 批量替换
sed -i 's/DEBUG=true/DEBUG=false/' backend/.env
sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' backend/.env
sed -i 's|CORS_ORIGINS=\["http://localhost:3000","http://localhost:8000"\]|CORS_ORIGINS=["https://ecomchat.cn","https://www.ecomchat.cn"]|' backend/.env
sed -i 's|http://localhost:8000/payment/alipay/return|https://ecomchat.cn/payment/alipay/return|' backend/.env
sed -i 's|http://localhost:8000/api/v1/payment/callback/alipay/notify|https://ecomchat.cn/api/v1/payment/callback/alipay/notify|' backend/.env
sed -i 's/noreply@example.com/noreply@ecomchat.cn/' backend/.env
```

## 部署前检查清单

### 服务器环境
- [ ] 域名 ecomchat.cn 已完成 ICP 备案
- [ ] DNS 记录已配置（A 记录指向服务器 IP）
- [ ] 服务器已安装 Docker 和 Docker Compose
- [ ] 防火墙已开放 80 和 443 端口

### 配置文件
- [ ] `backend/.env` 已更新为生产环境配置
- [ ] `nginx/conf.d/ecomchat.conf` 已创建
- [ ] `docker-compose.yml` 已更新
- [ ] `frontend/.env.production` 已更新

### SSL 证书
- [ ] 已安装 certbot
- [ ] 已获取 SSL 证书（/etc/letsencrypt/live/ecomchat.cn/）
- [ ] 证书有效期充足（> 30 天）

## 部署步骤

### 在服务器上执行

```bash
# 1. 进入项目目录
cd /path/to/ecom-chat-bot

# 2. 拉取最新代码
git pull origin master

# 3. 手动更新 backend/.env（见上文）
vim backend/.env

# 4. 获取 SSL 证书（首次部署）
sudo ./scripts/get-ssl-cert.sh

# 5. 部署应用
sudo ./scripts/deploy-domain.sh

# 6. 验证部署
curl -I https://ecomchat.cn
curl https://ecomchat.cn/health
```

## 验证清单

### 功能验证
- [ ] http://ecomchat.cn 自动重定向到 https://ecomchat.cn
- [ ] https://ecomchat.cn 前端页面正常加载
- [ ] https://ecomchat.cn/docs API 文档正常访问
- [ ] https://ecomchat.cn/health 健康检查返回 200
- [ ] WebSocket 连接正常（浏览器控制台无错误）
- [ ] 文件上传功能正常
- [ ] API 请求正常（检查 Network 面板）

### 安全验证
- [ ] SSL Labs 测试评分 A 或 A+（https://www.ssllabs.com/ssltest/）
- [ ] 安全头部正确设置（https://securityheaders.com/）
- [ ] HSTS 头部存在
- [ ] 证书链完整

### 性能验证
- [ ] 静态资源缓存生效（Cache-Control 头部）
- [ ] Gzip 压缩启用
- [ ] HTTP/2 启用
- [ ] 页面加载时间 < 3 秒

## 后续维护

### SSL 证书自动续期

```bash
# 添加 crontab 任务
sudo crontab -e

# 添加以下行
0 2 * * * certbot renew --quiet --deploy-hook "cd /path/to/ecom-chat-bot && docker compose restart nginx"
```

### 监控建议
1. 配置证书过期监控（提前 30 天告警）
2. 配置服务健康检查监控
3. 配置日志分析和告警
4. 定期检查安全更新

## 回滚方案

如果部署出现问题：

```bash
# 1. 停止 nginx
docker compose stop nginx

# 2. 恢复 frontend 直接暴露（编辑 docker-compose.yml）
# 在 frontend 服务中添加:
#   ports:
#     - "80:3000"

# 3. 重启 frontend
docker compose up -d frontend

# 4. 临时使用 HTTP 访问
# http://服务器IP
```

## 文件清单

### 新增文件
- `nginx/conf.d/ecomchat.conf` - HTTPS 配置
- `scripts/get-ssl-cert.sh` - SSL 证书获取脚本
- `scripts/deploy-domain.sh` - 部署脚本
- `docs/DEPLOYMENT.md` - 部署指南
- `docs/DEPLOYMENT_QUICK_REF.md` - 快速参考
- `docs/DEPLOYMENT_SUMMARY.md` - 本文件

### 修改文件
- `docker-compose.yml` - 添加 nginx 服务，调整端口
- `nginx/nginx.conf` - 移除 server 块
- `frontend/.env.production` - 更新 WebSocket URL
- `README.md` - 添加域名部署章节
- `backend/.env` - 需手动更新（不在 git 中）

## 技术支持

如遇到问题，请检查：
1. 日志：`docker compose logs nginx api frontend`
2. 容器状态：`docker compose ps`
3. Nginx 配置：`docker compose exec nginx nginx -t`
4. SSL 证书：`sudo certbot certificates`
5. DNS 解析：`nslookup ecomchat.cn`

详细文档：
- [完整部署指南](./DEPLOYMENT.md)
- [快速参考](./DEPLOYMENT_QUICK_REF.md)
