# LSP积分系统 Docker部署方案

## 概述

本文档详细介绍LSP积分系统的Docker容器化部署方案，包括开发环境和生产环境的部署步骤。

## 系统架构

```
┌─────────────────┐
│   Nginx/反向代理  │ (可选)
└────────┬────────┘
         │
┌────────▼────────┐
│   LSP API容器    │
│  (FastAPI应用)   │
└────────┬────────┘
         │
┌────────▼────────┐
│  PostgreSQL数据库 │ (外部)
└─────────────────┘
```

## 前置要求

1. **Docker环境**
   - Docker Engine 20.10+
   - Docker Compose 2.0+

2. **数据库**
   - PostgreSQL 15+ (外部数据库)
   - 已创建数据库和用户
   - 网络可访问

3. **系统资源**
   - 最小：1 CPU, 512MB RAM
   - 推荐：2 CPU, 1GB RAM

## 文件结构

```
lsp_system/
├── Dockerfile                 # 应用镜像定义
├── docker-compose.yml        # 开发环境编排
├── docker-compose.prod.yml   # 生产环境编排
├── .dockerignore            # Docker构建忽略文件
├── .env.example             # 环境变量示例
├── build.sh                 # 构建脚本
├── deploy.sh                # 部署脚本
└── scripts/
    ├── create_lsp_tables.sql    # 数据库初始化SQL
    └── init_lsp_tables.py       # 数据库初始化脚本
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd lsp_system

# 复制环境变量配置
cp .env.example .env

# 编辑环境变量
vim .env
```

### 2. 数据库初始化

首次部署需要初始化数据库表：

```bash
# 方式1：使用Python脚本
python scripts/init_lsp_tables.py

# 方式2：直接执行SQL
psql -h <db-host> -U postgres -d sponge -f scripts/create_lsp_tables.sql
```

### 3. 构建和运行

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/lsp/health

# API文档
open http://localhost:8000/lsp/docs
```

## 生产环境部署

### 1. 准备生产配置

创建生产环境配置文件：

```bash
# 创建生产环境变量文件
cp .env.example .env.prod

# 编辑生产配置
vim .env.prod
```

生产环境建议配置：

```env
# 数据库配置（连接生产数据库）
POSTGRES_HOST=your-prod-db.example.com
POSTGRES_PORT=5432
POSTGRES_DBNAME=lsp_prod
POSTGRES_USER=lsp_user
POSTGRES_PWD=strong-password-here

# API配置
AUTH_ENABLED=true
JWT_SECRET_KEY=your-production-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 其他生产配置
LOG_LEVEL=INFO
```

### 2. 使用部署脚本

```bash
# 一键部署
./deploy.sh

# 或手动执行
docker build -t lsp-system:latest .
docker-compose -f docker-compose.prod.yml up -d
```

### 3. 配置反向代理

Nginx配置示例：

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    # SSL证书配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # 反向代理配置
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API文档访问控制
    location /lsp/docs {
        allow 10.0.0.0/8;  # 内网访问
        deny all;
        proxy_pass http://localhost:8000/lsp/docs;
    }
}
```

## 环境变量说明

| 变量名 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| POSTGRES_HOST | 数据库主机 | 127.0.0.1 | db.example.com |
| POSTGRES_PORT | 数据库端口 | 5432 | 5432 |
| POSTGRES_DBNAME | 数据库名 | sponge | lsp_prod |
| POSTGRES_USER | 数据库用户 | postgres | lsp_user |
| POSTGRES_PWD | 数据库密码 | - | StrongPassword123 |
| AUTH_ENABLED | 启用认证 | false | true |
| JWT_SECRET_KEY | JWT密钥 | - | random-secret-key |
| JWT_ALGORITHM | JWT算法 | HS256 | HS256 |
| JWT_EXPIRE_MINUTES | JWT过期时间 | 30 | 60 |

## 监控和维护

### 1. 日志管理

```bash
# 查看实时日志
docker logs -f lsp_app

# 查看最近100行日志
docker logs --tail=100 lsp_app

# 导出日志
docker logs lsp_app > app.log
```

### 2. 健康检查

```bash
# 容器健康状态
docker ps | grep lsp_app

# API健康检查
curl http://localhost:8000/lsp/health

# 数据库连接测试
docker exec lsp_app python -c "from src.db.postgresql import POSTGRES_POOL; print('DB OK')"
```

### 3. 性能监控

```bash
# 容器资源使用
docker stats lsp_app

# 进入容器调试
docker exec -it lsp_app bash
```

### 4. 备份建议

虽然应用本身是无状态的，但建议：

1. **配置备份**
   ```bash
   # 备份环境配置
   cp .env.prod .env.prod.backup.$(date +%Y%m%d)
   ```

2. **日志归档**
   ```bash
   # 定期归档日志
   docker logs lsp_app > logs/app-$(date +%Y%m%d).log
   ```

## 更新部署

### 1. 零停机更新

```bash
# 拉取最新代码
git pull origin main

# 构建新镜像
docker build -t lsp-system:new .

# 启动新容器
docker run -d --name lsp_app_new --env-file .env.prod lsp-system:new

# 切换流量（通过负载均衡器）
# ...

# 停止旧容器
docker stop lsp_app && docker rm lsp_app

# 重命名新容器
docker rename lsp_app_new lsp_app
```

### 2. 使用Docker Compose更新

```bash
# 拉取最新代码
git pull origin main

# 重新构建并更新
docker-compose -f docker-compose.prod.yml up -d --build
```

## 故障排查

### 1. 容器无法启动

```bash
# 检查容器日志
docker logs lsp_app

# 常见问题：
# - 端口被占用：修改端口映射
# - 环境变量缺失：检查.env文件
# - 依赖安装失败：检查requirements.txt
```

### 2. 数据库连接失败

```bash
# 测试数据库连接
docker exec lsp_app python -c "
import psycopg2
from src.db.configs.global_config import POSTGRES_CONFIG
conn = psycopg2.connect(
    host=POSTGRES_CONFIG.host,
    port=POSTGRES_CONFIG.port,
    dbname=POSTGRES_CONFIG.dbname,
    user=POSTGRES_CONFIG.user,
    password=POSTGRES_CONFIG.pwd.get_secret_value()
)
print('Connection successful')
"

# 检查事项：
# - 数据库主机可达性
# - 防火墙规则
# - 数据库用户权限
# - 密码是否正确
```

### 3. API响应慢

```bash
# 检查容器资源
docker stats lsp_app

# 检查数据库查询
# 进入容器查看慢查询日志

# 可能的优化：
# - 增加容器资源限制
# - 优化数据库索引
# - 添加缓存层（Redis）
```

## 安全建议

1. **使用非root用户运行**
   ```dockerfile
   # 在Dockerfile中添加
   RUN useradd -m -u 1000 appuser
   USER appuser
   ```

2. **限制容器权限**
   ```yaml
   # 在docker-compose中添加
   security_opt:
     - no-new-privileges:true
   read_only: true
   ```

3. **定期更新基础镜像**
   ```bash
   # 扫描镜像漏洞
   docker scan lsp-system:latest
   ```

4. **使用Docker secrets管理敏感信息**
   ```bash
   # 创建secret
   echo "your-password" | docker secret create db_password -
   ```

## 扩展部署

### 1. 使用Docker Swarm

```bash
# 初始化Swarm
docker swarm init

# 部署服务
docker stack deploy -c docker-compose.prod.yml lsp_stack

# 扩展服务
docker service scale lsp_stack_app=3
```

### 2. 使用Kubernetes

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lsp-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lsp-api
  template:
    metadata:
      labels:
        app: lsp-api
    spec:
      containers:
      - name: lsp-api
        image: lsp-system:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: lsp-config
        - secretRef:
            name: lsp-secrets
```

## 总结

本部署方案提供了从开发到生产的完整Docker容器化部署流程。主要特点：

1. **简单易用**：一键构建和部署
2. **环境隔离**：开发和生产环境分离
3. **易于扩展**：支持水平扩展
4. **安全可靠**：包含安全最佳实践
5. **便于维护**：完善的监控和日志

通过Docker部署，可以确保应用在不同环境中的一致性，简化部署流程，提高运维效率。