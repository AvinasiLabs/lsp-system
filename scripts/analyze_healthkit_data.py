#!/usr/bin/env python3
"""
分析HealthKit数据类型和统计信息
"""
from postgresql import POSTGRES_POOL
from datetime import datetime
import pandas as pd


def analyze_healthkit_types():
    """分析所有HealthKit数据类型"""
    print("=== HealthKit 数据类型分析 ===\n")

    # 查询所有数据类型及其计数
    query = """
    SELECT type, COUNT(*) as count, 
           MIN(start_date) as earliest_date,
           MAX(start_date) as latest_date,
           COUNT(DISTINCT source_name) as sources
    FROM health_metric
    GROUP BY type
    ORDER BY count DESC;
    """

    results = POSTGRES_POOL._execute_query(query, fetch_all=True)

    if results:
        print(f"发现 {len(results)} 种不同的数据类型:\n")
        print(f"{'数据类型':<50} {'记录数':<10} {'数据源数':<10} {'最早日期':<20} {'最新日期':<20}")
        print("-" * 120)

        for row in results:
            type_name = row[0]
            count = row[1]
            earliest = row[2].strftime("%Y-%m-%d") if row[2] else "N/A"
            latest = row[3].strftime("%Y-%m-%d") if row[3] else "N/A"
            sources = row[4]

            print(f"{type_name:<50} {count:<10} {sources:<10} {earliest:<20} {latest:<20}")

    return results


def analyze_lsp_relevant_data():
    """分析与LSP积分系统相关的数据"""
    print("\n\n=== LSP积分系统相关数据分析 ===\n")

    # 定义LSP相关的数据类型映射
    lsp_data_mapping = {
        "睡眠": ["HKCategoryTypeIdentifierSleepAnalysis", "HKQuantityTypeIdentifierSleepAnalysis"],
        "步数": ["HKQuantityTypeIdentifierStepCount"],
        "站立": ["HKQuantityTypeIdentifierAppleStandTime", "HKCategoryTypeIdentifierAppleStandHour"],
        "运动": [
            "HKWorkoutTypeIdentifier",
            "HKQuantityTypeIdentifierActiveEnergyBurned",
            "HKQuantityTypeIdentifierBasalEnergyBurned",
            "HKQuantityTypeIdentifierDistanceWalkingRunning",
            "HKQuantityTypeIdentifierDistanceCycling",
            "HKQuantityTypeIdentifierDistanceSwimming",
            "HKQuantityTypeIdentifierAppleExerciseTime",
        ],
        "心率": [
            "HKQuantityTypeIdentifierHeartRate",
            "HKQuantityTypeIdentifierRestingHeartRate",
            "HKQuantityTypeIdentifierHeartRateVariabilitySDNN",
        ],
        "饮水": ["HKQuantityTypeIdentifierDietaryWater"],
        "营养": [
            "HKQuantityTypeIdentifierDietaryProtein",
            "HKQuantityTypeIdentifierDietaryCarbohydrates",
            "HKQuantityTypeIdentifierDietaryFiber",
            "HKQuantityTypeIdentifierDietaryFatTotal",
        ],
        "环境": ["HKQuantityTypeIdentifierEnvironmentalAudioExposure", "HKQuantityTypeIdentifierUVExposure"],
        "呼吸与冥想": ["HKCategoryTypeIdentifierMindfulSession", "HKQuantityTypeIdentifierRespiratoryRate"],
        "生理指标": [
            "HKQuantityTypeIdentifierBodyTemperature",
            "HKQuantityTypeIdentifierBloodPressureSystolic",
            "HKQuantityTypeIdentifierBloodPressureDiastolic",
            "HKQuantityTypeIdentifierOxygenSaturation",
            "HKQuantityTypeIdentifierVO2Max",
        ],
    }

    for category, types in lsp_data_mapping.items():
        print(f"\n{category}相关数据:")
        print("-" * 60)

        for data_type in types:
            # 查询该类型的数据统计
            query = """
            SELECT COUNT(*) as count,
                   MIN(start_date) as earliest,
                   MAX(start_date) as latest
            FROM health_metric
            WHERE type = %s;
            """

            result = POSTGRES_POOL._execute_query(query, (data_type,), fetch_one=True)

            if result and result[0] > 0:
                count = result[0]
                earliest = result[1].strftime("%Y-%m-%d") if result[1] else "N/A"
                latest = result[2].strftime("%Y-%m-%d") if result[2] else "N/A"
                print(f"  ✅ {data_type}: {count} 条记录 ({earliest} 至 {latest})")
            else:
                print(f"  ❌ {data_type}: 无数据")


def sample_sleep_data():
    """查看睡眠数据样本"""
    print("\n\n=== 睡眠数据样本 ===\n")

    query = """
    SELECT type, start_date, end_date, value, source_name
    FROM health_metric
    WHERE type LIKE '%Sleep%'
    ORDER BY start_date DESC
    LIMIT 10;
    """

    results = POSTGRES_POOL._execute_query(query, fetch_all=True)

    if results:
        for row in results:
            print(f"类型: {row[0]}")
            print(f"开始: {row[1]}")
            print(f"结束: {row[2]}")
            print(f"值: {row[3]}")
            print(f"来源: {row[4]}")
            print("-" * 40)


def main():
    """主函数"""
    # 分析所有数据类型
    all_types = analyze_healthkit_types()

    # 分析LSP相关数据
    analyze_lsp_relevant_data()

    # 查看睡眠数据样本
    sample_sleep_data()

    # 导出数据类型统计到CSV
    if all_types:
        df = pd.DataFrame(all_types, columns=["type", "count", "earliest_date", "latest_date", "sources"])
        df.to_csv("healthkit_data_types.csv", index=False)
        print("\n\n数据类型统计已导出到 healthkit_data_types.csv")


if __name__ == "__main__":
    main()
