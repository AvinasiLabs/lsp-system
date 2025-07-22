#!/usr/bin/env python3
"""
详细测试关键API接口
"""
import requests
import json

BASE_URL = "http://localhost:8000/lsp"

def test_key_apis():
    """详细测试关键接口"""
    
    print("=== 详细测试关键API接口 ===\n")
    
    # 1. 测试有效积分查询（之前失败的接口）
    print("1. 测试有效积分查询:")
    response = requests.get(f"{BASE_URL}/api/v1/scores/valid?user_id=user_001")
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   总有效积分: {data['total_valid_score']}")
        print(f"   维度积分: {json.dumps(data['dimension_scores'], indent=6)}")
        print(f"   记录数: {data['record_count']}")
    print()
    
    # 2. 测试健康数据汇总（检查睡眠时间）
    print("2. 测试健康数据汇总（2025-07-08）:")
    response = requests.get(f"{BASE_URL}/api/v1/health/daily-summary?user_id=user_001&date=2025-07-08")
    if response.status_code == 200:
        data = response.json()
        print(f"   睡眠时间: {data['sleep_hours']} 小时")
        print(f"   步数: {data['steps']} 步")
        print(f"   活动能量: {data['active_energy']} 卡路里")
        print(f"   运动时长: {data['exercise_minutes']} 分钟")
    print()
    
    # 3. 测试积分计算
    print("3. 测试积分计算（2025-07-08）:")
    response = requests.get(f"{BASE_URL}/api/v1/score/daily?user_id=user_001&date=2025-07-08")
    if response.status_code == 200:
        data = response.json()
        print(f"   总积分: {data['total_score']}")
        print(f"   用户等级: {data['user_level']}")
        print("   各维度积分:")
        for dim, scores in data['dimension_scores'].items():
            if scores['total'] > 0:
                print(f"     - {dim}: {scores['total']} (easy:{scores['easy']}, medium:{scores['medium']}, hard:{scores['hard']})")
    print()
    
    # 4. 测试即将过期积分
    print("4. 测试即将过期积分:")
    response = requests.get(f"{BASE_URL}/api/v1/scores/expiring?user_id=user_001&days_ahead=180")
    if response.status_code == 200:
        data = response.json()
        print(f"   即将过期总分: {data['total_expiring_score']}")
        print(f"   过期记录数: {len(data['expiring_by_date'])}")
        if data['expiring_by_date']:
            print("   前3个过期日期:")
            for item in data['expiring_by_date'][:3]:
                print(f"     - {item['date']}: {len(item['scores'])}条记录")
    print()
    
    # 5. 测试用户等级统计
    print("5. 测试用户等级统计:")
    response = requests.get(f"{BASE_URL}/api/v1/scores/tier-stats?user_id=user_001")
    if response.status_code == 200:
        data = response.json()
        print(f"   当前等级: {data['current_tier']}")
        print(f"   累计总积分: {data['total_earned_score']}")
        print(f"   当前有效积分: {data['total_valid_score']}")
        print(f"   积分过期时间: {data['expiration_months']} 个月")
    print()
    
    # 6. 测试不同日期的数据
    print("6. 测试不同日期的健康数据:")
    dates = ["2025-07-06", "2025-07-07", "2025-07-08"]
    for date in dates:
        response = requests.get(f"{BASE_URL}/api/v1/health/daily-summary?user_id=user_001&date={date}")
        if response.status_code == 200:
            data = response.json()
            print(f"   {date}: 睡眠{data['sleep_hours']}小时, 步数{data['steps']}步")
    print()
    
    # 7. 测试空数据用户
    print("7. 测试无数据用户:")
    response = requests.get(f"{BASE_URL}/api/v1/scores/valid?user_id=new_user_123")
    if response.status_code == 200:
        data = response.json()
        print(f"   用户ID: {data['user_id']}")
        print(f"   有效积分: {data['total_valid_score']}")
        print(f"   记录数: {data['record_count']}")

if __name__ == "__main__":
    test_key_apis()