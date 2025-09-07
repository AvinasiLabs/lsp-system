#!/usr/bin/env python3
"""
文档验证测试脚本
验证所有文档中描述的API是否存在并正常工作，检查代码示例是否可执行
"""

import os
import sys
import json
import requests
import traceback
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import subprocess
import importlib.util

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from src.db.configs.global_config import API_CONFIG
from src.core.score_config import DIMENSION_MAX_SCORES, calculate_percentage
from src.utils.logger import logger

class DocumentationValidator:
    """文档验证器 - 验证文档描述与实际代码的一致性"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        初始化验证器
        
        Args:
            base_url: API基础URL
        """
        self.base_url = base_url
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_all_tests(self) -> Dict:
        """
        运行所有文档验证测试
        
        Returns:
            测试结果汇总
        """
        print("🧪 开始文档验证测试...")
        print("=" * 80)
        
        # 测试套件
        test_suites = [
            ("API端点存在性验证", self._test_api_endpoints_exist),
            ("API响应格式验证", self._test_api_response_formats),
            ("配置一致性验证", self._test_config_consistency),
            ("代码示例可执行性验证", self._test_code_examples),
            ("数据库表结构验证", self._test_database_schema),
            ("环境变量配置验证", self._test_environment_config),
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
    
    def _test_api_endpoints_exist(self):
        """测试文档中提到的所有API端点是否存在"""
        
        # 从文档中提取的API端点列表
        documented_endpoints = [
            {
                "method": "GET",
                "path": "/lsp/health",
                "description": "健康检查端点"
            },
            {
                "method": "GET", 
                "path": "/lsp/api/v1/scores/valid",
                "description": "获取用户当前有效积分"
            },
            {
                "method": "GET",
                "path": "/lsp/api/v1/scores/history",
                "description": "获取积分历史记录"
            },
            {
                "method": "GET",
                "path": "/lsp/api/v1/scores/expiring",
                "description": "获取即将过期的积分"
            },
            {
                "method": "GET",
                "path": "/lsp/api/v1/scores/tier-stats",
                "description": "获取用户等级统计"
            },
            {
                "method": "POST",
                "path": "/lsp/api/v1/scores/check-expiration",
                "description": "检查并标记过期积分"
            },
            {
                "method": "GET",
                "path": "/lsp/api/v1/scores/summary/{year}/{month}",
                "description": "获取月度积分汇总"
            }
        ]
        
        for endpoint in documented_endpoints:
            path = endpoint["path"].replace("{year}", "2024").replace("{month}", "1")
            url = f"{self.base_url}{path}"
            
            try:
                if endpoint["method"] == "GET":
                    response = requests.get(url, timeout=5)
                elif endpoint["method"] == "POST":
                    response = requests.post(url, json={}, timeout=5)
                else:
                    self._record_test_result(
                        test_name=f"API端点存在性: {endpoint['method']} {endpoint['path']}",
                        passed=False,
                        message=f"不支持的HTTP方法: {endpoint['method']}"
                    )
                    continue
                
                # 检查响应状态
                # 401/403表示需要认证但端点存在
                # 400表示参数错误但端点存在
                # 404表示端点不存在
                if response.status_code == 404:
                    self._record_test_result(
                        test_name=f"API端点存在性: {endpoint['method']} {endpoint['path']}",
                        passed=False,
                        message=f"端点不存在 (404)",
                        details={"response_text": response.text[:200]}
                    )
                else:
                    self._record_test_result(
                        test_name=f"API端点存在性: {endpoint['method']} {endpoint['path']}",
                        passed=True,
                        message=f"端点存在 (状态码: {response.status_code})",
                        details={"status_code": response.status_code}
                    )
                    
            except requests.exceptions.ConnectionError:
                self._record_test_result(
                    test_name=f"API端点存在性: {endpoint['method']} {endpoint['path']}",
                    passed=False,
                    message="无法连接到服务器，请确保API服务器正在运行",
                    details={"base_url": self.base_url}
                )
            except Exception as e:
                self._record_test_result(
                    test_name=f"API端点存在性: {endpoint['method']} {endpoint['path']}",
                    passed=False,
                    message=f"测试失败: {str(e)}"
                )
    
    def _test_api_response_formats(self):
        """测试API响应格式是否符合文档描述"""
        
        # 测试健康检查API的响应格式
        try:
            response = requests.get(f"{self.base_url}/lsp/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                # 验证响应字段
                expected_fields = ["status", "timestamp", "version", "database_status"]
                missing_fields = []
                for field in expected_fields:
                    if field not in data:
                        missing_fields.append(field)
                
                if missing_fields:
                    self._record_test_result(
                        test_name="API响应格式: 健康检查",
                        passed=False,
                        message=f"响应缺少字段: {missing_fields}",
                        details={"response": data}
                    )
                else:
                    self._record_test_result(
                        test_name="API响应格式: 健康检查",
                        passed=True,
                        message="响应格式正确",
                        details={"response": data}
                    )
            else:
                self._record_test_result(
                    test_name="API响应格式: 健康检查",
                    passed=False,
                    message=f"API返回错误状态码: {response.status_code}"
                )
                
        except requests.exceptions.ConnectionError:
            self._record_test_result(
                test_name="API响应格式: 健康检查",
                passed=False,
                message="无法连接到服务器"
            )
        except Exception as e:
            self._record_test_result(
                test_name="API响应格式: 健康检查",
                passed=False,
                message=f"测试失败: {str(e)}"
            )
    
    def _test_config_consistency(self):
        """测试配置文件与文档描述的一致性"""
        
        # 测试积分配置是否与文档一致
        try:
            # 验证DIMENSION_MAX_SCORES的结构
            documented_dimensions = ["sleep", "exercise", "diet", "mental", "environment", "social", "cognition", "prevention"]
            documented_difficulties = ["easy", "medium", "hard", "super_hard", "total"]
            
            for dimension in documented_dimensions:
                if dimension not in DIMENSION_MAX_SCORES:
                    self._record_test_result(
                        test_name=f"配置一致性: 维度 {dimension}",
                        passed=False,
                        message=f"配置中缺少维度: {dimension}"
                    )
                    continue
                
                for difficulty in documented_difficulties:
                    if difficulty not in DIMENSION_MAX_SCORES[dimension]:
                        self._record_test_result(
                            test_name=f"配置一致性: {dimension}.{difficulty}",
                            passed=False,
                            message=f"配置中缺少难度级别: {dimension}.{difficulty}"
                        )
                    else:
                        self._record_test_result(
                            test_name=f"配置一致性: {dimension}.{difficulty}",
                            passed=True,
                            message=f"配置存在，最高分: {DIMENSION_MAX_SCORES[dimension][difficulty]}"
                        )
        
        except Exception as e:
            self._record_test_result(
                test_name="配置一致性验证",
                passed=False,
                message=f"测试失败: {str(e)}"
            )
    
    def _test_code_examples(self):
        """测试文档中的代码示例是否可执行"""
        
        # 测试百分比计算示例
        try:
            # 文档中的示例代码
            actual_score = 500
            dimension = "sleep"
            difficulty = "easy"
            
            percentage = calculate_percentage(actual_score, dimension, difficulty)
            
            # 验证计算结果合理性
            if 0 <= percentage <= 100:
                self._record_test_result(
                    test_name="代码示例: calculate_percentage函数",
                    passed=True,
                    message=f"百分比计算正确: {percentage}%",
                    details={"input": {"score": actual_score, "dimension": dimension, "difficulty": difficulty}, "output": percentage}
                )
            else:
                self._record_test_result(
                    test_name="代码示例: calculate_percentage函数",
                    passed=False,
                    message=f"百分比计算结果异常: {percentage}%"
                )
                
        except Exception as e:
            self._record_test_result(
                test_name="代码示例: calculate_percentage函数",
                passed=False,
                message=f"代码示例执行失败: {str(e)}"
            )
        
        # 测试导入语句示例
        import_examples = [
            "from src.core.score_config import DIMENSION_MAX_SCORES, calculate_percentage",
            "from src.db.postgresql import POSTGRES_POOL",
            "from src.services.score_persistence_service import ScorePersistenceService",
            "from src.core.score_engine import ScoreEngine",
        ]
        
        for import_example in import_examples:
            try:
                exec(import_example)
                self._record_test_result(
                    test_name=f"代码示例: 导入语句 - {import_example.split('import')[1].strip()}",
                    passed=True,
                    message="导入成功"
                )
            except Exception as e:
                self._record_test_result(
                    test_name=f"代码示例: 导入语句 - {import_example.split('import')[1].strip()}",
                    passed=False,
                    message=f"导入失败: {str(e)}"
                )
    
    def _test_database_schema(self):
        """测试数据库表结构是否与文档描述一致"""
        
        # 这里只验证配置是否可以加载，实际数据库连接测试需要数据库运行
        try:
            from src.db.postgresql import POSTGRES_POOL
            self._record_test_result(
                test_name="数据库配置: POSTGRES_POOL导入",
                passed=True,
                message="数据库连接池配置加载成功"
            )
        except Exception as e:
            self._record_test_result(
                test_name="数据库配置: POSTGRES_POOL导入",
                passed=False,
                message=f"数据库连接池配置加载失败: {str(e)}"
            )
    
    def _test_environment_config(self):
        """测试环境变量配置是否与文档一致"""
        
        # 检查关键环境变量的存在性
        required_env_vars = [
            ("AUTH_ENABLED", "认证开关"),
            ("DATABASE_URL", "数据库连接URL"),
        ]
        
        for env_var, description in required_env_vars:
            value = os.getenv(env_var)
            if value is not None:
                self._record_test_result(
                    test_name=f"环境变量: {env_var}",
                    passed=True,
                    message=f"{description} 已配置",
                    details={"value": value if env_var != "DATABASE_URL" else "***"}
                )
            else:
                self._record_test_result(
                    test_name=f"环境变量: {env_var}",
                    passed=False,
                    message=f"{description} 未配置"
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
            
        if details:
            print(f"   详情: {json.dumps(details, ensure_ascii=False, indent=2)}")
    
    def _generate_report(self) -> Dict:
        """生成测试报告"""
        total_tests = self.passed_tests + self.failed_tests
        pass_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "pass_rate": round(pass_rate, 2),
                "test_date": datetime.now().isoformat()
            },
            "test_results": self.test_results
        }
        
        print("\n" + "=" * 80)
        print("📊 文档验证测试报告")
        print("=" * 80)
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {self.passed_tests}")
        print(f"失败测试: {self.failed_tests}")
        print(f"通过率: {pass_rate:.2f}%")
        
        if self.failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['message']}")
        
        # 保存报告到文件
        report_file = f"tests/reports/documentation_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return report


def main():
    """主函数"""
    print("🚀 LSP系统文档验证测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建验证器并运行测试
    validator = DocumentationValidator()
    report = validator.run_all_tests()
    
    # 根据测试结果设置退出码
    if report["summary"]["failed_tests"] > 0:
        print("\n⚠️  发现文档一致性问题，请检查上述失败的测试项")
        sys.exit(1)
    else:
        print("\n🎉 所有文档验证测试通过!")
        sys.exit(0)


if __name__ == "__main__":
    main()