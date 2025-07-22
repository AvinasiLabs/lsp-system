#!/usr/bin/env python3
"""
全面测试所有API接口
"""
import requests
import json
from datetime import datetime, date

BASE_URL = "http://localhost:8000/lsp"

def print_result(name, response):
    """打印测试结果"""
    if response.status_code == 200:
        print(f"✓ {name}: 成功")
    else:
        print(f"✗ {name}: 失败 (状态码: {response.status_code})")
        if response.text:
            print(f"  错误: {response.text}")

def test_all_apis():
    """测试所有API接口"""
    
    print("=== 测试LSP积分系统所有API接口 ===\n")
    
    # 1. 系统状态接口
    print("1. 系统状态接口:")
    
    # 根路径
    response = requests.get(f"{BASE_URL}/")
    print_result("根路径", response)
    
    # 健康检查
    response = requests.get(f"{BASE_URL}/health")
    print_result("健康检查", response)
    
    # 2. 认证接口
    print("\n2. 认证接口:")
    
    # 认证状态
    response = requests.get(f"{BASE_URL}/api/v1/auth/status")
    print_result("认证状态", response)
    
    # 3. 健康数据接口
    print("\n3. 健康数据接口:")
    
    # 每日健康数据汇总
    response = requests.get(
        f"{BASE_URL}/api/v1/health/daily-summary",
        params={"user_id": "user_001", "date": "2025-07-08"}
    )
    print_result("每日健康数据汇总", response)
    
    # 4. 积分计算接口
    print("\n4. 积分计算接口:")
    
    # 计算每日积分
    response = requests.get(
        f"{BASE_URL}/api/v1/score/daily",
        params={"user_id": "user_001", "date": "2025-07-08"}
    )
    print_result("计算每日积分", response)
    
    # 计算日期范围积分
    response = requests.get(
        f"{BASE_URL}/api/v1/score/range",
        params={
            "user_id": "user_001",
            "start_date": "2025-07-05",
            "end_date": "2025-07-08"
        }
    )
    print_result("计算日期范围积分", response)
    
    # 获取可用积分维度
    response = requests.get(
        f"{BASE_URL}/api/v1/score/available-dimensions",
        params={"user_id": "user_001"}
    )
    print_result("获取可用积分维度", response)
    
    # 5. 积分查询接口
    print("\n5. 积分查询接口:")
    
    # 查询有效积分
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": "user_001"}
    )
    print_result("查询有效积分", response)
    
    # 查询积分历史
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/history",
        params={
            "user_id": "user_001",
            "start_date": "2025-07-01",
            "end_date": "2025-07-09"
        }
    )
    print_result("查询积分历史", response)
    
    # 查询即将过期积分
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/expiring",
        params={"user_id": "user_001", "days_ahead": 30}
    )
    print_result("查询即将过期积分", response)
    
    # 获取用户等级统计
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/tier-stats",
        params={"user_id": "user_001"}
    )
    print_result("获取用户等级统计", response)
    
    # 获取月度汇总
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/summary/2025/7",
        params={"user_id": "user_001"}
    )
    print_result("获取月度汇总", response)
    
    # 6. 边缘情况测试
    print("\n6. 边缘情况测试:")
    
    # 不存在的用户
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": "non_existent_user"}
    )
    print_result("不存在的用户", response)
    
    # 未来日期
    response = requests.get(
        f"{BASE_URL}/api/v1/score/daily",
        params={"user_id": "user_001", "date": "2025-12-31"}
    )
    print_result("未来日期", response)
    
    # 空user_id
    response = requests.get(f"{BASE_URL}/api/v1/scores/valid?user_id=")
    print_result("空user_id", response)
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    test_all_apis()