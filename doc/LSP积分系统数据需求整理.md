# LSP积分系统数据需求整理

## 概述
本文档整理了实现LSP积分系统所需的所有数据需求，并标记了哪些数据可以从iOS HealthKit获取。

## 数据分类说明
- ✅ **可从HealthKit获取**: 该数据可以直接从iOS HealthKit API获取
- ⚠️ **部分可从HealthKit获取**: 需要结合HealthKit数据和其他数据源
- ❌ **无法从HealthKit获取**: 需要其他数据源或用户手动输入

## 1. 睡眠相关数据

### 基础睡眠数据
- **睡眠时长** ✅ 
  - 数据类型: HKCategoryTypeIdentifierSleepAnalysis
  - 需求: 每日睡眠总时长（目标7.5小时）
  
- **深度睡眠时长** ✅
  - 数据类型: HKCategoryValueSleepAnalysisAsleepCore
  - 需求: 深度睡眠>1.5小时
  
- **REM睡眠时长** ✅
  - 数据类型: HKCategoryValueSleepAnalysisAsleepREM
  - 需求: REM睡眠>1.5小时

### 睡眠时间数据
- **入睡时间** ✅
  - 数据类型: 从HKCategoryTypeIdentifierSleepAnalysis获取
  - 需求: 11:30前入睡
  
- **起床时间** ✅
  - 数据类型: 从HKCategoryTypeIdentifierSleepAnalysis获取
  - 需求: 7:30前起床

### 其他睡眠相关
- **基因检测（sleepless genes）** ❌
  - 需要专门的基因检测服务

## 2. 运动相关数据

### 步数与活动
- **每日步数** ✅
  - 数据类型: HKQuantityTypeIdentifierStepCount
  - 需求: 上限30000步，0.05 LSP/步
  
- **站立时长** ✅
  - 数据类型: HKQuantityTypeIdentifierAppleStandTime
  - 需求: 80 LSP/小时

### 运动类型
- **Zone 2运动时长** ⚠️
  - 数据类型: HKWorkoutType + 心率数据计算
  - 需求: 需要根据心率区间判断
  
- **力量训练** ✅
  - 数据类型: HKWorkoutTypeIdentifier.functionalStrengthTraining
  - 需求: 记录训练时长
  
- **其他运动（含拉伸）** ✅
  - 数据类型: HKWorkoutType（各种运动类型）
  - 需求: 记录运动类型和时长

### 运动多样性
- **运动类型追踪** ⚠️
  - 数据类型: HKWorkoutType
  - 需求: 需要记录每天的运动类型，判断是否与前2天不同

## 3. 饮食相关数据

### 营养摄入
- **食物颜色识别** ❌
  - 需要图像识别功能，拍照分析
  
- **食物种类统计** ❌
  - 需要用户输入或图像识别
  
- **水分摄入** ✅
  - 数据类型: HKQuantityTypeIdentifierDietaryWater
  - 需求: 100 LSP/小时

### 营养成分
- **蛋白质摄入** ✅
  - 数据类型: HKQuantityTypeIdentifierDietaryProtein
  
- **Omega-3摄入** ⚠️
  - 数据类型: 需要用户记录保健品摄入
  
- **碳水化合物摄入** ✅
  - 数据类型: HKQuantityTypeIdentifierDietaryCarbohydrates

### 饮食模式
- **轻断食时间** ⚠️
  - 需要记录最后一餐和第一餐时间
  - 可以通过用户输入或智能推断
  
- **血糖监测（CGM）** ⚠️
  - 数据类型: HKQuantityTypeIdentifierBloodGlucose（如果有CGM设备）
  - 需要专门的连续血糖监测设备

### 生化检测
- **微量元素检测** ❌
- **常量元素检测** ❌
- **炎症指标** ❌
  - 需要医疗检测报告上传

## 4. 环境相关数据

### 光照与噪音
- **室外日照时间** ⚠️
  - 可以通过UV暴露数据间接判断: HKQuantityTypeIdentifierUVExposure
  
- **环境噪音** ✅
  - 数据类型: HKQuantityTypeIdentifierEnvironmentalAudioExposure
  - 需求: <70dB持续时间

### 环境质量
- **空气质量（AQI）** ❌
  - 需要外部API获取当地空气质量
  
- **空气净化器使用** ❌
  - 需要智能家居集成或用户手动记录

### 屏幕时间
- **手机使用时间** ⚠️
  - iOS屏幕时间API（需要权限）
  - 睡前手机使用监测

## 5. 心理健康数据

### 生理指标
- **心率变异性（HRV）** ✅
  - 数据类型: HKQuantityTypeIdentifierHeartRateVariabilitySDNN
  - 需求: HRV ≥ 平均值
  
- **静息心率** ✅
  - 数据类型: HKQuantityTypeIdentifierRestingHeartRate

### 心理活动
- **冥想/呼吸练习** ✅
  - 数据类型: HKCategoryTypeIdentifierMindfulSession
  - 需求: 10分钟/天

### 专业评估
- **PHQ-9抑郁评估** ❌
- **GAD-7焦虑评估** ❌
- **Cortisol皮质醇测试** ❌
  - 需要专业测试和报告上传

### 其他
- **Focus blocks时间** ❌
  - 需要专门的专注力追踪应用
  
- **情绪check-in** ❌
  - 需要用户手动输入

## 6. 认知能力数据

### 认知测试
- **Stroop测试** ❌
- **记忆测试** ❌
- **反应时间测试** ❌
- **N-back测试** ❌
  - 需要集成第三方认知测试平台

### 认知相关生理数据
- **VO2 Max** ✅
  - 数据类型: HKQuantityTypeIdentifierVO2Max
  - Apple Watch可以估算

## 7. 生物标记与医疗数据

### 基础生理数据
- **体温** ✅
  - 数据类型: HKQuantityTypeIdentifierBodyTemperature
  - 需求: 监测体温变化+0.4°C
  
- **血压** ✅
  - 数据类型: HKQuantityTypeIdentifierBloodPressureSystolic/Diastolic
  
- **血氧饱和度** ✅
  - 数据类型: HKQuantityTypeIdentifierOxygenSaturation

### 专业医疗检测
- **基因检测（Omics）** ❌
- **全血检测** ❌
- **生物年龄测试** ❌
- **肠道健康/微生物组学** ❌
- **蛋白质组学** ❌
- **代谢组学** ❌
- **免疫谱系** ❌
  - 所有Omics检测需要专业医疗机构

### 疫苗接种
- **疫苗记录** ⚠️
  - 数据类型: HKClinicalTypeIdentifierImmunizationRecord（需要医疗记录权限）

## 8. 社交与目标数据

- **Accountable partner匹配** ❌
- **社会角色选择** ❌
- **Challenge参与** ❌
- **任务完成度** ❌
  - 需要应用内功能开发

## 9. 用户身份与设备数据

### 身份验证
- **身份认证** ❌
- **zk身份验证** ❌
  - 需要专门的身份验证系统

### 设备连接
- **可穿戴设备连接状态** ⚠️
  - 可以检测是否有HealthKit数据源
  
- **设备类型** ✅
  - 数据类型: HKDevice信息

## 10. 积分系统管理数据

- **累计LSP积分** ❌
- **Tier等级** ❌
- **积分过期时间** ❌
- **积分倍数** ❌
- **健康投入金额** ❌
  - 需要应用内数据库管理

## 实施建议

### 优先级1: HealthKit可直接获取的数据
1. 睡眠分析（时长、深度、REM、时间）
2. 活动数据（步数、站立、运动）
3. 生理指标（HRV、心率、体温）
4. 营养基础数据（水分、蛋白质、碳水）

### 优先级2: 需要额外开发的核心功能
1. 食物拍照识别系统
2. Focus blocks追踪
3. 情绪与心理状态记录
4. 积分计算与管理系统

### 优先级3: 需要第三方集成
1. 认知测试平台集成
2. 空气质量API
3. 医疗检测报告上传系统
4. CGM设备集成

### 数据隐私与安全建议
1. 所有健康数据需要用户明确授权
2. 敏感医疗数据需要加密存储
3. 遵守HIPAA等医疗数据隐私法规
4. 实施数据最小化原则

## 总结
- **HealthKit可获取数据比例**: 约35%的核心数据可直接从HealthKit获取
- **需要额外开发**: 约40%的功能需要自主开发
- **需要第三方服务**: 约25%的数据需要第三方服务或医疗机构配合

建议分阶段实施，先利用HealthKit可获取的数据建立MVP，再逐步集成其他数据源。