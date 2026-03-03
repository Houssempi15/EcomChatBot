# 域名部署快速参考

## 一键部署命令

### 首次部署

```bash
# 1. 获取 SSL 证书
sudo ./scripts/get-ssl-cert.sh

# 2. 部署应用
sudo ./scripts/deploy-domain.sh
```

### 更新部署

```bash
# 拉取最新代码并重新部署
git pull origin master
sudo ./scripts/deploy-domain.sh
```

## 常用命令

### 服务管理

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f nginx
docker compose logs -f api
docker compose logs -f frontend

# 重启服务
docker compose restart nginx
docker compose restart api
docker compose restart frontend

# 停止服务
docker compose down

# 启动服务
docker compose up -d
```

### SSL 证书管理

```bash
# 查看证书信息
sudo certbot certificates

# 手动续期证书
sudo certbot renew

# 测试续期（不实际续期）
sudo certbot renew --dry-run

# 续期后重启 Nginx
sudo certbot renew --deploy-hook "cd /path/to/ecom-chat-bot && docker compose restart nginx"
```

### 故障排查

```bash
# 测试 Nginx 配置
docker compose exec nginx nginx -t

# 重新加载 Nginx 配置
docker compose exec nginx nginx -s reload

# 查看 Nginx 错误日志
docker compose logs nginx | grep error

# 查看后端错误日志
docker compose logs api | grep ERROR

# 测试 HTTP 重定向
curl -I http://ecomchat.cn

# 测试 HTTPS 访问
curl -I https://ecomchat.cn

# 测试健康检查
curl https://ecomchat.cn/health

# 测试 API
curl https://ecomchat.cn/api/v1/health
```

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看 Nginx 访问日志
docker compose logs nginx | grep "GET\|POST"

# 实时查看访问日志
docker compose logs -f nginx | grep "GET\|POST"
```

## 访问地址

- 前端: https://ecomchat.cn
- API 文档: https://ecomchat.cn/docs
- 健康检查: https://ecomchat.cn/health

## 配置文件位置

- Nginx 主配置: `nginx/nginx.conf`
- Nginx HTTPS 配置: `nginx/conf.d/ecomchat.conf`
- Docker Compose: `docker-compose.yml`
- 后端环境变量: `backend/.env`
- 前端环境变量: `frontend/.env.production`

## 证书文件位置

- 完整证书链: `/etc/letsencrypt/live/ecomchat.cn/fullchain.pem`
- 私钥: `/etc/letsencrypt/live/ecomchat.cn/privkey.pem`
- 证书有效期: 90 天
- 自动续期: 每天凌晨 2 点检查

## 端口说明

- 80: HTTP（自动重定向到 HTTPS）
- 443: HTTPS
- 内部端口（不对外暴露）:
  - 3000: Frontend (Next.js)
  - 8000: Backend (FastAPI)
  - 5432: PostgreSQL
  - 6379: Redis

## 安全检查

```bash
# SSL 评分测试
# 访问: https://www.ssllabs.com/ssltest/analyze.html?d=ecomchat.cn

# 安全头部检查
# 访问: https://securityheaders.com/?q=ecomchat.cn

# 检查证书过期时间
sudo certbot certificates | grep "Expiry Date"
```

## 回滚方案

如果部署出现问题：

```bash
# 1. 停止 nginx
docker compose stop nginx

# 2. 临时恢复前端直接暴露（编辑 docker-compose.yml）
# 在 frontend 服务中添加:
#   ports:
#     - "80:3000"

# 3. 重启前端
docker compose up -d frontend

# 4. 使用 HTTP 访问
# http://服务器IP
```

## 紧急联系

如遇到无法解决的问题，请检查：

1. DNS 记录是否正确
2. 防火墙是否开放 80/443 端口
3. SSL 证书是否有效
4. Docker 容器是否正常运行
5. 日志中的错误信息
