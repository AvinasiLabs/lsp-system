# 修复数据库连接错误

## 问题描述
"Failed to get a connection from the pool" 表示数据库连接池无法获取连接，可能的原因：
1. 数据库服务未启动
2. 数据库配置错误
3. Docker网络问题

## 快速诊断

### 1. 检查容器状态
```bash
docker-compose ps
```

### 2. 检查数据库连接
```bash
# 进入API容器
docker-compose exec api bash

# 在容器内测试数据库连接
python -c "
import psycopg2
import os

try:
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    print('✅ 数据库连接成功')
    conn.close()
except Exception as e:
    print(f'❌ 数据库连接失败: {e}')
"
```

### 3. 检查环境变量
```bash
# 在容器内
env | grep DB_
```

## 解决方案

### 方案1：使用docker-compose网络
确保 `.env` 文件中的数据库配置正确：
```bash
# 如果使用docker-compose，DB_HOST应该是服务名
DB_HOST=db  # 不是localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

### 方案2：重启所有服务
```bash
# 停止所有服务
docker-compose down

# 清理并重启
docker-compose up -d --force-recreate
```

### 方案3：检查数据库服务
```bash
# 查看数据库日志
docker-compose logs db

# 确保数据库正在运行
docker-compose ps db
```

### 方案4：如果使用外部数据库
确保：
1. 数据库可以从Docker容器访问
2. 防火墙允许连接
3. 数据库用户有正确的权限

## 临时解决方案

如果急需使用，可以修改代码返回友好错误：

在 `src/api/score_api.py` 中的错误处理部分添加数据库连接检查。