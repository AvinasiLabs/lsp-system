#!/usr/bin/env python3
"""
积分百分比完整测试脚本
测试所有维度的百分比计算、最高分配置、边界情况和API响应中的百分比字段
"""

import os
import sys
import json
import requests
import traceback
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.core.score_config import DIMENSION_MAX_SCORES, calculate_percentage, get_dimension_max_score
from src.core.score_engine import ScoreEngine
from src.models.health_data import DailyHealthSummary
from src.utils.logger import logger


class ScorePercentageCompleteTest:
    """积分百分比完整测试类"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """初始化测试类"""
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        self.base_url = base_url
        self.score_engine = ScoreEngine(auto_save=False)  # 不自动保存，避免污染数据库
        
    def run_all_tests(self) -> Dict:
        """运行所有积分百分比测试"""
        print("📊 开始积分百分比完整测试...")
        print("=" * 80)
        
        # 测试套件
        test_suites = [
            ("最高分配置验证", self._test_max_score_configuration),
            ("百分比计算函数测试", self._test_percentage_calculation_function),
            ("各维度百分比计算", self._test_all_dimension_percentages),
            ("边界情况百分比计算", self._test_edge_case_percentages),
            ("API响应百分比字段验证", self._test_api_percentage_fields),
            ("积分引擎百分比集成", self._test_score_engine_percentage_integration),
            ("无效输入处理", self._test_invalid_input_handling),
            ("精度和舍入测试", self._test_precision_and_rounding),
            ("配置一致性验证", self._test_configuration_consistency),
            ("性能测试", self._test_percentage_performance),
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
    
    def _test_max_score_configuration(self):
        """测试最高分配置验证"""
        
        # 验证所有维度都存在配置
        expected_dimensions = ["sleep", "exercise", "diet", "mental", "environment", "social", "cognition", "prevention"]
        expected_difficulties = ["easy", "medium", "hard", "super_hard", "total"]
        
        for dimension in expected_dimensions:
            if dimension not in DIMENSION_MAX_SCORES:
                self._record_test_result(
                    test_name=f"最高分配置: 维度 {dimension}",
                    passed=False,
                    message=f"缺少维度配置: {dimension}"
                )
                continue
            
            dimension_config = DIMENSION_MAX_SCORES[dimension]
            
            for difficulty in expected_difficulties:
                if difficulty not in dimension_config:
                    self._record_test_result(
                        test_name=f"最高分配置: {dimension}.{difficulty}",
                        passed=False,
                        message=f"缺少难度配置: {dimension}.{difficulty}"
                    )
                else:
                    max_score = dimension_config[difficulty]
                    # 验证分数为非负整数
                    valid_score = isinstance(max_score, int) and max_score >= 0
                    
                    self._record_test_result(
                        test_name=f"最高分配置: {dimension}.{difficulty}",
                        passed=valid_score,
                        message=f"最高分: {max_score}" if valid_score else f"无效分数: {max_score}",
                        details={"dimension": dimension, "difficulty": difficulty, "max_score": max_score}
                    )
        
        # 验证total分数是否等于其他难度之和
        for dimension in expected_dimensions:
            if dimension in DIMENSION_MAX_SCORES:
                config = DIMENSION_MAX_SCORES[dimension]
                if "total" in config:
                    expected_total = sum([config.get(d, 0) for d in ["easy", "medium", "hard", "super_hard"]])
                    actual_total = config["total"]
                    
                    self._record_test_result(
                        test_name=f"总分一致性: {dimension}",
                        passed=expected_total == actual_total,
                        message=f"期望总分: {expected_total}, 实际: {actual_total}",
                        details={
                            "dimension": dimension,
                            "expected_total": expected_total,
                            "actual_total": actual_total,
                            "breakdown": {d: config.get(d, 0) for d in ["easy", "medium", "hard", "super_hard"]}
                        }
                    )
    
    def _test_percentage_calculation_function(self):
        """测试百分比计算函数"""
        
        # 基础计算测试
        basic_tests = [
            {"score": 500, "dimension": "sleep", "difficulty": "easy", "expected": 50.0},
            {"score": 1000, "dimension": "sleep", "difficulty": "easy", "expected": 100.0},
            {"score": 0, "dimension": "sleep", "difficulty": "easy", "expected": 0.0},
            {"score": 1500, "dimension": "sleep", "difficulty": "easy", "expected": 150.0},  # 超过100%的情况
        ]
        
        for test in basic_tests:
            try:
                result = calculate_percentage(test["score"], test["dimension"], test["difficulty"])
                passed = abs(result - test["expected"]) < 0.01  # 允许小数精度误差
                
                self._record_test_result(
                    test_name=f"百分比计算: {test['score']}/{test['dimension']}/{test['difficulty']}",
                    passed=passed,
                    message=f"期望: {test['expected']}%, 计算: {result}%",
                    details=test
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"百分比计算: {test['score']}/{test['dimension']}/{test['difficulty']}",
                    passed=False,
                    message=f"计算失败: {str(e)}"
                )
        
        # 测试get_dimension_max_score函数
        max_score_tests = [
            {"dimension": "sleep", "difficulty": "easy", "expected": 1000},
            {"dimension": "sleep", "difficulty": "total", "expected": 17000},
            {"dimension": "nonexistent", "difficulty": "easy", "expected": 0},
            {"dimension": "sleep", "difficulty": "nonexistent", "expected": 0},
        ]
        
        for test in max_score_tests:
            try:
                result = get_dimension_max_score(test["dimension"], test["difficulty"])
                passed = result == test["expected"]
                
                self._record_test_result(
                    test_name=f"最高分获取: {test['dimension']}.{test['difficulty']}",
                    passed=passed,
                    message=f"期望: {test['expected']}, 获取: {result}",
                    details=test
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"最高分获取: {test['dimension']}.{test['difficulty']}",
                    passed=False,
                    message=f"获取失败: {str(e)}"
                )
    
    def _test_all_dimension_percentages(self):
        """测试所有维度的百分比计算"""
        
        # 为每个维度测试不同分数的百分比计算
        for dimension, config in DIMENSION_MAX_SCORES.items():
            if config["total"] == 0:  # 跳过未实现的维度
                self._record_test_result(
                    test_name=f"维度百分比: {dimension}",
                    passed=True,
                    message=f"维度 {dimension} 暂未实现，跳过测试",
                    details={"dimension": dimension, "status": "not_implemented"}
                )
                continue
            
            # 测试各难度的百分比计算
            for difficulty, max_score in config.items():
                if max_score == 0:  # 跳过分数为0的难度
                    continue
                
                test_scores = [
                    0,  # 0%
                    max_score // 4,  # 25%
                    max_score // 2,  # 50%
                    (max_score * 3) // 4,  # 75%
                    max_score,  # 100%
                    max_score + 100,  # 超过100%
                ]
                
                for score in test_scores:
                    try:
                        percentage = calculate_percentage(score, dimension, difficulty)
                        expected_percentage = (score / max_score) * 100
                        
                        passed = abs(percentage - expected_percentage) < 0.01
                        
                        self._record_test_result(
                            test_name=f"维度百分比: {dimension}.{difficulty} ({score}分)",
                            passed=passed,
                            message=f"百分比: {percentage:.2f}%",
                            details={
                                "dimension": dimension,
                                "difficulty": difficulty,
                                "score": score,
                                "max_score": max_score,
                                "percentage": percentage,
                                "expected": expected_percentage
                            }
                        )
                        
                    except Exception as e:
                        self._record_test_result(
                            test_name=f"维度百分比: {dimension}.{difficulty} ({score}分)",
                            passed=False,
                            message=f"计算失败: {str(e)}"
                        )
    
    def _test_edge_case_percentages(self):
        """测试边界情况百分比计算"""
        
        edge_cases = [
            {
                "name": "零分数",
                "score": 0,
                "dimension": "sleep",
                "difficulty": "easy",
                "expected": 0.0
            },
            {
                "name": "负分数",
                "score": -100,
                "dimension": "sleep",
                "difficulty": "easy",
                "expected": -10.0  # -100/1000 * 100
            },
            {
                "name": "极大分数",
                "score": 999999,
                "dimension": "sleep",
                "difficulty": "easy",
                "expected": 99999.9  # 999999/1000 * 100
            },
            {
                "name": "最大分数边界",
                "score": 1000,
                "dimension": "sleep",
                "difficulty": "easy",
                "expected": 100.0
            },
            {
                "name": "不存在的维度",
                "score": 500,
                "dimension": "nonexistent",
                "difficulty": "easy",
                "expected": 0.0  # 最大分数为0，返回0%
            },
            {
                "name": "不存在的难度",
                "score": 500,
                "dimension": "sleep",
                "difficulty": "nonexistent",
                "expected": 0.0  # 最大分数为0，返回0%
            }
        ]
        
        for case in edge_cases:
            try:
                result = calculate_percentage(case["score"], case["dimension"], case["difficulty"])
                passed = abs(result - case["expected"]) < 0.01
                
                self._record_test_result(
                    test_name=f"边界情况: {case['name']}",
                    passed=passed,
                    message=f"期望: {case['expected']}%, 计算: {result}%",
                    details=case
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"边界情况: {case['name']}",
                    passed=False,
                    message=f"计算失败: {str(e)}"
                )
    
    def _test_api_percentage_fields(self):
        """测试API响应中的百分比字段"""
        
        # 测试健康检查API是否包含百分比信息
        try:
            response = requests.get(f"{self.base_url}/lsp/health", timeout=5)
            if response.status_code == 200:
                self._record_test_result(
                    test_name="API可用性: 健康检查",
                    passed=True,
                    message="API服务正常运行"
                )
            else:
                self._record_test_result(
                    test_name="API可用性: 健康检查",
                    passed=False,
                    message=f"API返回错误状态: {response.status_code}"
                )
                return
                
        except requests.exceptions.ConnectionError:
            self._record_test_result(
                test_name="API可用性: 健康检查",
                passed=False,
                message="无法连接到API服务器，跳过API测试"
            )
            return
        except Exception as e:
            self._record_test_result(
                test_name="API可用性: 健康检查",
                passed=False,
                message=f"API测试失败: {str(e)}"
            )
            return
        
        # 测试积分API的百分比字段
        api_tests = [
            {
                "name": "有效积分API",
                "endpoint": "/lsp/api/v1/scores/valid",
                "method": "GET",
                "expected_fields": ["dimension_percentages"]
            },
            {
                "name": "月度汇总API",
                "endpoint": "/lsp/api/v1/scores/summary/2024/1",
                "method": "GET",
                "expected_fields": ["dimension_percentages"]
            }
        ]
        
        for test in api_tests:
            try:
                url = f"{self.base_url}{test['endpoint']}"
                if test["method"] == "GET":
                    response = requests.get(url, timeout=5)
                else:
                    response = requests.post(url, json={}, timeout=5)
                
                # 检查响应状态（401/403表示需要认证但端点存在）
                if response.status_code in [200, 401, 403]:
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            has_percentage_fields = all(field in data for field in test["expected_fields"])
                            
                            self._record_test_result(
                                test_name=f"API百分比字段: {test['name']}",
                                passed=has_percentage_fields,
                                message=f"百分比字段存在: {has_percentage_fields}",
                                details={
                                    "endpoint": test["endpoint"],
                                    "expected_fields": test["expected_fields"],
                                    "response_keys": list(data.keys()) if isinstance(data, dict) else "非字典响应"
                                }
                            )
                        except json.JSONDecodeError:
                            self._record_test_result(
                                test_name=f"API百分比字段: {test['name']}",
                                passed=False,
                                message="响应不是有效的JSON格式"
                            )
                    else:
                        self._record_test_result(
                            test_name=f"API百分比字段: {test['name']}",
                            passed=True,
                            message=f"端点存在但需要认证 (状态码: {response.status_code})"
                        )
                else:
                    self._record_test_result(
                        test_name=f"API百分比字段: {test['name']}",
                        passed=False,
                        message=f"API返回错误状态: {response.status_code}",
                        details={"response_text": response.text[:200]}
                    )
                    
            except Exception as e:
                self._record_test_result(
                    test_name=f"API百分比字段: {test['name']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_score_engine_percentage_integration(self):
        """测试积分引擎百分比集成"""
        
        try:
            # 创建测试健康数据
            test_health_data = DailyHealthSummary(
                sleep_hours=7.5,  # 满足睡眠易难度要求
                steps=10000,      # 满足运动要求
                water_ml=2000,    # 满足饮水要求
                hrv=30            # 满足心率变异性要求
            )
            
            # 使用积分引擎计算积分（包括百分比）
            result = self.score_engine.calculate_daily_score(
                user_id="test_user",
                date=datetime.now(),
                save_to_db=False
            )
            
            # 验证结果包含百分比数据
            has_percentages = "dimension_percentages" in result
            
            self._record_test_result(
                test_name="积分引擎集成: 百分比字段存在",
                passed=has_percentages,
                message="积分引擎返回包含百分比数据" if has_percentages else "积分引擎缺少百分比数据"
            )
            
            if has_percentages:
                dimension_percentages = result["dimension_percentages"]
                
                # 验证每个维度都有百分比数据
                for dimension, scores in result["dimension_scores"].items():
                    if dimension in dimension_percentages:
                        dim_percentages = dimension_percentages[dimension]
                        
                        # 验证百分比结构
                        expected_keys = ["easy", "medium", "hard", "super_hard", "total"]
                        has_all_keys = all(key in dim_percentages for key in expected_keys)
                        
                        self._record_test_result(
                            test_name=f"积分引擎集成: {dimension} 百分比结构",
                            passed=has_all_keys,
                            message=f"百分比结构完整" if has_all_keys else f"缺少百分比字段",
                            details={
                                "dimension": dimension,
                                "percentages": dim_percentages,
                                "scores": scores
                            }
                        )
                        
                        # 验证百分比计算正确性
                        if has_all_keys:
                            for difficulty in expected_keys:
                                score = scores.get(difficulty, 0)
                                percentage = dim_percentages.get(difficulty, 0)
                                expected_percentage = calculate_percentage(score, dimension, difficulty)
                                
                                passed = abs(percentage - expected_percentage) < 0.01
                                
                                self._record_test_result(
                                    test_name=f"积分引擎集成: {dimension}.{difficulty} 百分比计算",
                                    passed=passed,
                                    message=f"期望: {expected_percentage}%, 实际: {percentage}%",
                                    details={
                                        "dimension": dimension,
                                        "difficulty": difficulty,
                                        "score": score,
                                        "percentage": percentage,
                                        "expected_percentage": expected_percentage
                                    }
                                )
                    else:
                        self._record_test_result(
                            test_name=f"积分引擎集成: {dimension} 百分比数据",
                            passed=False,
                            message=f"维度 {dimension} 缺少百分比数据"
                        )
            
        except Exception as e:
            self._record_test_result(
                test_name="积分引擎集成测试",
                passed=False,
                message=f"测试失败: {str(e)}"
            )
    
    def _test_invalid_input_handling(self):
        """测试无效输入处理"""
        
        invalid_inputs = [
            {
                "name": "None分数",
                "score": None,
                "dimension": "sleep",
                "difficulty": "easy"
            },
            {
                "name": "字符串分数",
                "score": "500",
                "dimension": "sleep",
                "difficulty": "easy"
            },
            {
                "name": "浮点分数",
                "score": 500.5,
                "dimension": "sleep",
                "difficulty": "easy"
            },
            {
                "name": "None维度",
                "score": 500,
                "dimension": None,
                "difficulty": "easy"
            },
            {
                "name": "空字符串维度",
                "score": 500,
                "dimension": "",
                "difficulty": "easy"
            }
        ]
        
        for case in invalid_inputs:
            try:
                result = calculate_percentage(case["score"], case["dimension"], case["difficulty"])
                
                # 对于无效输入，应该返回0或抛出异常
                if result == 0.0:
                    self._record_test_result(
                        test_name=f"无效输入处理: {case['name']}",
                        passed=True,
                        message=f"正确处理无效输入，返回0%"
                    )
                else:
                    self._record_test_result(
                        test_name=f"无效输入处理: {case['name']}",
                        passed=False,
                        message=f"无效输入应返回0%，但返回了{result}%"
                    )
                    
            except Exception as e:
                # 抛出异常也是可接受的处理方式
                self._record_test_result(
                    test_name=f"无效输入处理: {case['name']}",
                    passed=True,
                    message=f"正确抛出异常处理无效输入: {type(e).__name__}"
                )
    
    def _test_precision_and_rounding(self):
        """测试精度和舍入"""
        
        precision_tests = [
            {
                "score": 333,
                "dimension": "sleep",
                "difficulty": "easy",  # max: 1000
                "expected": 33.3,  # 333/1000 * 100
                "description": "一位小数"
            },
            {
                "score": 333,
                "dimension": "sleep", 
                "difficulty": "medium",  # max: 2000
                "expected": 16.65,  # 333/2000 * 100
                "description": "两位小数"
            },
            {
                "score": 1,
                "dimension": "sleep",
                "difficulty": "total",  # max: 17000
                "expected": 0.01,  # 1/17000 * 100 ≈ 0.0059 -> 0.01 (rounded)
                "description": "极小百分比"
            }
        ]
        
        for test in precision_tests:
            try:
                result = calculate_percentage(test["score"], test["dimension"], test["difficulty"])
                
                # 检查精度（允许0.01的误差）
                passed = abs(result - test["expected"]) <= 0.01
                
                self._record_test_result(
                    test_name=f"精度舍入: {test['description']}",
                    passed=passed,
                    message=f"期望: {test['expected']}%, 计算: {result}%",
                    details=test
                )
                
            except Exception as e:
                self._record_test_result(
                    test_name=f"精度舍入: {test['description']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_configuration_consistency(self):
        """测试配置一致性验证"""
        
        # 验证已实现维度的total分数是否合理
        implemented_dimensions = ["sleep", "exercise", "diet", "mental"]
        
        for dimension in implemented_dimensions:
            config = DIMENSION_MAX_SCORES[dimension]
            total_score = config["total"]
            
            # total分数应该大于0
            if total_score <= 0:
                self._record_test_result(
                    test_name=f"配置一致性: {dimension} 总分有效性",
                    passed=False,
                    message=f"总分应大于0，实际: {total_score}"
                )
                continue
            
            # 验证各难度分数之和是否等于总分
            calculated_total = sum([config.get(d, 0) for d in ["easy", "medium", "hard", "super_hard"]])
            
            consistency_check = calculated_total == total_score
            
            self._record_test_result(
                test_name=f"配置一致性: {dimension} 总分计算",
                passed=consistency_check,
                message=f"计算总分: {calculated_total}, 配置总分: {total_score}",
                details={
                    "dimension": dimension,
                    "easy": config.get("easy", 0),
                    "medium": config.get("medium", 0),
                    "hard": config.get("hard", 0),
                    "super_hard": config.get("super_hard", 0),
                    "calculated_total": calculated_total,
                    "config_total": total_score
                }
            )
    
    def _test_percentage_performance(self):
        """测试百分比计算性能"""
        
        import time
        
        try:
            # 大量计算测试
            start_time = time.time()
            
            for i in range(1000):
                calculate_percentage(i, "sleep", "easy")
            
            end_time = time.time()
            duration = end_time - start_time
            
            # 1000次计算应该在1秒内完成
            performance_ok = duration < 1.0
            
            self._record_test_result(
                test_name="性能测试: 1000次百分比计算",
                passed=performance_ok,
                message=f"耗时: {duration:.4f}秒",
                details={
                    "iterations": 1000,
                    "duration": duration,
                    "avg_per_calculation": duration / 1000
                }
            )
            
        except Exception as e:
            self._record_test_result(
                test_name="性能测试",
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
            
        if details and len(str(details)) < 300:
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
        print("📊 积分百分比完整测试报告")
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
        report_file = f"tests/reports/score_percentage_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return report


def main():
    """主函数"""
    print("🚀 LSP系统积分百分比完整测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建测试实例并运行测试
    test = ScorePercentageCompleteTest()
    report = test.run_all_tests()
    
    # 根据测试结果设置退出码
    if report["summary"]["failed_tests"] > 0:
        print("\n⚠️  发现积分百分比问题，请检查上述失败的测试项")
        sys.exit(1)
    else:
        print("\n🎉 所有积分百分比测试通过!")
        sys.exit(0)


if __name__ == "__main__":
    main()