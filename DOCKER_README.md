# Docker部署指南

## 快速开始

### 1. 准备环境变量

复制环境变量示例文件并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置你的数据库连接信息：

```env
POSTGRES_HOST=your-database-host
POSTGRES_PWD=your-database-password
```

### 2. 构建和运行

使用docker-compose启动服务：

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 3. 验证部署

检查服务健康状态：

```bash
curl http://localhost:8000/health
```

访问API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 生产环境部署

### 1. 准备生产环境配置

```bash
cp .env.example .env.prod
# 编辑 .env.prod，配置生产环境数据库等信息
```

### 2. 使用生产部署脚本

```bash
# 一键部署
./deploy.sh

# 或手动步骤：
# 构建镜像
./build.sh

# 使用生产配置启动
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 生产环境建议

1. **使用环境变量或Docker secrets管理敏感信息**
   ```bash
   # 创建Docker secret
   echo "your-password" | docker secret create postgres_pwd -
   ```

2. **配置反向代理（Nginx示例）**
   ```nginx
   server {
       listen 80;
       server_name api.yourdomain.com;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }
   ```

3. **启用HTTPS**
   - 使用Let's Encrypt获取SSL证书
   - 在Nginx中配置SSL

4. **监控和日志**
   - 日志文件映射到 `/var/log/lsp` 目录
   - 可以集成Prometheus、Grafana等监控工具

## 常用Docker命令

```bash
# 查看运行中的容器
docker ps

# 查看容器日志
docker logs lsp_app -f

# 进入容器调试
docker exec -it lsp_app bash

# 重启容器
docker-compose restart

# 查看容器资源使用
docker stats lsp_app

# 清理未使用的镜像
docker image prune -a
```

## 故障排查

### 1. 容器无法启动

检查日志：
```bash
docker-compose logs app
```

常见问题：
- 端口被占用：修改docker-compose.yml中的端口映射
- 环境变量缺失：检查.env文件

### 2. 数据库连接失败

- 确认数据库主机地址可达
- 检查防火墙规则
- 验证数据库凭据

### 3. 健康检查失败

```bash
# 进入容器测试连接
docker exec -it lsp_app bash
python -c "from src.db.postgresql import POSTGRES_POOL; print(POSTGRES_POOL)"
```

## 更新部署

1. 拉取最新代码
2. 重新构建镜像：`./build.sh`
3. 重新部署：`./deploy.sh`

## 备份建议

虽然应用本身是无状态的，但建议：

1. 定期备份生产环境配置文件（.env.prod）
2. 如果有本地日志，定期归档
3. 监控磁盘空间使用

## 性能优化

1. **资源限制**已在docker-compose.prod.yml中配置
2. **多实例部署**：可以使用Docker Swarm或Kubernetes
3. **缓存层**：可以添加Redis提升性能

## 安全建议

1. 定期更新基础镜像
2. 扫描镜像漏洞：`docker scan lsp-system:latest`
3. 使用非root用户运行（可在Dockerfile中添加）
4. 限制容器网络访问