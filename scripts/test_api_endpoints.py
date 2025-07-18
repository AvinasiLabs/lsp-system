#!/usr/bin/env python3
"""
测试API端点的多用户功能
"""
import requests
import json
from datetime import datetime, timedelta


def test_api_endpoints(base_url="http://localhost:8000"):
    """测试基础API端点"""
    print("LSP积分系统 - API端点测试\n")
    
    # 测试根路径
    print("1. 测试根路径")
    response = requests.get(f"{base_url}/")
    print(f"   状态码: {response.status_code}")
    data = response.json()
    print(f"   响应: {data}")
    auth_enabled = data.get("auth_enabled", False)
    print(f"   认证系统: {'已启用' if auth_enabled else '已禁用'}\n")
    
    # 测试健康检查
    print("2. 测试健康检查")
    response = requests.get(f"{base_url}/health")
    print(f"   状态码: {response.status_code}")
    print(f"   响应: {response.json()}\n")
    
    return auth_enabled


def test_auth_endpoints(base_url):
    """测试认证端点"""
    print("=== 测试认证系统 ===\n")
    
    # 检查认证状态
    print("1. 检查认证状态")
    response = requests.get(f"{base_url}/api/v1/auth/status")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   认证启用: {data['auth_enabled']}")
        print(f"   消息: {data['message']}")
        return data['auth_enabled']
    return False


def get_test_token(base_url, user_id="user_001"):
    """获取测试令牌"""
    print(f"\n2. 为用户 {user_id} 创建测试令牌")
    response = requests.post(f"{base_url}/api/v1/auth/demo-token/{user_id}")
    if response.status_code == 200:
        data = response.json()
        token = data['access_token']
        print(f"   获得令牌: {token[:20]}...")
        print(f"   用户ID: {data['user_id']}")
        print(f"   过期时间: {data['expires_in']}秒")
        return token
    else:
        print(f"   错误: {response.text}")
        return None


def test_health_endpoints(base_url, auth_enabled):
    """测试健康数据端点"""
    print("\n=== 测试健康数据端点 ===\n")
    
    # 准备请求头
    headers = {}
    params = {"date": "2025-07-08"}
    
    if auth_enabled:
        # 获取测试令牌
        token = get_test_token(base_url, "user_001")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        else:
            print("⚠️  警告: 无法获取认证令牌")
            return
    else:
        # 非认证模式，使用查询参数
        params["user_id"] = "user_001"
    
    # 测试健康数据汇总
    print("\n3. 测试健康数据汇总")
    response = requests.get(
        f"{base_url}/api/v1/health/daily-summary", 
        params=params, 
        headers=headers
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   日期: {data['date']}")
        print(f"   睡眠: {data.get('sleep_hours', 'N/A')} 小时")
        print(f"   步数: {data.get('steps', 'N/A')} 步")
        print(f"   运动: {data.get('exercise_minutes', 'N/A')} 分钟")
    else:
        print(f"   错误: {response.text}")
    
    # 测试每日积分计算
    print("\n4. 测试每日积分计算")
    response = requests.get(
        f"{base_url}/api/v1/score/daily", 
        params=params, 
        headers=headers
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   用户ID: {data['user_id']}")
        print(f"   日期: {data['date']}")
        print(f"   总积分: {data['total_score']}")
        print(f"   等级: {data['user_level']}")
        print("   维度积分:")
        for dim, scores in data['dimension_scores'].items():
            if scores['total'] > 0:
                print(f"     {dim}: {scores['total']} 分")
    else:
        print(f"   错误: {response.text}")
    
    # 测试积分范围查询
    print("\n5. 测试积分范围查询（一周数据）")
    range_params = {
        "start_date": "2025-07-03",
        "end_date": "2025-07-09"
    }
    if not auth_enabled:
        range_params["user_id"] = "user_001"
    
    response = requests.get(
        f"{base_url}/api/v1/score/range", 
        params=range_params, 
        headers=headers
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   查询到 {len(data)} 天的数据")
        total_score = sum(d['total_score'] for d in data)
        avg_score = total_score / len(data) if data else 0
        print(f"   总积分: {total_score}")
        print(f"   平均每日积分: {avg_score:.0f}")
    else:
        print(f"   错误: {response.text}")
    
    # 测试可用维度查询
    print("\n6. 测试可用维度查询")
    dim_params = {}
    if not auth_enabled:
        dim_params["user_id"] = "user_001"
    
    response = requests.get(
        f"{base_url}/api/v1/score/available-dimensions", 
        params=dim_params, 
        headers=headers
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("   可用维度:")
        for dim, available in data['dimensions'].items():
            status = "✅" if available else "❌"
            print(f"     {status} {dim}")
    else:
        print(f"   错误: {response.text}")


def test_multi_user_isolation(base_url, auth_enabled):
    """测试多用户数据隔离"""
    print("\n\n=== 测试多用户数据隔离 ===\n")
    
    test_date = "2025-07-08"
    users = ["user_001", "user_002", "user_003"]
    
    print(f"测试日期: {test_date}")
    print(f"测试用户: {', '.join(users)}")
    
    if auth_enabled:
        print("\n认证模式下的多用户测试：")
        print("为每个用户创建独立的访问令牌...\n")
        
        for user_id in users:
            # 获取该用户的令牌
            token = get_test_token(base_url, user_id)
            if not token:
                print(f"❌ 无法为用户 {user_id} 创建令牌")
                continue
            
            headers = {"Authorization": f"Bearer {token}"}
            
            # 测试健康数据
            response = requests.get(
                f"{base_url}/api/v1/health/daily-summary",
                params={"date": test_date},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n用户 {user_id}:")
                print(f"  健康数据: 睡眠={data.get('sleep_hours', 0)}小时, "
                      f"步数={data.get('steps', 0)}步")
            
            # 测试积分
            response = requests.get(
                f"{base_url}/api/v1/score/daily",
                params={"date": test_date},
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  积分: {data['total_score']}分, 等级: {data['user_level']}")
    else:
        print("\n非认证模式下的多用户测试：")
        print("使用user_id查询参数区分用户...\n")
        
        for user_id in users:
            print(f"用户 {user_id}:")
            
            # 测试健康数据
            response = requests.get(
                f"{base_url}/api/v1/health/daily-summary",
                params={"user_id": user_id, "date": test_date}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  健康数据: 睡眠={data.get('sleep_hours', 0)}小时, "
                      f"步数={data.get('steps', 0)}步")
            
            # 测试积分
            response = requests.get(
                f"{base_url}/api/v1/score/daily",
                params={"user_id": user_id, "date": test_date}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  积分: {data['total_score']}分, 等级: {data['user_level']}")
            
            print()


def main():
    """主函数"""
    import sys
    
    # 检查服务器是否运行
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/", timeout=2)
    except requests.exceptions.ConnectionError:
        print("❌ 错误: API服务器未运行")
        print("   请先运行: python start_server.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 连接错误: {e}")
        sys.exit(1)
    
    # 运行测试
    auth_enabled = test_api_endpoints(base_url)
    auth_enabled = test_auth_endpoints(base_url)
    test_health_endpoints(base_url, auth_enabled)
    test_multi_user_isolation(base_url, auth_enabled)
    
    # 显示API文档地址
    print("\n\n=== API文档地址 ===")
    print(f"Swagger UI: {base_url}/docs")
    print(f"ReDoc: {base_url}/redoc")
    
    print("\n✅ 所有测试完成!")


if __name__ == "__main__":
    main()