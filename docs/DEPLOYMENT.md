# 域名部署指南 - ecomchat.cn

本文档提供将项目部署到 ecomchat.cn 域名的完整步骤。

## 前置条件

- 域名 ecomchat.cn 已完成 ICP 备案
- 服务器已安装 Docker 和 Docker Compose
- 服务器防火墙已开放 80 和 443 端口

## 部署步骤

### 1. 配置 DNS 记录

在域名服务商处添加以下 DNS 记录：

```
类型    主机记录    记录值
A       @          服务器公网IP
A       www        服务器公网IP
```

等待 DNS 记录生效（通常需要几分钟到几小时）。

### 2. 获取 SSL 证书

在服务器上执行以下命令获取 Let's Encrypt 免费 SSL 证书：

```bash
# 1. 安装 Certbot
sudo apt-get update
sudo apt-get install certbot

# 2. 停止占用 80 端口的服务（如果有）
cd /path/to/ecom-chat-bot
docker compose down

# 3. 获取证书（替换邮箱地址）
sudo certbot certonly --standalone \
  -d ecomchat.cn \
  -d www.ecomchat.cn \
  --email your-email@example.com \
  --agree-tos

# 4. 验证证书文件
sudo ls -la /etc/letsencrypt/live/ecomchat.cn/
# 应该看到 fullchain.pem 和 privkey.pem
```

### 3. 配置防火墙

确保服务器防火墙开放必要端口：

```bash
# Ubuntu/Debian
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status

# CentOS/RHEL
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 4. 部署应用

```bash
# 1. 进入项目目录
cd /path/to/ecom-chat-bot

# 2. 拉取最新代码
git pull origin master

# 3. 构建并启动服务
docker compose build
docker compose up -d

# 4. 查看服务状态
docker compose ps

# 5. 查看日志
docker compose logs -f nginx
docker compose logs -f api
docker compose logs -f frontend
```

### 5. 验证部署

访问以下 URL 验证部署是否成功：

- http://ecomchat.cn → 应该自动重定向到 https://ecomchat.cn
- https://ecomchat.cn → 前端页面正常加载
- https://ecomchat.cn/docs → API 文档正常访问
- https://ecomchat.cn/health → 返回健康检查状态

### 6. 配置 SSL 证书自动续期

Let's Encrypt 证书有效期 90 天，需要配置自动续期：

```bash
# 编辑 crontab
sudo crontab -e

# 添加以下行（每天凌晨 2 点检查并续期）
0 2 * * * certbot renew --quiet --deploy-hook "cd /path/to/ecom-chat-bot && docker compose restart nginx"
```

## 故障排查

### 问题 1: 无法访问网站

检查项：
- DNS 记录是否生效：`nslookup ecomchat.cn`
- 防火墙是否开放端口：`sudo ufw status`
- Nginx 容器是否运行：`docker compose ps nginx`
- Nginx 日志：`docker compose logs nginx`

### 问题 2: SSL 证书错误

检查项：
- 证书文件是否存在：`sudo ls -la /etc/letsencrypt/live/ecomchat.cn/`
- 证书是否过期：`sudo certbot certificates`
- Nginx 配置是否正确：`docker compose exec nginx nginx -t`

### 问题 3: API 请求失败

检查项：
- 后端容器是否运行：`docker compose ps api`
- 后端日志：`docker compose logs api`
- CORS 配置是否正确：检查 backend/.env 中的 CORS_ORIGINS

### 问题 4: WebSocket 连接失败

检查项：
- 前端 WebSocket URL 配置：frontend/.env.production
- Nginx WebSocket 代理配置：nginx/conf.d/ecomchat.conf
- 浏览器控制台错误信息

## 回滚方案

如果部署出现问题，可以快速回滚：

```bash
# 1. 停止 nginx 服务
docker compose stop nginx

# 2. 临时恢复前端直接暴露（修改 docker-compose.yml）
# 在 frontend 服务中添加：
#   ports:
#     - "80:3000"

# 3. 重启前端
docker compose up -d frontend

# 4. 临时使用 HTTP 访问
# 访问 http://服务器IP
```

## 性能优化建议

1. **启用 CDN**：接入阿里云 CDN 或腾讯云 CDN 加速静态资源
2. **配置监控**：使用 Prometheus + Grafana 监控服务状态
3. **日志分析**：使用 ELK 或 Loki 分析访问日志
4. **负载���衡**：流量增大时部署多个后端实例

## 安全检查清单

- [ ] SSL 证书有效且评分 A+（https://www.ssllabs.com/ssltest/）
- [ ] 安全头部正确配置（https://securityheaders.com/）
- [ ] HSTS 头部已启用
- [ ] 不暴露敏感信息（版本号、内部路径）
- [ ] 定期更新 Docker 镜像和系统包
- [ ] 配置证书过期监控告警

## 相关文件

- `nginx/conf.d/ecomchat.conf` - HTTPS 配置
- `nginx/nginx.conf` - Nginx 主配置
- `docker-compose.yml` - 服务编排配置
- `backend/.env` - 后端环境变量
- `frontend/.env.production` - 前端生产环境变量

