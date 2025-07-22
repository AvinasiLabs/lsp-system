#!/usr/bin/env python3
"""
测试valid积分接口的边缘情况
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/lsp"

def test_valid_scores_edge_cases():
    """测试各种边缘情况"""
    
    print("=== 测试有效积分接口的边缘情况 ===\n")
    
    # 测试1: 不存在的用户
    print("1. 测试不存在的用户:")
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": "non_existent_user_12345"}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # 测试2: 存在但没有任何积分记录的用户
    print("2. 测试没有积分记录的用户:")
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": "new_user_no_scores"}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # 测试3: 空的user_id
    print("3. 测试空的user_id:")
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": ""}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # 测试4: 不提供user_id参数（认证禁用时）
    print("4. 测试不提供user_id参数:")
    response = requests.get(f"{BASE_URL}/api/v1/scores/valid")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # 测试5: 特殊字符的user_id
    print("5. 测试特殊字符的user_id:")
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": "user@#$%^&*()"}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # 测试6: 超长的user_id
    print("6. 测试超长的user_id:")
    long_user_id = "user_" + "x" * 200
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": long_user_id}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()
    
    # 测试7: 正常的用户（如果存在）
    print("7. 测试正常的用户（user_001）:")
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": "user_001"}
    )
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    print()

if __name__ == "__main__":
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    try:
        test_valid_scores_edge_cases()
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()