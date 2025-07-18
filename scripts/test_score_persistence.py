#!/usr/bin/env python3
"""
测试积分持久化功能
"""
import sys
import os
from datetime import datetime, timedelta
import requests
import json

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.score_engine import ScoreEngine
from src.services.score_persistence_service import ScorePersistenceService
from src.db.postgresql import POSTGRES_POOL


def test_direct_persistence():
    """直接测试持久化服务"""
    print("=== 测试积分持久化服务 ===\n")
    
    service = ScorePersistenceService()
    user_id = "test_user_001"
    test_date = datetime(2025, 7, 18)
    
    # 1. 测试过期日期计算
    print("1. 测试过期日期计算")
    for tier in ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Ambassador"]:
        expire_date = service.calculate_expire_date(test_date, tier)
        if expire_date:
            days_until_expire = (expire_date - test_date).days
            print(f"   {tier}: {days_until_expire}天后过期 ({expire_date.date()})")
        else:
            print(f"   {tier}: 永不过期")
    print()
    
    # 2. 测试保存积分
    print("2. 测试保存积分")
    dimension_scores = {
        'sleep': {
            'easy': 1000,
            'medium': 0,
            'hard': 0,
            'super_hard': 0,
            'total': 1000,
            'details': {'sleep_hours': 7.8}
        },
        'exercise': {
            'easy': 500,
            'medium': 800,
            'hard': 0,
            'super_hard': 0,
            'total': 1300,
            'details': {'steps': 10000, 'exercise_minutes': 30}
        }
    }
    
    success = service.save_daily_scores(
        user_id=user_id,
        date=test_date,
        dimension_scores=dimension_scores,
        total_score=2300,
        tier_level="Bronze"
    )
    print(f"   保存结果: {'成功' if success else '失败'}")
    print()
    
    # 3. 测试查询有效积分
    print("3. 测试查询有效积分")
    valid_scores = service.get_user_valid_scores(user_id)
    print(f"   总有效积分: {valid_scores['total_valid_score']}")
    print(f"   各维度积分: {valid_scores['dimension_scores']}")
    print()
    
    # 4. 测试查询积分历史
    print("4. 测试查询积分历史")
    history = service.get_user_score_history(
        user_id,
        test_date - timedelta(days=7),
        test_date + timedelta(days=1)
    )
    print(f"   找到{len(history)}条记录")
    for record in history[:3]:  # 只显示前3条
        print(f"   - {record['date']} {record['dimension']} {record['score']}分")
    print()
    
    # 5. 测试即将过期积分
    print("5. 测试即将过期积分")
    expiring = service.get_expiring_scores(user_id, days_ahead=200)
    print(f"   未来200天内将过期: {expiring.get('total_expiring_score', 0)}分")
    print()


def test_score_engine_integration():
    """测试ScoreEngine集成"""
    print("\n=== 测试ScoreEngine自动保存 ===\n")
    
    # 创建引擎，启用自动保存
    engine = ScoreEngine(auto_save=True)
    user_id = "test_user_002"
    test_date = datetime(2025, 7, 18)
    
    print("1. 计算并自动保存积分")
    result = engine.calculate_daily_score(user_id, test_date)
    
    print(f"   用户ID: {result['user_id']}")
    print(f"   日期: {result['date']}")
    print(f"   总积分: {result['total_score']}")
    print(f"   保存到数据库: {result.get('saved_to_db', False)}")
    print()
    
    # 验证保存结果
    print("2. 验证保存结果")
    service = ScorePersistenceService()
    valid_scores = service.get_user_valid_scores(user_id)
    print(f"   数据库中的有效积分: {valid_scores['total_valid_score']}")
    print()


def test_api_endpoints(base_url="http://localhost:8000"):
    """测试API端点"""
    print("\n=== 测试积分查询API ===\n")
    
    headers = {}
    params = {}
    
    # 根据认证状态设置参数
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            auth_enabled = response.json().get('auth_enabled', False)
            if not auth_enabled:
                params['user_id'] = 'test_user_001'
            else:
                print("认证已启用，需要先获取token")
                return
    except:
        print("API服务器未运行，跳过API测试")
        return
    
    # 1. 测试有效积分查询
    print("1. 测试有效积分查询")
    response = requests.get(
        f"{base_url}/api/v1/scores/valid",
        params=params,
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   总有效积分: {data['total_valid_score']}")
        print(f"   记录数: {data['record_count']}")
    else:
        print(f"   错误: {response.status_code} - {response.text}")
    print()
    
    # 2. 测试积分历史查询
    print("2. 测试积分历史查询")
    history_params = params.copy()
    history_params.update({
        'start_date': '2025-07-10',
        'end_date': '2025-07-20',
        'include_expired': False
    })
    response = requests.get(
        f"{base_url}/api/v1/scores/history",
        params=history_params,
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   找到{len(data)}条记录")
        for record in data[:3]:
            print(f"   - {record['date']} {record['dimension']} {record['score']}分")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    # 3. 测试即将过期积分
    print("3. 测试即将过期积分")
    expiring_params = params.copy()
    expiring_params['days_ahead'] = 30
    response = requests.get(
        f"{base_url}/api/v1/scores/expiring",
        params=expiring_params,
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   30天内将过期: {data['total_expiring_score']}分")
    else:
        print(f"   错误: {response.status_code}")
    print()
    
    # 4. 测试等级统计
    print("4. 测试等级统计")
    response = requests.get(
        f"{base_url}/api/v1/scores/tier-stats",
        params=params,
        headers=headers
    )
    if response.status_code == 200:
        data = response.json()
        print(f"   当前等级: {data['current_tier']}")
        print(f"   累计获得: {data['total_earned_score']}分")
        print(f"   当前有效: {data['total_valid_score']}分")
        print(f"   过期规则: {data['expiration_months']}个月")
    else:
        print(f"   错误: {response.status_code}")
    print()


def test_expiration_mechanism():
    """测试过期机制"""
    print("\n=== 测试积分过期机制 ===\n")
    
    service = ScorePersistenceService()
    
    # 创建一些测试数据
    user_id = "test_user_expire"
    
    # 保存一些已经应该过期的积分
    old_date = datetime.now() - timedelta(days=200)  # 200天前
    
    print("1. 保存200天前的积分（应该已过期）")
    success = service.save_daily_scores(
        user_id=user_id,
        date=old_date,
        dimension_scores={
            'sleep': {'easy': 1000, 'medium': 0, 'hard': 0, 'super_hard': 0, 'total': 1000}
        },
        total_score=1000,
        tier_level="Bronze"  # 6个月过期
    )
    print(f"   保存结果: {'成功' if success else '失败'}")
    
    # 检查过期
    print("\n2. 执行过期检查")
    checked, expired = service.mark_expired_scores()
    print(f"   检查了{checked}条记录")
    print(f"   标记了{expired}条为过期")
    
    # 验证过期结果
    print("\n3. 验证过期结果")
    valid_scores = service.get_user_valid_scores(user_id)
    print(f"   该用户的有效积分: {valid_scores['total_valid_score']}")
    print()


def cleanup_test_data():
    """清理测试数据"""
    print("\n=== 清理测试数据 ===\n")
    
    try:
        conn = POSTGRES_POOL.get_connection()
        cursor = conn.cursor()
        
        # 删除测试用户的数据
        test_users = ['test_user_001', 'test_user_002', 'test_user_expire']
        
        cursor.execute("""
            DELETE FROM user_scores 
            WHERE user_id IN %s
        """, (tuple(test_users),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        
        print(f"清理了{deleted_count}条测试记录")
        
    except Exception as e:
        print(f"清理失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            POSTGRES_POOL.return_connection(conn)


def main():
    """主函数"""
    print("LSP积分系统 - 持久化功能测试\n")
    
    try:
        # 1. 测试持久化服务
        test_direct_persistence()
        
        # 2. 测试ScoreEngine集成
        test_score_engine_integration()
        
        # 3. 测试过期机制
        test_expiration_mechanism()
        
        # 4. 测试API端点（如果服务器在运行）
        test_api_endpoints()
        
        # 5. 清理测试数据
        # cleanup_test_data()  # 可选，根据需要启用
        
        print("\n✅ 所有测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()