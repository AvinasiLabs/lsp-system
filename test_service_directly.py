#!/usr/bin/env python3
"""
直接测试ScorePersistenceService
"""
from datetime import datetime
from src.services.score_persistence_service import ScorePersistenceService
from src.db.postgresql import POSTGRES_POOL

def test_service():
    print("=== 直接测试ScorePersistenceService ===\n")
    
    service = ScorePersistenceService()
    
    # 测试get_user_valid_scores
    print("1. 测试get_user_valid_scores:")
    try:
        result = service.get_user_valid_scores('user_001')
        print(f"   结果: {result}")
        
        if 'error' in result:
            print(f"\n   ✗ 错误信息: {result['error']}")
            
            # 尝试分析错误
            print("\n2. 分析错误原因:")
            
            # 直接测试查询
            try:
                data = POSTGRES_POOL.select_data(
                    table_name="user_scores",
                    conditions="""
                        user_id = %s 
                        AND is_expired = FALSE 
                        AND (expire_date IS NULL OR expire_date > %s)
                        AND dimension != 'total'
                    """,
                    params=('user_001', datetime.now())
                )
                print(f"   查询返回数据类型: {type(data)}")
                if data:
                    print(f"   第一条记录类型: {type(data[0])}")
                    print(f"   第一条记录内容: {data[0]}")
                    
                    # 尝试访问数据
                    try:
                        if isinstance(data[0], dict):
                            print(f"   dimension字段: {data[0]['dimension']}")
                        elif isinstance(data[0], tuple):
                            print(f"   ✗ 数据是元组而不是字典！")
                            print("   这就是问题所在 - select_data返回元组而代码期望字典")
                    except Exception as e:
                        print(f"   访问数据失败: {e}")
                        
            except Exception as e:
                print(f"   直接查询失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   ✓ 成功! 有效积分: {result['total_valid_score']}")
            
    except Exception as e:
        print(f"   ✗ 调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_service()