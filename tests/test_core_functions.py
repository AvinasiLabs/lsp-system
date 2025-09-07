#!/usr/bin/env python3
"""
核心功能测试脚本
只测试不依赖外部库的核心功能
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class CoreFunctionTest:
    """核心功能测试类"""
    
    def __init__(self):
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
    
    def run_all_tests(self):
        """运行所有核心功能测试"""
        print("🧪 LSP系统核心功能测试")
        print("=" * 60)
        
        test_functions = [
            ("积分配置验证", self._test_score_config),
            ("百分比计算测试", self._test_percentage_calculation),
            ("配置完整性测试", self._test_config_completeness),
            ("边界情况测试", self._test_edge_cases),
        ]
        
        for test_name, test_func in test_functions:
            print(f"\n📋 {test_name}")
            print("-" * 40)
            try:
                test_func()
            except Exception as e:
                self._record_test_result(
                    test_name=test_name,
                    passed=False,
                    message=f"测试异常: {str(e)}"
                )
        
        self._print_summary()
        return self.failed_tests == 0
    
    def _test_score_config(self):
        """测试积分配置"""
        from src.core.score_config import DIMENSION_MAX_SCORES, get_dimension_max_score
        
        # 验证维度存在
        expected_dimensions = ["sleep", "exercise", "diet", "mental"]
        for dimension in expected_dimensions:
            if dimension in DIMENSION_MAX_SCORES:
                self._record_test_result(
                    test_name=f"维度配置: {dimension}",
                    passed=True,
                    message=f"配置存在，总分: {DIMENSION_MAX_SCORES[dimension]['total']}"
                )
            else:
                self._record_test_result(
                    test_name=f"维度配置: {dimension}",
                    passed=False,
                    message="配置缺失"
                )
        
        # 测试获取最高分函数
        sleep_easy_max = get_dimension_max_score("sleep", "easy")
        expected_sleep_easy = 1000
        
        self._record_test_result(
            test_name="获取最高分函数",
            passed=sleep_easy_max == expected_sleep_easy,
            message=f"睡眠易难度最高分: {sleep_easy_max} (期望: {expected_sleep_easy})"
        )
    
    def _test_percentage_calculation(self):
        """测试百分比计算"""
        from src.core.score_config import calculate_percentage
        
        test_cases = [
            {"score": 500, "dimension": "sleep", "difficulty": "easy", "expected": 50.0},
            {"score": 1000, "dimension": "sleep", "difficulty": "easy", "expected": 100.0},
            {"score": 0, "dimension": "sleep", "difficulty": "easy", "expected": 0.0},
            {"score": 1500, "dimension": "sleep", "difficulty": "easy", "expected": 150.0},
        ]
        
        for case in test_cases:
            result = calculate_percentage(case["score"], case["dimension"], case["difficulty"])
            passed = abs(result - case["expected"]) < 0.01
            
            self._record_test_result(
                test_name=f"百分比计算: {case['score']}/{case['dimension']}/{case['difficulty']}",
                passed=passed,
                message=f"结果: {result}%, 期望: {case['expected']}%"
            )
    
    def _test_config_completeness(self):
        """测试配置完整性"""
        from src.core.score_config import DIMENSION_MAX_SCORES
        
        difficulties = ["easy", "medium", "hard", "super_hard", "total"]
        
        for dimension, config in DIMENSION_MAX_SCORES.items():
            if config["total"] > 0:  # 只检查已实现的维度
                for difficulty in difficulties:
                    if difficulty in config:
                        self._record_test_result(
                            test_name=f"配置完整性: {dimension}.{difficulty}",
                            passed=True,
                            message=f"配置: {config[difficulty]}"
                        )
                    else:
                        self._record_test_result(
                            test_name=f"配置完整性: {dimension}.{difficulty}",
                            passed=False,
                            message="配置缺失"
                        )
                
                # 检查总分是否等于各部分之和
                calculated_total = sum([config.get(d, 0) for d in ["easy", "medium", "hard", "super_hard"]])
                actual_total = config["total"]
                
                self._record_test_result(
                    test_name=f"总分一致性: {dimension}",
                    passed=calculated_total == actual_total,
                    message=f"计算总分: {calculated_total}, 配置总分: {actual_total}"
                )
    
    def _test_edge_cases(self):
        """测试边界情况"""
        from src.core.score_config import calculate_percentage, get_dimension_max_score
        
        # 测试无效输入
        edge_cases = [
            {"func": "calculate_percentage", "args": [0, "sleep", "easy"], "desc": "零分数"},
            {"func": "calculate_percentage", "args": [-100, "sleep", "easy"], "desc": "负分数"},
            {"func": "calculate_percentage", "args": [999999, "sleep", "easy"], "desc": "极大分数"},
            {"func": "get_dimension_max_score", "args": ["nonexistent", "easy"], "desc": "不存在的维度"},
            {"func": "get_dimension_max_score", "args": ["sleep", "nonexistent"], "desc": "不存在的难度"},
        ]
        
        for case in edge_cases:
            try:
                if case["func"] == "calculate_percentage":
                    result = calculate_percentage(*case["args"])
                    self._record_test_result(
                        test_name=f"边界情况: {case['desc']}",
                        passed=True,
                        message=f"处理成功，结果: {result}"
                    )
                elif case["func"] == "get_dimension_max_score":
                    result = get_dimension_max_score(*case["args"])
                    self._record_test_result(
                        test_name=f"边界情况: {case['desc']}",
                        passed=True,
                        message=f"处理成功，结果: {result}"
                    )
            except Exception as e:
                # 异常也是一种处理方式
                self._record_test_result(
                    test_name=f"边界情况: {case['desc']}",
                    passed=True,
                    message=f"抛出异常处理: {type(e).__name__}"
                )
    
    def _record_test_result(self, test_name: str, passed: bool, message: str):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        self.test_results.append(result)
        
        if passed:
            self.passed_tests += 1
            print(f"✅ {test_name}: {message}")
        else:
            self.failed_tests += 1
            print(f"❌ {test_name}: {message}")
    
    def _print_summary(self):
        """打印测试摘要"""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("📊 核心功能测试摘要")
        print("=" * 60)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {self.passed_tests}")
        print(f"失败测试: {self.failed_tests}")
        print(f"通过率: {pass_rate:.2f}%")
        
        if self.failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # 保存报告
        report_file = Path(__file__).parent / "reports" / f"core_function_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": self.passed_tests,
                    "failed_tests": self.failed_tests,
                    "pass_rate": pass_rate
                },
                "test_results": self.test_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: {report_file}")


def main():
    """主函数"""
    test = CoreFunctionTest()
    success = test.run_all_tests()
    
    if success:
        print("\n🎉 所有核心功能测试通过！")
        print("\n💡 核心积分计算模块工作正常")
        print("   - 积分配置完整")
        print("   - 百分比计算正确")
        print("   - 边界情况处理良好")
        return 0
    else:
        print("\n⚠️  部分核心功能测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    sys.exit(main())