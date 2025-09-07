#!/usr/bin/env python3
"""
测试套件主运行脚本
运行所有测试并生成综合报告
"""

import os
import sys
import subprocess
import json
import traceback
from datetime import datetime
from typing import Dict, List
from pathlib import Path

# 确保tests目录下的reports文件夹存在
reports_dir = Path(__file__).parent / "reports"
reports_dir.mkdir(exist_ok=True)


class TestSuiteRunner:
    """测试套件运行器"""
    
    def __init__(self):
        """初始化运行器"""
        self.test_dir = Path(__file__).parent
        self.results = []
        self.overall_passed = True
        
        # 测试脚本列表
        self.test_scripts = [
            {
                "name": "文档验证测试",
                "script": "test_documentation_validity.py",
                "description": "验证文档与实际代码的一致性"
            },
            {
                "name": "睡眠分析完整测试",
                "script": "test_sleep_analysis_complete.py",
                "description": "测试睡眠分析的各个方面"
            },
            {
                "name": "积分百分比完整测试",
                "script": "test_score_percentage_complete.py",
                "description": "测试积分百分比计算功能"
            },
            {
                "name": "集成测试",
                "script": "test_integration_complete.py",
                "description": "端到端集成测试"
            },
            {
                "name": "文档覆盖率分析",
                "script": "generate_doc_coverage.py",
                "description": "分析项目文档覆盖率"
            }
        ]
    
    def run_all_tests(self) -> Dict:
        """运行所有测试"""
        print("🚀 LSP系统完整测试套件")
        print("=" * 80)
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 测试目录: {self.test_dir}")
        print(f"📋 测试脚本数量: {len(self.test_scripts)}")
        print()
        
        start_time = datetime.now()
        
        for i, test_info in enumerate(self.test_scripts, 1):
            print(f"\n{'=' * 60}")
            print(f"📋 [{i}/{len(self.test_scripts)}] {test_info['name']}")
            print(f"📄 {test_info['description']}")
            print("=" * 60)
            
            result = self._run_single_test(test_info)
            self.results.append(result)
            
            if not result["passed"]:
                self.overall_passed = False
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # 生成综合报告
        return self._generate_comprehensive_report(start_time, end_time, duration)
    
    def _run_single_test(self, test_info: Dict) -> Dict:
        """运行单个测试脚本"""
        script_path = self.test_dir / test_info["script"]
        
        if not script_path.exists():
            return {
                "name": test_info["name"],
                "script": test_info["script"],
                "passed": False,
                "message": f"测试脚本不存在: {script_path}",
                "output": "",
                "error": f"文件不存在: {script_path}",
                "duration": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 运行测试脚本
            start_time = datetime.now()
            
            process = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=self.test_dir.parent,  # 在项目根目录运行
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 检查返回码
            passed = process.returncode == 0
            
            result = {
                "name": test_info["name"],
                "script": test_info["script"],
                "passed": passed,
                "message": "测试通过" if passed else f"测试失败 (退出码: {process.returncode})",
                "output": process.stdout,
                "error": process.stderr if process.stderr else "",
                "duration": duration,
                "return_code": process.returncode,
                "timestamp": datetime.now().isoformat()
            }
            
            # 打印结果摘要
            status_icon = "✅" if passed else "❌"
            print(f"{status_icon} {test_info['name']}: {result['message']}")
            print(f"⏱️  耗时: {duration:.2f}秒")
            
            if not passed and process.stderr:
                print(f"⚠️  错误输出: {process.stderr[:500]}...")
            
            return result
            
        except subprocess.TimeoutExpired:
            return {
                "name": test_info["name"],
                "script": test_info["script"],
                "passed": False,
                "message": "测试超时 (超过5分钟)",
                "output": "",
                "error": "测试执行超时",
                "duration": 300,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "name": test_info["name"],
                "script": test_info["script"],
                "passed": False,
                "message": f"测试执行异常: {str(e)}",
                "output": "",
                "error": str(e),
                "duration": 0,
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_comprehensive_report(self, start_time: datetime, end_time: datetime, duration) -> Dict:
        """生成综合报告"""
        
        # 统计结果
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["passed"]])
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # 生成报告
        report = {
            "summary": {
                "total_test_suites": total_tests,
                "passed_test_suites": passed_tests,
                "failed_test_suites": failed_tests,
                "pass_rate": round(pass_rate, 2),
                "overall_passed": self.overall_passed,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "total_duration": duration.total_seconds()
            },
            "test_results": self.results,
            "recommendations": self._generate_recommendations()
        }
        
        # 打印综合报告
        self._print_comprehensive_report(report)
        
        # 保存报告
        report_file = reports_dir / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 综合测试报告已保存到: {report_file}")
        
        return report
    
    def _generate_recommendations(self) -> List[Dict]:
        """生成改进建议"""
        recommendations = []
        
        # 检查失败的测试
        failed_tests = [r for r in self.results if not r["passed"]]
        
        if failed_tests:
            recommendations.append({
                "priority": "高",
                "category": "测试失败",
                "issue": f"有 {len(failed_tests)} 个测试套件失败",
                "suggestion": "优先修复失败的测试，确保基础功能正常",
                "failed_suites": [t["name"] for t in failed_tests]
            })
        
        # 检查性能问题
        slow_tests = [r for r in self.results if r["duration"] > 60]  # 超过1分钟的测试
        if slow_tests:
            recommendations.append({
                "priority": "中",
                "category": "性能优化",
                "issue": f"有 {len(slow_tests)} 个测试套件运行较慢",
                "suggestion": "考虑优化测试性能或拆分大型测试",
                "slow_suites": [(t["name"], f"{t['duration']:.1f}s") for t in slow_tests]
            })
        
        # 检查错误输出
        tests_with_errors = [r for r in self.results if r["error"]]
        if tests_with_errors:
            recommendations.append({
                "priority": "中",
                "category": "错误处理",
                "issue": f"有 {len(tests_with_errors)} 个测试有错误输出",
                "suggestion": "检查并修复测试中的警告和错误",
                "error_suites": [t["name"] for t in tests_with_errors]
            })
        
        # 基于通过率给出建议
        pass_rate = (len([r for r in self.results if r["passed"]]) / len(self.results) * 100) if self.results else 0
        
        if pass_rate < 80:
            recommendations.append({
                "priority": "高",
                "category": "整体质量",
                "issue": f"测试通过率较低 ({pass_rate:.1f}%)",
                "suggestion": "全面检查项目功能，提高代码质量和测试覆盖率"
            })
        elif pass_rate < 95:
            recommendations.append({
                "priority": "中",
                "category": "质量改进",
                "issue": f"测试通过率有待提高 ({pass_rate:.1f}%)",
                "suggestion": "继续改进功能实现，争取达到95%以上通过率"
            })
        
        return recommendations
    
    def _print_comprehensive_report(self, report: Dict):
        """打印综合报告"""
        summary = report["summary"]
        
        print("\n" + "=" * 80)
        print("📊 LSP系统测试套件综合报告")
        print("=" * 80)
        
        # 基本统计
        print(f"📈 总体通过率: {summary['pass_rate']:.2f}%")
        print(f"🧪 测试套件总数: {summary['total_test_suites']}")
        print(f"✅ 通过的套件: {summary['passed_test_suites']}")
        print(f"❌ 失败的套件: {summary['failed_test_suites']}")
        print(f"⏱️  总耗时: {summary['total_duration']:.2f}秒")
        
        # 各测试套件详情
        print("\n📋 各测试套件详情:")
        for result in self.results:
            status_icon = "✅" if result["passed"] else "❌"
            print(f"  {status_icon} {result['name']}: {result['message']} ({result['duration']:.1f}s)")
        
        # 失败的测试详情
        failed_tests = [r for r in self.results if not r["passed"]]
        if failed_tests:
            print(f"\n❌ 失败的测试详情:")
            for test in failed_tests:
                print(f"  📋 {test['name']}")
                print(f"     💬 {test['message']}")
                if test["error"]:
                    print(f"     ⚠️  {test['error'][:200]}...")
        
        # 改进建议
        recommendations = report["recommendations"]
        if recommendations:
            print(f"\n💡 改进建议:")
            for rec in recommendations:
                priority_icon = "🔴" if rec["priority"] == "高" else "🟡" if rec["priority"] == "中" else "🟢"
                print(f"  {priority_icon} [{rec['category']}] {rec['suggestion']}")
        
        # 整体评估
        overall_status = "通过" if summary["overall_passed"] else "失败"
        status_icon = "🎉" if summary["overall_passed"] else "⚠️"
        
        print(f"\n{status_icon} 整体测试状态: {overall_status}")
        
        if summary["pass_rate"] >= 95:
            print("🏆 优秀! 所有测试基本通过")
        elif summary["pass_rate"] >= 80:
            print("👍 良好! 大部分测试通过")
        elif summary["pass_rate"] >= 60:
            print("👌 一般，还需继续改进")
        else:
            print("⚠️  需要大幅改进测试通过率")


def main():
    """主函数"""
    try:
        runner = TestSuiteRunner()
        report = runner.run_all_tests()
        
        # 根据整体结果设置退出码
        if report["summary"]["overall_passed"]:
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断测试执行")
        sys.exit(2)
    except Exception as e:
        print(f"\n❌ 测试套件执行失败: {str(e)}")
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()