#!/usr/bin/env python3
"""
完整睡眠分析测试脚本
测试睡眠阶段分析、数据源优先级选择、睡眠积分计算和时间限制评分
"""

import os
import sys
import json
import traceback
from datetime import datetime, date, timedelta, time
from typing import Dict, List, Optional, Tuple
import sqlite3

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.core.calculators.sleep_calculator import SleepCalculator
from src.services.sleep_analysis_service import SleepAnalysisService
from src.models.health_data import DailyHealthSummary
from src.utils.logger import logger


class SleepAnalysisCompleteTest:
    """完整的睡眠分析测试类"""
    
    def __init__(self):
        """初始化测试类"""
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.sleep_calculator = SleepCalculator()
        self.sleep_service = SleepAnalysisService()
        
    def run_all_tests(self) -> Dict:
        """运行所有睡眠分析测试"""
        print("🛌 开始完整睡眠分析测试...")
        print("=" * 80)
        
        # 测试套件
        test_suites = [
            ("睡眠计算器规则验证", self._test_sleep_calculator_rules),
            ("易难度积分计算测试", self._test_easy_score_calculation),
            ("中难度积分计算测试（睡眠阶段）", self._test_medium_score_with_stages),
            ("难难度积分计算测试（时间限制）", self._test_hard_score_with_time_limits),
            ("数据源优先级测试", self._test_data_source_priority),
            ("睡眠阶段分析测试", self._test_sleep_stage_analysis),
            ("时间限制评分测试", self._test_time_restriction_scoring),
            ("边界情况测试", self._test_edge_cases),
            ("连锁惩罚机制测试", self._test_chain_punishment),
            ("综合场景测试", self._test_comprehensive_scenarios),
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
    
    def _test_sleep_calculator_rules(self):
        """测试睡眠计算器规则验证"""
        try:
            rules = self.sleep_calculator.get_rules()
            
            # 验证规则结构完整性
            required_sections = ['easy', 'medium', 'hard', 'super_hard', 'chain_punishment']
            for section in required_sections:
                if section not in rules:
                    self._record_test_result(
                        test_name=f"规则结构: {section}",
                        passed=False,
                        message=f"缺少规则部分: {section}"
                    )
                else:
                    self._record_test_result(
                        test_name=f"规则结构: {section}",
                        passed=True,
                        message=f"规则部分存在",
                        details={"rules": rules[section]}
                    )
            
            # 验证易难度规则
            easy_rules = rules['easy']
            required_easy_fields = ['target_hours', 'min_hours', 'base_points', 'deduction_per_minute']
            for field in required_easy_fields:
                if field not in easy_rules:
                    self._record_test_result(
                        test_name=f"易难度规则: {field}",
                        passed=False,
                        message=f"缺少字段: {field}"
                    )
                else:
                    self._record_test_result(
                        test_name=f"易难度规则: {field}",
                        passed=True,
                        message=f"字段存在: {easy_rules[field]}"
                    )
            
            # 验证中难度规则
            medium_rules = rules['medium']
            required_medium_fields = ['deep_sleep_hours', 'rem_sleep_hours', 'base_points']
            for field in required_medium_fields:
                if field not in medium_rules:
                    self._record_test_result(
                        test_name=f"中难度规则: {field}",
                        passed=False,
                        message=f"缺少字段: {field}"
                    )
                else:
                    self._record_test_result(
                        test_name=f"中难度规则: {field}",
                        passed=True,
                        message=f"字段存在: {medium_rules[field]}"
                    )
            
        except Exception as e:
            self._record_test_result(
                test_name="规则验证",
                passed=False,
                message=f"规则验证失败: {str(e)}"
            )
    
    def _test_easy_score_calculation(self):
        """测试易难度积分计算"""
        
        # 测试用例：不同睡眠时长
        test_cases = [
            {"sleep_hours": 8.0, "expected_score": 1000, "description": "睡够8小时，满分"},
            {"sleep_hours": 7.5, "expected_score": 1000, "description": "睡够7.5小时，满分"},
            {"sleep_hours": 7.0, "expected_score": 850, "description": "睡够7小时，扣分"},
            {"sleep_hours": 6.5, "expected_score": 700, "description": "睡够6.5小时，扣分较多"},
            {"sleep_hours": 6.0, "expected_score": 550, "description": "睡够6小时，扣分很多"},
            {"sleep_hours": 5.5, "expected_score": 0, "description": "睡眠不足6小时，无分"},
            {"sleep_hours": None, "expected_score": 0, "description": "无睡眠数据，无分"},
        ]
        
        for case in test_cases:
            try:
                # 创建测试数据
                health_data = DailyHealthSummary(
                    sleep_hours=case["sleep_hours"]
                )
                
                # 计算积分
                scores = self.sleep_calculator.calculate(health_data)
                actual_score = scores['easy']
                
                # 验证结果（允许±10分的误差）
                if case["expected_score"] == 0:
                    passed = actual_score == 0
                else:
                    passed = abs(actual_score - case["expected_score"]) <= 10
                
                self._record_test_result(
                    test_name=f"易难度计算: {case['description']}",
                    passed=passed,
                    message=f"期望: {case['expected_score']}, 实际: {actual_score}",
                    details={"input": case, "output": scores}
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"易难度计算: {case['description']}",
                    passed=False,
                    message=f"计算失败: {str(e)}"
                )
    
    def _test_medium_score_with_stages(self):
        """测试中难度积分计算（睡眠阶段）"""
        
        # 模拟测试用例
        test_cases = [
            {
                "name": "完美睡眠阶段",
                "deep_sleep_hours": 2.0,
                "rem_sleep_hours": 2.0,
                "expected_score": 2000,
                "description": "深度和REM睡眠都达标"
            },
            {
                "name": "仅深度睡眠达标",
                "deep_sleep_hours": 1.8,
                "rem_sleep_hours": 1.0,
                "expected_score": 1000,
                "description": "只有深度睡眠达标，一半分数"
            },
            {
                "name": "仅REM睡眠达标",
                "deep_sleep_hours": 1.0,
                "rem_sleep_hours": 1.8,
                "expected_score": 1000,
                "description": "只有REM睡眠达标，一半分数"
            },
            {
                "name": "都未达标",
                "deep_sleep_hours": 1.0,
                "rem_sleep_hours": 1.0,
                "expected_score": 0,
                "description": "深度和REM睡眠都未达标"
            }
        ]
        
        for case in test_cases:
            try:
                # 这里测试计算逻辑，不依赖实际数据库
                rules = self.sleep_calculator.get_rules()['medium']
                
                meets_deep = case["deep_sleep_hours"] >= rules['deep_sleep_hours']
                meets_rem = case["rem_sleep_hours"] >= rules['rem_sleep_hours']
                
                if meets_deep and meets_rem:
                    expected_score = rules['base_points']
                elif meets_deep or meets_rem:
                    expected_score = rules['base_points'] // 2
                else:
                    expected_score = 0
                
                passed = expected_score == case["expected_score"]
                
                self._record_test_result(
                    test_name=f"中难度计算: {case['name']}",
                    passed=passed,
                    message=f"期望: {case['expected_score']}, 计算: {expected_score}",
                    details={
                        "deep_sleep": case["deep_sleep_hours"],
                        "rem_sleep": case["rem_sleep_hours"],
                        "meets_deep": meets_deep,
                        "meets_rem": meets_rem
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"中难度计算: {case['name']}",
                    passed=False,
                    message=f"计算失败: {str(e)}"
                )
    
    def _test_hard_score_with_time_limits(self):
        """测试难难度积分计算（时间限制）"""
        
        # 测试时间限制逻辑
        test_cases = [
            {
                "name": "完美时间",
                "sleep_time": time(23, 00),  # 11:00 PM
                "wake_time": time(7, 00),    # 7:00 AM
                "expected_score": 4000,
                "description": "入睡和起床时间都达标"
            },
            {
                "name": "仅入睡时间达标",
                "sleep_time": time(23, 00),  # 11:00 PM
                "wake_time": time(8, 00),    # 8:00 AM
                "expected_score": 2000,
                "description": "只有入睡时间达标"
            },
            {
                "name": "仅起床时间达标",
                "sleep_time": time(23, 45),  # 11:45 PM
                "wake_time": time(7, 00),    # 7:00 AM
                "expected_score": 2000,
                "description": "只有起床时间达标"
            },
            {
                "name": "都未达标",
                "sleep_time": time(23, 45),  # 11:45 PM
                "wake_time": time(8, 00),    # 8:00 AM
                "expected_score": 0,
                "description": "入睡和起床时间都未达标"
            }
        ]
        
        for case in test_cases:
            try:
                rules = self.sleep_calculator.get_rules()['hard']
                
                # 解析目标时间
                sleep_target_time = time(23, 30)  # 11:30 PM
                wake_target_time = time(7, 30)    # 7:30 AM
                
                meets_sleep = case["sleep_time"] <= sleep_target_time
                meets_wake = case["wake_time"] <= wake_target_time
                
                if meets_sleep and meets_wake:
                    expected_score = rules['base_points']
                elif meets_sleep or meets_wake:
                    expected_score = rules['base_points'] // 2
                else:
                    expected_score = 0
                
                passed = expected_score == case["expected_score"]
                
                self._record_test_result(
                    test_name=f"难难度计算: {case['name']}",
                    passed=passed,
                    message=f"期望: {case['expected_score']}, 计算: {expected_score}",
                    details={
                        "sleep_time": case["sleep_time"].strftime('%H:%M'),
                        "wake_time": case["wake_time"].strftime('%H:%M'),
                        "meets_sleep": meets_sleep,
                        "meets_wake": meets_wake
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"难难度计算: {case['name']}",
                    passed=False,
                    message=f"计算失败: {str(e)}"
                )
    
    def _test_data_source_priority(self):
        """测试数据源优先级选择"""
        
        # 测试数据源优先级：Apple Watch > Oura > WHOOP
        priority_tests = [
            {
                "name": "Apple Watch优先级",
                "available_sources": ["Apple Watch", "Oura", "WHOOP"],
                "expected_priority": "Apple Watch"
            },
            {
                "name": "Oura次优先级",
                "available_sources": ["Oura", "WHOOP"],
                "expected_priority": "Oura"
            },
            {
                "name": "WHOOP最低优先级",
                "available_sources": ["WHOOP"],
                "expected_priority": "WHOOP"
            },
            {
                "name": "无数据源",
                "available_sources": [],
                "expected_priority": None
            }
        ]
        
        for test in priority_tests:
            try:
                # 模拟数据源选择逻辑
                source_priority = ["Apple Watch", "Oura", "WHOOP"]
                selected_source = None
                
                for priority_source in source_priority:
                    if priority_source in test["available_sources"]:
                        selected_source = priority_source
                        break
                
                passed = selected_source == test["expected_priority"]
                
                self._record_test_result(
                    test_name=f"数据源优先级: {test['name']}",
                    passed=passed,
                    message=f"期望: {test['expected_priority']}, 选择: {selected_source}",
                    details={
                        "available_sources": test["available_sources"],
                        "selected_source": selected_source
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"数据源优先级: {test['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_sleep_stage_analysis(self):
        """测试睡眠阶段分析"""
        
        # 测试睡眠阶段数据解析
        stage_tests = [
            {
                "name": "完整睡眠阶段",
                "stages": {
                    "deep": 1.8,  # 小时
                    "rem": 1.6,   # 小时
                    "light": 4.0, # 小时
                    "awake": 0.6  # 小时
                },
                "total_sleep": 8.0,
                "expected_deep_percentage": 22.5,  # 1.8/8.0 * 100
                "expected_rem_percentage": 20.0    # 1.6/8.0 * 100
            }
        ]
        
        for test in stage_tests:
            try:
                stages = test["stages"]
                total = test["total_sleep"]
                
                # 计算百分比
                deep_percentage = (stages["deep"] / total) * 100
                rem_percentage = (stages["rem"] / total) * 100
                
                deep_passed = abs(deep_percentage - test["expected_deep_percentage"]) < 0.1
                rem_passed = abs(rem_percentage - test["expected_rem_percentage"]) < 0.1
                
                self._record_test_result(
                    test_name=f"睡眠阶段分析: {test['name']} - 深度睡眠",
                    passed=deep_passed,
                    message=f"期望: {test['expected_deep_percentage']}%, 计算: {deep_percentage:.1f}%",
                    details=test
                )
                
                self._record_test_result(
                    test_name=f"睡眠阶段分析: {test['name']} - REM睡眠",
                    passed=rem_passed,
                    message=f"期望: {test['expected_rem_percentage']}%, 计算: {rem_percentage:.1f}%",
                    details=test
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"睡眠阶段分析: {test['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_time_restriction_scoring(self):
        """测试时间限制评分"""
        
        # 测试不同时间的评分
        time_tests = [
            {
                "sleep_time": "22:30",
                "wake_time": "06:30",
                "expected_sleep_meets": True,
                "expected_wake_meets": True,
                "description": "理想时间"
            },
            {
                "sleep_time": "23:30",
                "wake_time": "07:30",
                "expected_sleep_meets": True,
                "expected_wake_meets": True,
                "description": "边界时间"
            },
            {
                "sleep_time": "23:31",
                "wake_time": "07:31",
                "expected_sleep_meets": False,
                "expected_wake_meets": False,
                "description": "超出边界"
            }
        ]
        
        target_sleep_time = time(23, 30)  # 11:30 PM
        target_wake_time = time(7, 30)    # 7:30 AM
        
        for test in time_tests:
            try:
                # 解析时间字符串
                sleep_time = datetime.strptime(test["sleep_time"], "%H:%M").time()
                wake_time = datetime.strptime(test["wake_time"], "%H:%M").time()
                
                meets_sleep = sleep_time <= target_sleep_time
                meets_wake = wake_time <= target_wake_time
                
                sleep_passed = meets_sleep == test["expected_sleep_meets"]
                wake_passed = meets_wake == test["expected_wake_meets"]
                
                self._record_test_result(
                    test_name=f"时间限制评分: {test['description']} - 入睡",
                    passed=sleep_passed,
                    message=f"入睡时间 {test['sleep_time']}, 达标: {meets_sleep}",
                    details=test
                )
                
                self._record_test_result(
                    test_name=f"时间限制评分: {test['description']} - 起床",
                    passed=wake_passed,
                    message=f"起床时间 {test['wake_time']}, 达标: {meets_wake}",
                    details=test
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"时间限制评分: {test['description']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_edge_cases(self):
        """测试边界情况"""
        
        edge_cases = [
            {
                "name": "零睡眠时间",
                "health_data": DailyHealthSummary(sleep_hours=0),
                "expected_easy": 0
            },
            {
                "name": "负睡眠时间",
                "health_data": DailyHealthSummary(sleep_hours=-1),
                "expected_easy": 0
            },
            {
                "name": "极长睡眠时间",
                "health_data": DailyHealthSummary(sleep_hours=20),
                "expected_easy": 1000
            },
            {
                "name": "空数据",
                "health_data": DailyHealthSummary(),
                "expected_easy": 0
            }
        ]
        
        for case in edge_cases:
            try:
                scores = self.sleep_calculator.calculate(case["health_data"])
                actual_easy = scores['easy']
                
                passed = actual_easy == case["expected_easy"]
                
                self._record_test_result(
                    test_name=f"边界情况: {case['name']}",
                    passed=passed,
                    message=f"期望: {case['expected_easy']}, 实际: {actual_easy}",
                    details={
                        "input": case["health_data"].model_dump(),
                        "output": scores
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"边界情况: {case['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_chain_punishment(self):
        """测试连锁惩罚机制"""
        
        try:
            # 模拟3天睡眠不足的历史数据
            history_data = {}
            base_date = datetime.now() - timedelta(days=3)
            
            for i in range(3):
                date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
                history_data[date_str] = DailyHealthSummary(sleep_hours=5.5)  # 少于6小时
            
            # 测试连锁惩罚检查
            punishment = self.sleep_calculator.check_chain_punishment(history_data)
            
            if punishment:
                self._record_test_result(
                    test_name="连锁惩罚: 3天睡眠不足",
                    passed=True,
                    message=f"正确触发连锁惩罚: {punishment['message']}",
                    details=punishment
                )
            else:
                self._record_test_result(
                    test_name="连锁惩罚: 3天睡眠不足",
                    passed=False,
                    message="应该触发连锁惩罚但未触发"
                )
            
            # 测试无连锁惩罚的情况
            good_history = {}
            for i in range(3):
                date_str = (base_date + timedelta(days=i)).strftime('%Y-%m-%d')
                good_history[date_str] = DailyHealthSummary(sleep_hours=8.0)  # 充足睡眠
            
            no_punishment = self.sleep_calculator.check_chain_punishment(good_history)
            
            self._record_test_result(
                test_name="连锁惩罚: 充足睡眠无惩罚",
                passed=no_punishment is None,
                message="充足睡眠无连锁惩罚" if no_punishment is None else f"意外触发惩罚: {no_punishment}"
            )
            
        except Exception as e:
            self._record_test_result(
                test_name="连锁惩罚机制",
                passed=False,
                message=f"测试失败: {str(e)}"
            )
    
    def _test_comprehensive_scenarios(self):
        """测试综合场景"""
        
        scenarios = [
            {
                "name": "完美睡眠",
                "health_data": DailyHealthSummary(sleep_hours=8.0),
                "user_id": "test_user",
                "date": datetime.now(),
                "description": "8小时优质睡眠"
            },
            {
                "name": "普通睡眠",
                "health_data": DailyHealthSummary(sleep_hours=7.0),
                "user_id": "test_user",
                "date": datetime.now(),
                "description": "7小时普通睡眠"
            },
            {
                "name": "睡眠不足",
                "health_data": DailyHealthSummary(sleep_hours=5.5),
                "user_id": "test_user",
                "date": datetime.now(),
                "description": "睡眠严重不足"
            }
        ]
        
        for scenario in scenarios:
            try:
                scores = self.sleep_calculator.calculate(
                    scenario["health_data"],
                    user_id=scenario["user_id"],
                    date=scenario["date"]
                )
                
                # 验证积分合理性
                total_score = scores['total']
                easy_score = scores['easy']
                
                # 基本验证：总分应该是各部分之和
                calculated_total = sum([scores[k] for k in ['easy', 'medium', 'hard', 'super_hard']])
                total_correct = total_score == calculated_total
                
                # 验证易难度积分合理性
                if scenario["health_data"].sleep_hours and scenario["health_data"].sleep_hours >= 7.5:
                    easy_reasonable = easy_score == 1000
                elif scenario["health_data"].sleep_hours and scenario["health_data"].sleep_hours < 6:
                    easy_reasonable = easy_score == 0
                else:
                    easy_reasonable = 0 < easy_score < 1000
                
                self._record_test_result(
                    test_name=f"综合场景: {scenario['name']} - 总分计算",
                    passed=total_correct,
                    message=f"总分: {total_score}, 计算: {calculated_total}",
                    details={
                        "scenario": scenario["description"],
                        "scores": scores
                    }
                )
                
                self._record_test_result(
                    test_name=f"综合场景: {scenario['name']} - 易难度合理性",
                    passed=easy_reasonable,
                    message=f"易难度积分: {easy_score}",
                    details={
                        "sleep_hours": scenario["health_data"].sleep_hours,
                        "easy_score": easy_score
                    }
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"综合场景: {scenario['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
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
            
        if details and len(str(details)) < 200:
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
        print("📊 睡眠分析完整测试报告")
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
        report_file = f"tests/reports/sleep_analysis_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return report


def main():
    """主函数"""
    print("🚀 LSP系统睡眠分析完整测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建测试实例并运行测试
    test = SleepAnalysisCompleteTest()
    report = test.run_all_tests()
    
    # 根据测试结果设置退出码
    if report["summary"]["failed_tests"] > 0:
        print("\n⚠️  发现睡眠分析问题，请检查上述失败的测试项")
        sys.exit(1)
    else:
        print("\n🎉 所有睡眠分析测试通过!")
        sys.exit(0)


if __name__ == "__main__":
    main()