#!/usr/bin/env python3
"""
测试边缘情况和错误处理
"""
import requests
import json

BASE_URL = "http://localhost:8000/lsp"

def test_edge_cases():
    """测试各种边缘情况"""
    
    print("=== 测试边缘情况和错误处理 ===\n")
    
    # 1. 测试无效日期
    print("1. 测试无效日期格式:")
    test_cases = [
        ("invalid-date", "无效日期格式"),
        ("2025-13-01", "无效月份"),
        ("2025-07-32", "无效日期"),
        ("", "空日期")
    ]
    
    for date, desc in test_cases:
        response = requests.get(f"{BASE_URL}/api/v1/score/daily?user_id=user_001&date={date}")
        print(f"   {desc} ({date}): 状态码 {response.status_code}")
    print()
    
    # 2. 测试日期范围限制
    print("2. 测试日期范围限制:")
    # 超过90天限制
    response = requests.get(
        f"{BASE_URL}/api/v1/score/range",
        params={
            "user_id": "user_001",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31"
        }
    )
    print(f"   超过90天范围: 状态码 {response.status_code}")
    if response.status_code != 200:
        print(f"   错误信息: {response.json().get('detail', 'N/A')}")
    
    # 结束日期早于开始日期
    response = requests.get(
        f"{BASE_URL}/api/v1/score/range",
        params={
            "user_id": "user_001",
            "start_date": "2025-07-08",
            "end_date": "2025-07-01"
        }
    )
    print(f"   结束日期早于开始日期: 状态码 {response.status_code}")
    if response.status_code != 200:
        print(f"   错误信息: {response.json().get('detail', 'N/A')}")
    print()
    
    # 3. 测试特殊user_id
    print("3. 测试特殊user_id:")
    special_ids = [
        "user with spaces",
        "user@email.com",
        "user/slash",
        "user\\backslash",
        "user'quote",
        'user"doublequote',
        "用户中文",
        "😀emoji",
        "a" * 100  # 超长ID
    ]
    
    for uid in special_ids[:5]:  # 只测试前5个
        response = requests.get(f"{BASE_URL}/api/v1/scores/valid", params={"user_id": uid})
        print(f"   '{uid}': 状态码 {response.status_code}, 积分 {response.json().get('total_valid_score', 'N/A')}")
    print()
    
    # 4. 测试并发请求
    print("4. 测试快速连续请求:")
    import time
    start_time = time.time()
    for i in range(10):
        response = requests.get(f"{BASE_URL}/api/v1/scores/valid?user_id=user_001")
        if response.status_code != 200:
            print(f"   请求{i+1}失败: {response.status_code}")
    elapsed = time.time() - start_time
    print(f"   10次请求耗时: {elapsed:.2f}秒")
    print()
    
    # 5. 测试缺少必需参数
    print("5. 测试缺少必需参数:")
    # 积分历史缺少日期
    response = requests.get(f"{BASE_URL}/api/v1/scores/history?user_id=user_001")
    print(f"   积分历史缺少日期参数: 状态码 {response.status_code}")
    
    # 日期范围缺少end_date
    response = requests.get(f"{BASE_URL}/api/v1/score/range?user_id=user_001&start_date=2025-07-01")
    print(f"   日期范围缺少end_date: 状态码 {response.status_code}")
    print()
    
    # 6. 测试认证系统
    print("6. 测试认证系统:")
    # 尝试登录（认证禁用时）
    response = requests.post(
        f"{BASE_URL}/api/v1/auth/login",
        json={"user_id": "user_001", "password": "password123"}
    )
    print(f"   登录请求（认证禁用）: 状态码 {response.status_code}")
    if response.status_code != 200:
        print(f"   错误信息: {response.json().get('detail', 'N/A')}")

if __name__ == "__main__":
    test_edge_cases()