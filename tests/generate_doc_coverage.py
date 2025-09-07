#!/usr/bin/env python3
"""
文档覆盖率报告生成器
分析代码库并生成文档覆盖率报告，识别未文档化的特性和不一致之处
"""

import os
import sys
import json
import ast
import re
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
import importlib.util

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))


class DocumentationCoverageAnalyzer:
    """文档覆盖率分析器"""
    
    def __init__(self, project_root: str = None):
        """初始化分析器"""
        self.project_root = Path(project_root or os.path.dirname(os.path.abspath(__file__)) + "/..")
        self.src_path = self.project_root / "src"
        self.docs_path = self.project_root / "docs"
        
        # 分析结果存储
        self.code_features = {
            "classes": {},
            "functions": {},
            "methods": {},
            "apis": {},
            "configs": {},
            "constants": {}
        }
        
        self.doc_features = {
            "documented_apis": set(),
            "documented_classes": set(),
            "documented_functions": set(),
            "documented_configs": set(),
            "code_examples": []
        }
        
        self.coverage_stats = {
            "total_features": 0,
            "documented_features": 0,
            "undocumented_features": [],
            "inconsistent_features": [],
            "unused_docs": []
        }
    
    def analyze_project(self) -> Dict:
        """分析整个项目的文档覆盖率"""
        print("📊 开始分析项目文档覆盖率...")
        print("=" * 80)
        
        try:
            # 1. 分析源代码
            print("\n🔍 分析源代码特性...")
            self._analyze_source_code()
            
            # 2. 分析文档内容
            print("\n📚 分析文档内容...")
            self._analyze_documentation()
            
            # 3. 计算覆盖率
            print("\n📈 计算覆盖率...")
            self._calculate_coverage()
            
            # 4. 生成报告
            print("\n📋 生成报告...")
            return self._generate_coverage_report()
            
        except Exception as e:
            print(f"❌ 分析失败: {str(e)}")
            traceback.print_exc()
            return {"error": str(e)}
    
    def _analyze_source_code(self):
        """分析源代码，提取所有特性"""
        
        # 分析Python源文件
        python_files = list(self.src_path.rglob("*.py"))
        print(f"找到 {len(python_files)} 个Python文件")
        
        for py_file in python_files:
            try:
                self._analyze_python_file(py_file)
            except Exception as e:
                print(f"⚠️  分析文件失败 {py_file}: {str(e)}")
        
        # 分析配置文件
        self._analyze_config_files()
        
        # 分析API路由
        self._analyze_api_routes()
    
    def _analyze_python_file(self, file_path: Path):
        """分析单个Python文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析AST
            tree = ast.parse(content)
            
            # 提取类
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "file": str(file_path.relative_to(self.project_root)),
                        "docstring": ast.get_docstring(node),
                        "methods": [],
                        "line_number": node.lineno
                    }
                    
                    # 提取方法
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_info = {
                                "name": item.name,
                                "class": node.name,
                                "file": str(file_path.relative_to(self.project_root)),
                                "docstring": ast.get_docstring(item),
                                "line_number": item.lineno,
                                "is_public": not item.name.startswith('_')
                            }
                            class_info["methods"].append(method_info)
                            
                            # 记录到方法字典
                            method_key = f"{node.name}.{item.name}"
                            self.code_features["methods"][method_key] = method_info
                    
                    self.code_features["classes"][node.name] = class_info
                
                # 提取独立函数
                elif isinstance(node, ast.FunctionDef) and not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree) if hasattr(parent, 'body') and node in parent.body):
                    function_info = {
                        "name": node.name,
                        "file": str(file_path.relative_to(self.project_root)),
                        "docstring": ast.get_docstring(node),
                        "line_number": node.lineno,
                        "is_public": not node.name.startswith('_')
                    }
                    self.code_features["functions"][node.name] = function_info
            
            # 提取常量（大写变量）
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            constant_info = {
                                "name": target.id,
                                "file": str(file_path.relative_to(self.project_root)),
                                "line_number": node.lineno
                            }
                            self.code_features["constants"][target.id] = constant_info
            
        except SyntaxError:
            print(f"⚠️  语法错误，跳过文件: {file_path}")
        except Exception as e:
            print(f"⚠️  分析文件出错 {file_path}: {str(e)}")
    
    def _analyze_config_files(self):
        """分析配置文件"""
        
        # 查找配置相关文件
        config_patterns = ["*config*.py", "*.env*", "*.yaml", "*.yml", "*.json"]
        
        for pattern in config_patterns:
            config_files = list(self.project_root.rglob(pattern))
            for config_file in config_files:
                if config_file.name.startswith('.'):
                    continue
                
                config_info = {
                    "name": config_file.name,
                    "file": str(config_file.relative_to(self.project_root)),
                    "type": config_file.suffix
                }
                
                # 尝试提取配置项
                if config_file.suffix == '.py':
                    try:
                        self._extract_config_from_python(config_file, config_info)
                    except Exception as e:
                        print(f"⚠️  提取Python配置失败 {config_file}: {str(e)}")
                elif config_file.name.endswith('.env') or '.env' in config_file.name:
                    try:
                        self._extract_config_from_env(config_file, config_info)
                    except Exception as e:
                        print(f"⚠️  提取环境变量配置失败 {config_file}: {str(e)}")
                
                self.code_features["configs"][config_file.name] = config_info
    
    def _extract_config_from_python(self, config_file: Path, config_info: Dict):
        """从Python配置文件提取配置项"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            config_items = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            config_items.append({
                                "key": target.id,
                                "line": node.lineno
                            })
            
            config_info["items"] = config_items
            
        except Exception as e:
            config_info["error"] = str(e)
    
    def _extract_config_from_env(self, env_file: Path, config_info: Dict):
        """从环境变量文件提取配置项"""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            env_vars = []
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key = line.split('=')[0].strip()
                        env_vars.append({
                            "key": key,
                            "line": i
                        })
            
            config_info["items"] = env_vars
            
        except Exception as e:
            config_info["error"] = str(e)
    
    def _analyze_api_routes(self):
        """分析API路由"""
        
        # 查找API相关文件
        api_files = list(self.src_path.rglob("*api*.py"))
        
        for api_file in api_files:
            try:
                with open(api_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 使用正则表达式查找路由定义
                route_patterns = [
                    r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
                ]
                
                for pattern in route_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        method = match.group(1).upper()
                        path = match.group(2)
                        
                        api_key = f"{method} {path}"
                        api_info = {
                            "method": method,
                            "path": path,
                            "file": str(api_file.relative_to(self.project_root)),
                            "line_number": content[:match.start()].count('\n') + 1
                        }
                        
                        self.code_features["apis"][api_key] = api_info
                        
            except Exception as e:
                print(f"⚠️  分析API文件出错 {api_file}: {str(e)}")
    
    def _analyze_documentation(self):
        """分析文档内容"""
        
        # 查找所有文档文件
        doc_patterns = ["*.md", "*.rst", "*.txt"]
        doc_files = []
        
        for pattern in doc_patterns:
            doc_files.extend(list(self.project_root.rglob(pattern)))
        
        print(f"找到 {len(doc_files)} 个文档文件")
        
        for doc_file in doc_files:
            try:
                self._analyze_doc_file(doc_file)
            except Exception as e:
                print(f"⚠️  分析文档文件出错 {doc_file}: {str(e)}")
    
    def _analyze_doc_file(self, doc_file: Path):
        """分析单个文档文件"""
        try:
            with open(doc_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取API端点
            api_patterns = [
                r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}:]+)',
                r'`(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}:]+)`',
                r'```\s*(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}:]+)'
            ]
            
            for pattern in api_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    method = match.group(1).upper()
                    path = match.group(2)
                    api_endpoint = f"{method} {path}"
                    self.doc_features["documented_apis"].add(api_endpoint)
            
            # 提取类名
            class_patterns = [
                r'class\s+(\w+)',
                r'`(\w+Calculator)`',
                r'`(\w+Service)`',
                r'`(\w+Engine)`',
                r'### (\w+)\s*类',
                r'## (\w+)\s*类'
            ]
            
            for pattern in class_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    class_name = match.group(1)
                    self.doc_features["documented_classes"].add(class_name)
            
            # 提取函数名
            function_patterns = [
                r'def\s+(\w+)',
                r'`(\w+)\(`',
                r'### (\w+)\s*函数',
                r'## (\w+)\s*函数'
            ]
            
            for pattern in function_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    function_name = match.group(1)
                    if not function_name.startswith('_'):  # 只关注公共函数
                        self.doc_features["documented_functions"].add(function_name)
            
            # 提取配置项
            config_patterns = [
                r'([A-Z_]+)\s*[:=]',
                r'`([A-Z_]+)`',
                r'环境变量.*?`([A-Z_]+)`',
                r'配置.*?`([A-Z_]+)`'
            ]
            
            for pattern in config_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    config_name = match.group(1)
                    self.doc_features["documented_configs"].add(config_name)
            
            # 提取代码示例
            code_block_pattern = r'```(?:python|bash|json|yaml)?\s*\n(.*?)\n```'
            code_matches = re.finditer(code_block_pattern, content, re.DOTALL)
            for match in code_matches:
                code_example = {
                    "file": str(doc_file.relative_to(self.project_root)),
                    "code": match.group(1).strip(),
                    "language": "unknown"
                }
                self.doc_features["code_examples"].append(code_example)
                
        except Exception as e:
            print(f"⚠️  分析文档文件内容出错: {str(e)}")
    
    def _calculate_coverage(self):
        """计算文档覆盖率"""
        
        # 统计总特性数量
        total_features = 0
        documented_features = 0
        undocumented_features = []
        inconsistent_features = []
        
        # 检查类的文档覆盖率
        for class_name, class_info in self.code_features["classes"].items():
            total_features += 1
            if class_name in self.doc_features["documented_classes"] or class_info["docstring"]:
                documented_features += 1
            else:
                undocumented_features.append({
                    "type": "class",
                    "name": class_name,
                    "file": class_info["file"],
                    "line": class_info["line_number"]
                })
        
        # 检查函数的文档覆盖率
        for func_name, func_info in self.code_features["functions"].items():
            if func_info["is_public"]:  # 只检查公共函数
                total_features += 1
                if func_name in self.doc_features["documented_functions"] or func_info["docstring"]:
                    documented_features += 1
                else:
                    undocumented_features.append({
                        "type": "function",
                        "name": func_name,
                        "file": func_info["file"],
                        "line": func_info["line_number"]
                    })
        
        # 检查方法的文档覆盖率
        for method_key, method_info in self.code_features["methods"].items():
            if method_info["is_public"]:  # 只检查公共方法
                total_features += 1
                method_name = method_info["name"]
                if method_name in self.doc_features["documented_functions"] or method_info["docstring"]:
                    documented_features += 1
                else:
                    undocumented_features.append({
                        "type": "method",
                        "name": method_key,
                        "file": method_info["file"],
                        "line": method_info["line_number"]
                    })
        
        # 检查API的文档覆盖率
        for api_key, api_info in self.code_features["apis"].items():
            total_features += 1
            if api_key in self.doc_features["documented_apis"]:
                documented_features += 1
            else:
                undocumented_features.append({
                    "type": "api",
                    "name": api_key,
                    "file": api_info["file"],
                    "line": api_info["line_number"]
                })
        
        # 检查配置的文档覆盖率
        for config_name, config_info in self.code_features["configs"].items():
            total_features += 1
            if config_name in self.doc_features["documented_configs"]:
                documented_features += 1
            else:
                undocumented_features.append({
                    "type": "config",
                    "name": config_name,
                    "file": config_info["file"]
                })
        
        # 检查文档中是否有过时的内容
        unused_docs = []
        
        # 检查文档中提到但代码中不存在的API
        for doc_api in self.doc_features["documented_apis"]:
            if doc_api not in self.code_features["apis"]:
                # 检查是否是通配符路径
                is_template = "{" in doc_api or "<" in doc_api
                if not is_template:
                    unused_docs.append({
                        "type": "api",
                        "name": doc_api,
                        "reason": "API endpoint not found in code"
                    })
        
        # 检查文档中提到但代码中不存在的类
        for doc_class in self.doc_features["documented_classes"]:
            if doc_class not in self.code_features["classes"]:
                unused_docs.append({
                    "type": "class",
                    "name": doc_class,
                    "reason": "Class not found in code"
                })
        
        # 更新统计信息
        self.coverage_stats.update({
            "total_features": total_features,
            "documented_features": documented_features,
            "undocumented_features": undocumented_features,
            "inconsistent_features": inconsistent_features,
            "unused_docs": unused_docs
        })
    
    def _generate_coverage_report(self) -> Dict:
        """生成文档覆盖率报告"""
        
        stats = self.coverage_stats
        coverage_rate = (stats["documented_features"] / stats["total_features"] * 100) if stats["total_features"] > 0 else 0
        
        # 按类型统计未文档化特性
        undocumented_by_type = {}
        for item in stats["undocumented_features"]:
            item_type = item["type"]
            if item_type not in undocumented_by_type:
                undocumented_by_type[item_type] = []
            undocumented_by_type[item_type].append(item)
        
        # 按文件统计未文档化特性
        undocumented_by_file = {}
        for item in stats["undocumented_features"]:
            file_name = item["file"]
            if file_name not in undocumented_by_file:
                undocumented_by_file[file_name] = []
            undocumented_by_file[file_name].append(item)
        
        # 生成改进建议
        improvement_suggestions = self._generate_improvement_suggestions()
        
        report = {
            "summary": {
                "total_features": stats["total_features"],
                "documented_features": stats["documented_features"],
                "undocumented_features": len(stats["undocumented_features"]),
                "coverage_rate": round(coverage_rate, 2),
                "unused_docs": len(stats["unused_docs"]),
                "analysis_date": datetime.now().isoformat()
            },
            "detailed_stats": {
                "by_type": {
                    "classes": {
                        "total": len(self.code_features["classes"]),
                        "documented": len([c for c in self.code_features["classes"].values() if c["name"] in self.doc_features["documented_classes"] or c["docstring"]])
                    },
                    "functions": {
                        "total": len([f for f in self.code_features["functions"].values() if f["is_public"]]),
                        "documented": len([f for f in self.code_features["functions"].values() if f["is_public"] and (f["name"] in self.doc_features["documented_functions"] or f["docstring"])])
                    },
                    "methods": {
                        "total": len([m for m in self.code_features["methods"].values() if m["is_public"]]),
                        "documented": len([m for m in self.code_features["methods"].values() if m["is_public"] and (m["name"] in self.doc_features["documented_functions"] or m["docstring"])])
                    },
                    "apis": {
                        "total": len(self.code_features["apis"]),
                        "documented": len([a for a in self.code_features["apis"].keys() if a in self.doc_features["documented_apis"]])
                    },
                    "configs": {
                        "total": len(self.code_features["configs"]),
                        "documented": len([c for c in self.code_features["configs"].keys() if c in self.doc_features["documented_configs"]])
                    }
                }
            },
            "undocumented_features": {
                "by_type": undocumented_by_type,
                "by_file": undocumented_by_file
            },
            "unused_documentation": stats["unused_docs"],
            "code_examples": {
                "total": len(self.doc_features["code_examples"]),
                "examples": self.doc_features["code_examples"][:5]  # 只显示前5个示例
            },
            "improvement_suggestions": improvement_suggestions
        }
        
        # 打印报告摘要
        self._print_report_summary(report)
        
        # 保存详细报告
        report_file = f"tests/reports/doc_coverage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📄 详细报告已保存到: {report_file}")
        
        return report
    
    def _generate_improvement_suggestions(self) -> List[Dict]:
        """生成改进建议"""
        suggestions = []
        
        stats = self.coverage_stats
        coverage_rate = (stats["documented_features"] / stats["total_features"] * 100) if stats["total_features"] > 0 else 0
        
        if coverage_rate < 60:
            suggestions.append({
                "priority": "高",
                "category": "整体覆盖率",
                "issue": f"文档覆盖率过低 ({coverage_rate:.1f}%)",
                "suggestion": "建议优先为公共API和核心类添加文档"
            })
        
        if coverage_rate < 80:
            suggestions.append({
                "priority": "中",
                "category": "代码注释",
                "issue": "缺少代码注释和docstring",
                "suggestion": "为所有公共方法添加docstring说明"
            })
        
        # 检查是否有很多未使用的文档
        if len(stats["unused_docs"]) > 5:
            suggestions.append({
                "priority": "中",
                "category": "文档维护",
                "issue": f"发现 {len(stats['unused_docs'])} 个过时的文档条目",
                "suggestion": "清理过时的文档内容，保持文档与代码同步"
            })
        
        # 检查API文档覆盖率
        api_total = len(self.code_features["apis"])
        api_documented = len([a for a in self.code_features["apis"].keys() if a in self.doc_features["documented_apis"]])
        if api_total > 0:
            api_coverage = (api_documented / api_total) * 100
            if api_coverage < 90:
                suggestions.append({
                    "priority": "高",
                    "category": "API文档",
                    "issue": f"API文档覆盖率不足 ({api_coverage:.1f}%)",
                    "suggestion": "为所有API端点创建详细的文档说明和使用示例"
                })
        
        # 检查代码示例
        if len(self.doc_features["code_examples"]) < 10:
            suggestions.append({
                "priority": "中",
                "category": "使用示例",
                "issue": "缺少足够的代码使用示例",
                "suggestion": "添加更多实际的代码使用示例来帮助用户理解"
            })
        
        return suggestions
    
    def _print_report_summary(self, report: Dict):
        """打印报告摘要"""
        summary = report["summary"]
        
        print("\n" + "=" * 80)
        print("📊 文档覆盖率分析报告")
        print("=" * 80)
        print(f"📈 总体覆盖率: {summary['coverage_rate']:.2f}%")
        print(f"🔍 分析特性总数: {summary['total_features']}")
        print(f"✅ 已文档化特性: {summary['documented_features']}")
        print(f"❌ 未文档化特性: {summary['undocumented_features']}")
        print(f"⚠️  过时文档条目: {summary['unused_docs']}")
        
        # 按类型显示统计
        detailed = report["detailed_stats"]["by_type"]
        print("\n📋 分类统计:")
        for category, stats in detailed.items():
            if stats["total"] > 0:
                coverage = (stats["documented"] / stats["total"]) * 100
                print(f"  {category}: {stats['documented']}/{stats['total']} ({coverage:.1f}%)")
        
        # 显示最需要改进的文件
        by_file = report["undocumented_features"]["by_file"]
        if by_file:
            print(f"\n📁 最需要改进的文件 (前5个):")
            sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)
            for file_name, items in sorted_files[:5]:
                print(f"  {file_name}: {len(items)} 个未文档化特性")
        
        # 显示改进建议
        suggestions = report["improvement_suggestions"]
        if suggestions:
            print(f"\n💡 改进建议:")
            for suggestion in suggestions:
                priority_icon = "🔴" if suggestion["priority"] == "高" else "🟡" if suggestion["priority"] == "中" else "🟢"
                print(f"  {priority_icon} [{suggestion['category']}] {suggestion['suggestion']}")
        
        # 评估质量等级
        coverage_rate = summary['coverage_rate']
        if coverage_rate >= 95:
            quality_grade = "A+ (优秀)"
        elif coverage_rate >= 90:
            quality_grade = "A (很好)"
        elif coverage_rate >= 80:
            quality_grade = "B (良好)"
        elif coverage_rate >= 70:
            quality_grade = "C (一般)"
        elif coverage_rate >= 60:
            quality_grade = "D (需改进)"
        else:
            quality_grade = "F (待改进)"
        
        print(f"\n🎯 文档质量等级: {quality_grade}")


def main():
    """主函数"""
    print("🚀 LSP系统文档覆盖率分析")
    print(f"⏰ 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建分析器并运行分析
    analyzer = DocumentationCoverageAnalyzer()
    report = analyzer.analyze_project()
    
    if "error" in report:
        print(f"\n❌ 分析失败: {report['error']}")
        sys.exit(1)
    
    # 根据覆盖率设置退出码
    coverage_rate = report["summary"]["coverage_rate"]
    if coverage_rate < 70:
        print(f"\n⚠️  文档覆盖率偏低 ({coverage_rate:.2f}%)，建议改进")
        sys.exit(1)
    else:
        print(f"\n🎉 文档覆盖率达标 ({coverage_rate:.2f}%)")
        sys.exit(0)


if __name__ == "__main__":
    main()