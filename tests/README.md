# LSP系统测试套件

这个测试套件为LSP积分系统提供全面的测试覆盖，旨在验证文档准确性并确保所有功能正常工作。

## 测试脚本概述

### 1. 文档验证测试 (`test_documentation_validity.py`)
- **目标**: 验证所有文档化的API是否存在并正常工作
- **验证内容**:
  - API端点存在性
  - API响应格式
  - 配置一致性
  - 代码示例可执行性
  - 数据库表结构
  - 环境变量配置

### 2. 睡眠分析完整测试 (`test_sleep_analysis_complete.py`)
- **目标**: 测试睡眠阶段分析、数据源优先级选择和积分计算
- **验证内容**:
  - 睡眠计算器规则
  - 易/中/难难度积分计算
  - 数据源优先级 (Apple Watch > Oura > WHOOP)
  - 睡眠阶段分析
  - 时间限制评分
  - 边界情况处理
  - 连锁惩罚机制

### 3. 积分百分比完整测试 (`test_score_percentage_complete.py`)
- **目标**: 测试所有维度的百分比计算和配置
- **验证内容**:
  - 最高分配置验证
  - 百分比计算函数
  - 各维度百分比计算
  - 边界情况处理
  - API响应百分比字段
  - 积分引擎百分比集成
  - 无效输入处理
  - 精度和舍入

### 4. 集成测试 (`test_integration_complete.py`)
- **目标**: 端到端测试完整工作流程
- **验证内容**:
  - 服务初始化验证
  - 数据流集成
  - 睡眠分析到积分计算
  - 多源数据处理
  - 数据冲突解决
  - 完整工作流程
  - API端到端测试
  - 错误处理集成
  - 性能集成测试
  - 数据一致性

### 5. 文档覆盖率报告 (`generate_doc_coverage.py`)
- **目标**: 分析项目文档覆盖率并生成改进建议
- **分析内容**:
  - 源代码特性提取
  - 文档内容分析
  - 覆盖率计算
  - 未文档化特性识别
  - 过时文档检测
  - 改进建议生成

## 运行测试

### 运行所有测试
```bash
# 运行完整测试套件
python tests/run_all_tests.py
```

### 运行单个测试
```bash
# 文档验证测试
python tests/test_documentation_validity.py

# 睡眠分析测试
python tests/test_sleep_analysis_complete.py

# 积分百分比测试
python tests/test_score_percentage_complete.py

# 集成测试
python tests/test_integration_complete.py

# 文档覆盖率分析
python tests/generate_doc_coverage.py
```

## 前置条件

### API服务器
某些测试需要API服务器运行：
```bash
# 启动API服务器
python start_server.py
```

### Python依赖
确保已安装必要的依赖：
```bash
pip install requests fastapi uvicorn pydantic
```

### 数据库连接
集成测试可能需要数据库连接。确保数据库配置正确并且可访问。

## 测试结果

### 报告位置
所有测试都会在 `tests/reports/` 目录下生成详细的JSON报告：
- `documentation_validation_YYYYMMDD_HHMMSS.json`
- `sleep_analysis_complete_YYYYMMDD_HHMMSS.json`
- `score_percentage_complete_YYYYMMDD_HHMMSS.json`
- `integration_complete_YYYYMMDD_HHMMSS.json`
- `doc_coverage_YYYYMMDD_HHMMSS.json`
- `comprehensive_test_report_YYYYMMDD_HHMMSS.json`

### 退出码
- **0**: 所有测试通过
- **1**: 有测试失败
- **2**: 用户中断
- **3**: 系统错误

### 通过率目标
- **文档验证**: 目标 95% 通过率
- **睡眠分析**: 目标 90% 通过率
- **积分百分比**: 目标 95% 通过率
- **集成测试**: 目标 85% 通过率
- **文档覆盖率**: 目标 70% 覆盖率

## 解读测试结果

### 成功指标
- ✅ 绿色勾号表示测试通过
- 📊 百分比显示覆盖率或通过率
- 🎉 最终成功消息

### 失败指标
- ❌ 红叉表示测试失败
- ⚠️ 黄色警告表示需要注意的问题
- 📋 详细错误信息和建议

### 改进建议
每个测试都会根据结果生成具体的改进建议：
- **高优先级** 🔴: 需要立即修复的关键问题
- **中优先级** 🟡: 建议改进的功能点
- **低优先级** 🟢: 可选的优化项

## 故障排除

### 常见问题

**1. API连接失败**
- 确保API服务器正在运行 (`python start_server.py`)
- 检查端口8001是否可用
- 验证防火墙设置

**2. 数据库连接错误**
- 检查数据库服务是否运行
- 验证连接字符串配置
- 确认数据库权限

**3. 导入错误**
- 确保在项目根目录运行测试
- 检查Python路径配置
- 验证所有依赖已安装

**4. 测试超时**
- 某些测试可能需要较长时间
- 检查系统性能
- 考虑调整超时设置

### 调试模式
在测试脚本中设置详细输出：
```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
python tests/test_integration_complete.py
```

## 持续集成

这些测试脚本设计为可在CI/CD管道中运行：

```yaml
# GitHub Actions 示例
name: LSP Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v3
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python tests/run_all_tests.py
```

## 贡献指南

添加新测试时，请遵循以下模式：
1. 继承适当的测试基类
2. 实现 `_record_test_result` 方法记录结果
3. 生成详细的JSON报告
4. 提供清晰的中文错误消息
5. 包含改进建议

## 质量目标

当前项目的质量目标是87%，略低于95%的目标。这些测试旨在：
1. 识别文档与实现之间的差距
2. 验证所有核心功能正常工作
3. 提供具体的改进路径
4. 确保代码质量持续提升

运行完整测试套件应该帮助项目达到并超越95%的质量目标。