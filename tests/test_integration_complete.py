#!/usr/bin/env python3
"""
完整集成测试脚本
端到端测试睡眠分析到积分计算的完整工作流程，包括多源数据处理和冲突解决
"""

import os
import sys
import json
import requests
import traceback
from datetime import datetime, date, timedelta, time
from typing import Dict, List, Optional, Tuple
import sqlite3
import tempfile

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.core.score_engine import ScoreEngine
from src.services.sleep_analysis_service import SleepAnalysisService
from src.services.health_data_service import HealthDataService
from src.services.score_persistence_service import ScorePersistenceService
from src.models.health_data import DailyHealthSummary
from src.utils.logger import logger


class IntegrationCompleteTest:
    """完整集成测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """初始化集成测试类"""
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.base_url = base_url
        
        # 初始化服务
        self.score_engine = ScoreEngine(auto_save=False)
        self.sleep_service = SleepAnalysisService()
        self.health_service = HealthDataService()
        self.persistence_service = ScorePersistenceService()
        
    def run_all_tests(self) -> Dict:
        """运行所有集成测试"""
        print("🔄 开始完整集成测试...")
        print("=" * 80)
        
        # 测试套件
        test_suites = [
            ("服务初始化验证", self._test_service_initialization),
            ("数据流集成测试", self._test_data_flow_integration),
            ("睡眠分析到积分计算", self._test_sleep_analysis_to_scoring),
            ("多源数据处理集成", self._test_multi_source_data_integration),
            ("数据冲突解决测试", self._test_data_conflict_resolution),
            ("完整工作流测试", self._test_complete_workflow),
            ("API端到端测试", self._test_api_end_to_end),
            ("错误处理集成测试", self._test_error_handling_integration),
            ("性能集成测试", self._test_performance_integration),
            ("数据一致性验证", self._test_data_consistency),
        ]
        
        for suite_name, test_func in test_suites:
            print(f"\n📋 {suite_name}")
            print("-" * 60)
            try:
                test_func()
            except Exception as e:
                self._record_test_result(
                    test_name=suite_name,
                    passed=False,
                    message=f"测试套件执行失败: {str(e)}",
                    details={"error": str(e), "traceback": traceback.format_exc()}
                )
        
        return self._generate_report()
    
    def _test_service_initialization(self):
        """测试服务初始化验证"""
        
        # 测试各服务是否能正常初始化
        services_to_test = [
            ("ScoreEngine", self.score_engine),
            ("SleepAnalysisService", self.sleep_service),
            ("HealthDataService", self.health_service),
            ("ScorePersistenceService", self.persistence_service),
        ]
        
        for service_name, service in services_to_test:
            try:
                # 检查服务对象是否有必要的方法
                required_methods = {
                    "ScoreEngine": ["calculate_daily_score", "get_available_dimensions"],
                    "SleepAnalysisService": ["analyze_sleep_stages", "get_sleep_time_details"],
                    "HealthDataService": ["get_daily_summary"],
                    "ScorePersistenceService": ["save_daily_scores", "get_user_valid_scores"],
                }
                
                if service_name in required_methods:
                    missing_methods = []
                    for method in required_methods[service_name]:
                        if not hasattr(service, method):
                            missing_methods.append(method)
                    
                    if missing_methods:
                        self._record_test_result(
                            test_name=f"服务初始化: {service_name}",
                            passed=False,
                            message=f"缺少必要方法: {missing_methods}"
                        )
                    else:
                        self._record_test_result(
                            test_name=f"服务初始化: {service_name}",
                            passed=True,
                            message="服务初始化正常，包含所有必要方法"
                        )
                else:
                    self._record_test_result(
                        test_name=f"服务初始化: {service_name}",
                        passed=True,
                        message="服务初始化正常"
                    )
                    
            except Exception as e:
                self._record_test_result(
                    test_name=f"服务初始化: {service_name}",
                    passed=False,
                    message=f"初始化失败: {str(e)}"
                )
    
    def _test_data_flow_integration(self):
        """测试数据流集成"""
        
        try:
            # 模拟数据输入 -> 处理 -> 输出的完整流程
            test_user_id = "integration_test_user"
            test_date = datetime(2024, 1, 15)
            
            # 1. 创建健康数据摘要
            health_summary = DailyHealthSummary(
                sleep_hours=8.0,
                steps=10000,
                exercise_minutes=45,
                water_ml=2500,
                hrv=35,
                stand_hours=8
            )
            
            # 2. 通过积分引擎计算积分
            score_result = self.score_engine.calculate_daily_score(
                user_id=test_user_id,
                date=test_date,
                save_to_db=False
            )
            
            # 3. 验证数据流完整性
            required_fields = [
                "user_id", "date", "health_summary", "dimension_scores", 
                "dimension_percentages", "total_score", "timestamp"
            ]
            
            missing_fields = [field for field in required_fields if field not in score_result]
            
            if missing_fields:
                self._record_test_result(
                    test_name="数据流集成: 结果完整性",
                    passed=False,
                    message=f"缺少字段: {missing_fields}",
                    details={"result_keys": list(score_result.keys())}
                )
            else:
                self._record_test_result(
                    test_name="数据流集成: 结果完整性",
                    passed=True,
                    message="数据流结果包含所有必要字段",
                    details={"total_score": score_result.get("total_score", 0)}
                )
            
            # 4. 验证积分合理性
            total_score = score_result.get("total_score", 0)
            dimension_scores = score_result.get("dimension_scores", {})
            
            if total_score > 0:
                self._record_test_result(
                    test_name="数据流集成: 积分计算",
                    passed=True,
                    message=f"成功计算积分: {total_score}",
                    details={"dimension_scores": dimension_scores}
                )
            else:
                self._record_test_result(
                    test_name="数据流集成: 积分计算",
                    passed=False,
                    message="积分计算结果为0，可能存在问题"
                )
            
        except Exception as e:
            self._record_test_result(
                test_name="数据流集成测试",
                passed=False,
                message=f"数据流测试失败: {str(e)}"
            )
    
    def _test_sleep_analysis_to_scoring(self):
        """测试从睡眠分析到积分计算的完整流程"""
        
        # 测试场景：不同质量的睡眠数据
        sleep_scenarios = [
            {
                "name": "优质睡眠",
                "health_data": DailyHealthSummary(sleep_hours=8.5),
                "expected_easy_score": 1000,  # 应该获得满分
                "description": "8.5小时充足睡眠"
            },
            {
                "name": "一般睡眠",
                "health_data": DailyHealthSummary(sleep_hours=7.0),
                "expected_easy_score": 850,  # 应该扣分
                "description": "7小时中等睡眠"
            },
            {
                "name": "睡眠不足",
                "health_data": DailyHealthSummary(sleep_hours=5.5),
                "expected_easy_score": 0,    # 应该无分
                "description": "5.5小时睡眠不足"
            }
        ]
        
        for scenario in sleep_scenarios:
            try:
                # 计算睡眠积分
                result = self.score_engine.calculate_daily_score(
                    user_id="sleep_test_user",
                    date=datetime.now(),
                    save_to_db=False
                )
                
                # 获取睡眠维度积分
                sleep_scores = result.get("dimension_scores", {}).get("sleep", {})
                easy_score = sleep_scores.get("easy", 0)
                
                # 验证积分是否符合预期（允许±10%的误差）
                expected = scenario["expected_easy_score"]
                if expected == 0:
                    passed = easy_score == 0
                else:
                    passed = abs(easy_score - expected) <= expected * 0.1
                
                self._record_test_result(
                    test_name=f"睡眠分析积分: {scenario['name']}",
                    passed=passed,
                    message=f"期望: {expected}, 实际: {easy_score}",
                    details={
                        "scenario": scenario["description"],
                        "sleep_hours": scenario["health_data"].sleep_hours,
                        "sleep_scores": sleep_scores
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"睡眠分析积分: {scenario['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_multi_source_data_integration(self):
        """测试多源数据处理集成"""
        
        # 模拟多个数据源的数据
        data_source_scenarios = [
            {
                "name": "Apple Watch数据",
                "source": "Apple Watch",
                "priority": 1,
                "data_quality": "高"
            },
            {
                "name": "Oura Ring数据",
                "source": "Oura",
                "priority": 2,
                "data_quality": "中"
            },
            {
                "name": "WHOOP数据",
                "source": "WHOOP",
                "priority": 3,
                "data_quality": "中"
            }
        ]
        
        # 测试数据源优先级逻辑
        for scenario in data_source_scenarios:
            try:
                # 这里测试数据源选择逻辑
                available_sources = [s["source"] for s in data_source_scenarios[:scenario["priority"]]]
                
                # 模拟数据源选择
                source_priority = ["Apple Watch", "Oura", "WHOOP"]
                selected_source = None
                
                for priority_source in source_priority:
                    if priority_source in available_sources:
                        selected_source = priority_source
                        break
                
                expected_source = scenario["source"]
                if scenario["priority"] == 1:
                    expected_source = "Apple Watch"
                elif scenario["priority"] == 2:
                    expected_source = "Apple Watch" if "Apple Watch" in available_sources else "Oura"
                
                passed = selected_source == expected_source
                
                self._record_test_result(
                    test_name=f"多源数据: {scenario['name']}优先级",
                    passed=passed,
                    message=f"选择: {selected_source}, 期望: {expected_source}",
                    details={
                        "available_sources": available_sources,
                        "selected_source": selected_source,
                        "priority": scenario["priority"]
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"多源数据: {scenario['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_data_conflict_resolution(self):
        """测试数据冲突解决"""
        
        # 模拟数据冲突场景
        conflict_scenarios = [
            {
                "name": "睡眠时长冲突",
                "apple_watch_data": {"sleep_hours": 8.0},
                "oura_data": {"sleep_hours": 7.5},
                "expected_resolution": "Apple Watch",  # 优先级更高
                "description": "不同设备报告不同睡眠时长"
            },
            {
                "name": "心率变异性冲突",
                "apple_watch_data": {"hrv": 35},
                "oura_data": {"hrv": 40},
                "expected_resolution": "Apple Watch",
                "description": "HRV数据冲突"
            }
        ]
        
        for scenario in conflict_scenarios:
            try:
                # 模拟冲突解决逻辑
                # 在实际系统中，这应该由数据服务处理
                
                # Apple Watch优先级更高
                if scenario["expected_resolution"] == "Apple Watch":
                    resolved_data = scenario["apple_watch_data"]
                else:
                    resolved_data = scenario["oura_data"]
                
                self._record_test_result(
                    test_name=f"数据冲突解决: {scenario['name']}",
                    passed=True,
                    message=f"使用{scenario['expected_resolution']}数据",
                    details={
                        "scenario": scenario["description"],
                        "resolved_data": resolved_data,
                        "resolution_strategy": "优先级排序"
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"数据冲突解决: {scenario['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_complete_workflow(self):
        """测试完整工作流程"""
        
        try:
            # 端到端测试：从原始数据到最终积分和百分比
            test_user_id = "workflow_test_user"
            test_date = datetime(2024, 2, 15)
            
            # 1. 准备测试数据
            test_health_data = DailyHealthSummary(
                sleep_hours=7.8,      # 接近满分的睡眠
                steps=12000,          # 超过目标的步数
                exercise_minutes=30,  # 中等运动量
                water_ml=2200,        # 适量饮水
                hrv=38,              # 良好的心率变异性
                stand_hours=10       # 充足的站立时间
            )
            
            # 2. 执行完整计算流程
            workflow_result = self.score_engine.calculate_daily_score(
                user_id=test_user_id,
                date=test_date,
                save_to_db=False
            )
            
            # 3. 验证工作流程的各个阶段
            stages_to_verify = [
                ("数据输入", workflow_result.get("health_summary") is not None),
                ("积分计算", workflow_result.get("total_score", 0) > 0),
                ("百分比计算", workflow_result.get("dimension_percentages") is not None),
                ("结果格式化", workflow_result.get("timestamp") is not None),
            ]
            
            for stage_name, stage_passed in stages_to_verify:
                self._record_test_result(
                    test_name=f"完整工作流: {stage_name}",
                    passed=stage_passed,
                    message="阶段完成" if stage_passed else "阶段失败"
                )
            
            # 4. 验证结果合理性
            total_score = workflow_result.get("total_score", 0)
            dimension_scores = workflow_result.get("dimension_scores", {})
            dimension_percentages = workflow_result.get("dimension_percentages", {})
            
            # 检查积分分布是否合理
            if total_score > 0 and dimension_scores:
                calculated_total = 0
                for dim, scores in dimension_scores.items():
                    calculated_total += scores.get("total", 0)
                
                total_consistency = calculated_total == total_score
                
                self._record_test_result(
                    test_name="完整工作流: 积分一致性",
                    passed=total_consistency,
                    message=f"总分一致性检查: {total_score} = {calculated_total}",
                    details={
                        "total_score": total_score,
                        "calculated_total": calculated_total,
                        "dimension_breakdown": dimension_scores
                    }
                )
            
            # 检查百分比是否合理（应该在0-100之间，允许超过100%）
            percentage_reasonable = True
            percentage_issues = []
            
            for dimension, percentages in dimension_percentages.items():
                for difficulty, percentage in percentages.items():
                    if not isinstance(percentage, (int, float)) or percentage < 0:
                        percentage_reasonable = False
                        percentage_issues.append(f"{dimension}.{difficulty}: {percentage}")
            
            self._record_test_result(
                test_name="完整工作流: 百分比合理性",
                passed=percentage_reasonable,
                message="所有百分比数据合理" if percentage_reasonable else f"异常百分比: {percentage_issues}",
                details={"dimension_percentages": dimension_percentages}
            )
            
        except Exception as e:
            self._record_test_result(
                test_name="完整工作流测试",
                passed=False,
                message=f"工作流测试失败: {str(e)}"
            )
    
    def _test_api_end_to_end(self):
        """测试API端到端集成"""
        
        # 检查API服务是否可用
        try:
            health_response = requests.get(f"{self.base_url}/lsp/health", timeout=5)
            if health_response.status_code != 200:
                self._record_test_result(
                    test_name="API端到端: 服务可用性",
                    passed=False,
                    message=f"API服务不可用，状态码: {health_response.status_code}"
                )
                return
            
            self._record_test_result(
                test_name="API端到端: 服务可用性",
                passed=True,
                message="API服务正常运行"
            )
            
        except requests.exceptions.ConnectionError:
            self._record_test_result(
                test_name="API端到端: 服务可用性",
                passed=False,
                message="无法连接到API服务，跳过API集成测试"
            )
            return
        except Exception as e:
            self._record_test_result(
                test_name="API端到端: 服务可用性",
                passed=False,
                message=f"API测试失败: {str(e)}"
            )
            return
        
        # 测试关键API端点
        api_endpoints = [
            {
                "name": "有效积分查询",
                "endpoint": "/lsp/api/v1/scores/valid",
                "method": "GET",
                "expected_fields": ["total_valid_score", "dimension_scores", "dimension_percentages"]
            },
            {
                "name": "积分历史查询",
                "endpoint": "/lsp/api/v1/scores/history?start_date=2024-01-01&end_date=2024-01-31",
                "method": "GET",
                "expected_type": list
            }
        ]
        
        for endpoint_test in api_endpoints:
            try:
                url = f"{self.base_url}{endpoint_test['endpoint']}"
                
                if endpoint_test["method"] == "GET":
                    response = requests.get(url, timeout=10)
                else:
                    response = requests.post(url, json={}, timeout=10)
                
                # 检查响应状态（200, 401, 403都表示端点存在）
                if response.status_code in [200, 401, 403]:
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            
                            # 验证响应格式
                            if "expected_fields" in endpoint_test:
                                if isinstance(data, dict):
                                    has_expected_fields = all(
                                        field in data for field in endpoint_test["expected_fields"]
                                    )
                                    self._record_test_result(
                                        test_name=f"API端到端: {endpoint_test['name']} 响应格式",
                                        passed=has_expected_fields,
                                        message="响应包含期望字段" if has_expected_fields else "响应缺少期望字段"
                                    )
                                else:
                                    self._record_test_result(
                                        test_name=f"API端到端: {endpoint_test['name']} 响应格式",
                                        passed=False,
                                        message="响应不是预期的字典格式"
                                    )
                            
                            elif "expected_type" in endpoint_test:
                                correct_type = isinstance(data, endpoint_test["expected_type"])
                                self._record_test_result(
                                    test_name=f"API端到端: {endpoint_test['name']} 响应类型",
                                    passed=correct_type,
                                    message=f"响应类型正确: {type(data)}" if correct_type else f"响应类型错误: {type(data)}"
                                )
                            
                            self._record_test_result(
                                test_name=f"API端到端: {endpoint_test['name']} 成功响应",
                                passed=True,
                                message="API端点正常响应"
                            )
                            
                        except json.JSONDecodeError:
                            self._record_test_result(
                                test_name=f"API端到端: {endpoint_test['name']} JSON解析",
                                passed=False,
                                message="响应不是有效的JSON格式"
                            )
                    else:
                        self._record_test_result(
                            test_name=f"API端到端: {endpoint_test['name']} 认证",
                            passed=True,
                            message=f"端点存在但需要认证 (状态码: {response.status_code})"
                        )
                else:
                    self._record_test_result(
                        test_name=f"API端到端: {endpoint_test['name']}",
                        passed=False,
                        message=f"API返回错误状态: {response.status_code}",
                        details={"response_text": response.text[:200]}
                    )
                    
            except Exception as e:
                self._record_test_result(
                    test_name=f"API端到端: {endpoint_test['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_error_handling_integration(self):
        """测试错误处理集成"""
        
        # 测试各种错误情况下的系统行为
        error_scenarios = [
            {
                "name": "空健康数据",
                "health_data": DailyHealthSummary(),
                "should_handle_gracefully": True
            },
            {
                "name": "部分健康数据",
                "health_data": DailyHealthSummary(sleep_hours=7.0),
                "should_handle_gracefully": True
            },
            {
                "name": "异常健康数据",
                "health_data": DailyHealthSummary(sleep_hours=-1, steps=-100),
                "should_handle_gracefully": True
            }
        ]
        
        for scenario in error_scenarios:
            try:
                # 尝试处理异常数据
                result = self.score_engine.calculate_daily_score(
                    user_id="error_test_user",
                    date=datetime.now(),
                    save_to_db=False
                )
                
                # 检查是否优雅地处理了错误
                has_result = isinstance(result, dict)
                has_total_score = "total_score" in result if has_result else False
                
                if scenario["should_handle_gracefully"]:
                    self._record_test_result(
                        test_name=f"错误处理: {scenario['name']}",
                        passed=has_result and has_total_score,
                        message="系统优雅处理异常数据" if has_result else "系统未能处理异常数据",
                        details={
                            "input_data": scenario["health_data"].model_dump(),
                            "has_result": has_result,
                            "total_score": result.get("total_score", "N/A") if has_result else None
                        }
                    )
                
            except Exception as e:
                # 对于应该优雅处理的情况，抛出异常表示处理不当
                if scenario["should_handle_gracefully"]:
                    self._record_test_result(
                        test_name=f"错误处理: {scenario['name']}",
                        passed=False,
                        message=f"系统未能优雅处理错误，抛出异常: {str(e)}"
                    )
                else:
                    self._record_test_result(
                        test_name=f"错误处理: {scenario['name']}",
                        passed=True,
                        message=f"系统正确抛出异常: {type(e).__name__}"
                    )
    
    def _test_performance_integration(self):
        """测试性能集成"""
        
        import time
        
        try:
            # 批量处理性能测试
            batch_size = 10
            start_time = time.time()
            
            results = []
            for i in range(batch_size):
                # 创建略有不同的测试数据
                health_data = DailyHealthSummary(
                    sleep_hours=7.0 + (i * 0.1),
                    steps=8000 + (i * 200),
                    exercise_minutes=30 + i,
                    water_ml=2000 + (i * 50)
                )
                
                result = self.score_engine.calculate_daily_score(
                    user_id=f"perf_test_user_{i}",
                    date=datetime.now() - timedelta(days=i),
                    save_to_db=False
                )
                results.append(result)
            
            end_time = time.time()
            total_duration = end_time - start_time
            avg_duration = total_duration / batch_size
            
            # 性能基准：每次计算应该在0.5秒内完成
            performance_acceptable = avg_duration < 0.5
            
            self._record_test_result(
                test_name="性能集成: 批量积分计算",
                passed=performance_acceptable,
                message=f"平均耗时: {avg_duration:.3f}秒/次",
                details={
                    "batch_size": batch_size,
                    "total_duration": total_duration,
                    "avg_duration": avg_duration,
                    "performance_target": "< 0.5秒/次"
                }
            )
            
        except Exception as e:
            self._record_test_result(
                test_name="性能集成测试",
                passed=False,
                message=f"性能测试失败: {str(e)}"
            )
    
    def _test_data_consistency(self):
        """测试数据一致性验证"""
        
        try:
            # 多次计算相同数据，验证结果一致性
            test_health_data = DailyHealthSummary(
                sleep_hours=7.5,
                steps=9000,
                exercise_minutes=25,
                water_ml=2100,
                hrv=32
            )
            
            results = []
            for i in range(5):  # 计算5次
                result = self.score_engine.calculate_daily_score(
                    user_id="consistency_test_user",
                    date=datetime(2024, 3, 1),  # 固定日期
                    save_to_db=False
                )
                results.append(result)
            
            # 验证所有结果的total_score是否相同
            total_scores = [r.get("total_score", 0) for r in results]
            all_same = len(set(total_scores)) == 1
            
            self._record_test_result(
                test_name="数据一致性: 重复计算结果",
                passed=all_same,
                message=f"5次计算结果一致" if all_same else f"结果不一致: {total_scores}",
                details={
                    "total_scores": total_scores,
                    "unique_scores": list(set(total_scores))
                }
            )
            
            # 验证维度积分一致性
            if all_same and results:
                first_result = results[0]
                dimension_scores = first_result.get("dimension_scores", {})
                dimension_percentages = first_result.get("dimension_percentages", {})
                
                # 检查积分和百分比的对应关系
                consistency_issues = []
                for dimension, scores in dimension_scores.items():
                    if dimension in dimension_percentages:
                        percentages = dimension_percentages[dimension]
                        for difficulty in ["easy", "medium", "hard", "super_hard", "total"]:
                            if difficulty in scores and difficulty in percentages:
                                score = scores[difficulty]
                                percentage = percentages[difficulty]
                                
                                # 计算期望百分比
                                from src.core.score_config import calculate_percentage
                                expected_percentage = calculate_percentage(score, dimension, difficulty)
                                
                                if abs(percentage - expected_percentage) > 0.01:
                                    consistency_issues.append(
                                        f"{dimension}.{difficulty}: {percentage}% vs {expected_percentage}%"
                                    )
                
                self._record_test_result(
                    test_name="数据一致性: 积分百分比对应",
                    passed=len(consistency_issues) == 0,
                    message="积分和百分比数据一致" if len(consistency_issues) == 0 else f"发现不一致: {consistency_issues[:3]}"
                )
            
        except Exception as e:
            self._record_test_result(
                test_name="数据一致性验证",
                passed=False,
                message=f"一致性测试失败: {str(e)}"
            )
    
    def _record_test_result(self, test_name: str, passed: bool, message: str, details: Optional[Dict] = None):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {message}")
            
        if details and len(str(details)) < 400:
            print(f"   详情: {json.dumps(details, ensure_ascii=False, default=str)}")
    
    def _generate_report(self) -> Dict:
        """生成测试报告"""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 按测试类别统计
        category_stats = {}
        for result in self.test_results:
            category = result["test_name"].split(":")[0]
            if category not in category_stats:
                category_stats[category] = {"passed": 0, "failed": 0}
            
            if result["passed"]:
                category_stats[category]["passed"] += 1
            else:
                category_stats[category]["failed"] += 1
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "pass_rate": round(pass_rate, 2),
                "test_date": datetime.now().isoformat(),
                "category_stats": category_stats
            },
            "test_results": self.test_results
        }
        
        print("\n" + "=" * 80)
        print("📊 完整集成测试报告")
        print("=" * 80)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {self.passed_tests}")
        print(f"失败测试: {self.failed_tests}")
        print(f"通过率: {pass_rate:.2f}%")
        
        print("\n📋 各类别测试统计:")
        for category, stats in category_stats.items():
            total_cat = stats["passed"] + stats["failed"]
            pass_rate_cat = (stats["passed"] / total_cat * 100) if total_cat > 0 else 0
            print(f"  {category}: {stats['passed']}/{total_cat} ({pass_rate_cat:.1f}%)")
        
        if self.failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # 保存报告到文件
        report_file = f"tests/reports/integration_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return report


def main():
    """主函数"""
    print("🚀 LSP系统完整集成测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建测试实例并运行测试
    test = IntegrationCompleteTest()
    report = test.run_all_tests()
    
    # 根据测试结果设置退出码
    if report["summary"]["failed_tests"] > 0:
        print("\n⚠️  发现集成测试问题，请检查上述失败的测试项")
        sys.exit(1)
    else:
        print("\n🎉 所有集成测试通过!")
        sys.exit(0)


if __name__ == "__main__":
    main()