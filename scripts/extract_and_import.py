#!/usr/bin/env python3
"""
从SQL dump中提取数据并导入
"""
import subprocess
import os

# 提取health_metric的数据
print("正在提取health_metric表的数据...")

# 使用sed提取COPY数据部分
cmd = """
sed -n '/^COPY public.health_metric/,/^\\\\\\./p' /Users/longevitygo/Documents/avinasi/lsp_system/sponge_no_perms.sql > /tmp/health_metric_data.sql
"""
subprocess.run(cmd, shell=True)

# 检查提取的数据
result = subprocess.run("wc -l /tmp/health_metric_data.sql", shell=True, capture_output=True, text=True)
print(f"提取了 {result.stdout.strip()} 的数据")

# 导入数据
print("\n正在导入数据到PostgreSQL...")
cmd = 'PGPASSWORD="Sponge_2025" psql -U postgres -h localhost -d sponge < /tmp/health_metric_data.sql'
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

if result.returncode == 0:
    print("✅ 数据导入成功!")
else:
    print(f"❌ 导入失败: {result.stderr}")
    # 尝试查看错误详情
    print("\n尝试查看最后几行数据...")
    subprocess.run("tail -n 5 /tmp/health_metric_data.sql", shell=True)

# 清理临时文件
# os.remove("/tmp/health_metric_data.sql")

# 验证导入结果
print("\n验证导入结果...")
cmd = """PGPASSWORD="Sponge_2025" psql -U postgres -h localhost -d sponge -c "SELECT COUNT(*) as count FROM health_metric;" """
subprocess.run(cmd, shell=True)
