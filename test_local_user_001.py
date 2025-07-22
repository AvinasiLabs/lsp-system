#!/usr/bin/env python3
"""
测试本地user_001的积分计算
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/lsp"

def test_user_001():
    """测试user_001的各种接口"""
    
    print("=== 测试user_001的积分计算 ===\n")
    
    # 1. 获取可用的积分维度
    print("1. 获取可用的积分维度:")
    response = requests.get(
        f"{BASE_URL}/api/v1/score/available-dimensions",
        params={"user_id": "user_001"}
    )
    if response.status_code == 200:
        print(f"   可用维度: {response.json()['dimensions']}")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    # 2. 获取最近有数据的日期的积分
    dates_to_test = ["2025-07-08", "2025-07-07", "2025-07-06"]
    
    for date in dates_to_test:
        print(f"2. 计算 {date} 的积分:")
        response = requests.get(
            f"{BASE_URL}/api/v1/score/daily",
            params={"user_id": "user_001", "date": date}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   总积分: {data['total_score']}")
            print(f"   用户等级: {data['user_level']}")
            print("   各维度积分:")
            for dim, scores in data['dimension_scores'].items():
                if scores['total'] > 0:
                    print(f"     - {dim}: {scores['total']} (easy:{scores['easy']}, medium:{scores['medium']}, hard:{scores['hard']})")
            
            # 显示健康数据问题
            health = data['health_summary']
            if health['sleep_hours'] and health['sleep_hours'] > 24:
                print(f"   ⚠️  睡眠时间异常: {health['sleep_hours']}小时")
        else:
            print(f"   错误: {response.status_code}")
        print()
    
    # 3. 获取日期范围的积分
    print("3. 获取一周的积分汇总:")
    response = requests.get(
        f"{BASE_URL}/api/v1/score/range",
        params={
            "user_id": "user_001",
            "start_date": "2025-07-03",
            "end_date": "2025-07-09"
        }
    )
    
    if response.status_code == 200:
        scores = response.json()
        print(f"   获取到 {len(scores)} 天的积分数据")
        total = sum(s['total_score'] for s in scores)
        print(f"   一周总积分: {total}")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    # 4. 获取健康数据汇总
    print("4. 获取2025-07-08的健康数据:")
    response = requests.get(
        f"{BASE_URL}/api/v1/health/daily-summary",
        params={"user_id": "user_001", "date": "2025-07-08"}
    )
    
    if response.status_code == 200:
        health = response.json()
        print(f"   睡眠: {health.get('sleep_hours', 'N/A')} 小时")
        print(f"   步数: {health.get('steps', 'N/A')} 步")
        print(f"   活动能量: {health.get('active_energy', 'N/A')} 卡路里")
        print(f"   运动时长: {health.get('exercise_minutes', 'N/A')} 分钟")
        print(f"   饮水: {health.get('water_ml', 'N/A')} 毫升")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    # 5. 测试有效积分查询
    print("5. 查询有效积分（可能失败）:")
    response = requests.get(
        f"{BASE_URL}/api/v1/scores/valid",
        params={"user_id": "user_001"}
    )
    print(f"   状态码: {response.status_code}")
    if response.status_code == 200:
        print(f"   响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    else:
        print(f"   错误: {response.json()}")

if __name__ == "__main__":
    test_user_001()