"""Automated data quality checks for hotel booking datasets."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

# 允许从 src/data 目录直接运行脚本，同时还能导入 src/config.py。
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# Code Runner 在 Windows 上可能默认不是 UTF-8，这里避免中文输出乱码。
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config import EXPECTED_COLUMNS, PROJECT_ROOT, RAW_DATA_PATH, TARGET_COLUMN


ID_KEYWORDS = ("id", "booking_id", "order_id", "reservation_id")


def load_data(path: Path) -> pd.DataFrame:
    """读取指定路径下的 CSV 数据集。"""
    if not path.exists():
        raise FileNotFoundError(f"Data file does not exist: {path}")
    return pd.read_csv(path)


def check_completeness(df: pd.DataFrame) -> dict[str, Any]:
    """检查字段完整性，并统计每个字段的缺失情况。"""
    actual_columns = df.columns.tolist()
    # 对比项目说明字段和实际字段，识别缺失字段与额外字段。
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in actual_columns]
    extra_columns = [col for col in actual_columns if col not in EXPECTED_COLUMNS]
    missing_summary = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "missing_count": df.isna().sum(),
            "missing_ratio": df.isna().mean(),
            "unique_count": df.nunique(dropna=True),
        }
    ).sort_values(["missing_count", "missing_ratio"], ascending=False)

    return {
        "row_count": len(df),
        "column_count": len(actual_columns),
        "expected_column_count": len(EXPECTED_COLUMNS),
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        "is_empty": df.empty,
        "missing_summary": missing_summary,
    }


def check_consistency(df: pd.DataFrame) -> dict[str, Any]:
    """检查酒店预订数据中关键字段的取值一致性。"""
    result: dict[str, Any] = {}

    # 目标变量应只包含 0/1；如果换成同结构新数据，这里能快速发现异常编码。
    if TARGET_COLUMN in df.columns:
        target_values = sorted(df[TARGET_COLUMN].dropna().unique().tolist())
        result["target_values"] = target_values
        result["target_invalid_count"] = int((~df[TARGET_COLUMN].isin([0, 1])).sum())
        result["target_missing_count"] = int(df[TARGET_COLUMN].isna().sum())
    else:
        result["target_values"] = None
        result["target_invalid_count"] = None
        result["target_missing_count"] = None

    for col in ["adr", "adults", "children", "babies"]:
        if col in df.columns:
            result[f"{col}_negative_count"] = int((df[col] < 0).sum())

    stay_cols = ["stays_in_weekend_nights", "stays_in_week_nights"]
    for col in stay_cols:
        if col in df.columns:
            result[f"{col}_negative_count"] = int((df[col] < 0).sum())

    if all(col in df.columns for col in stay_cols):
        total_stays = df[stay_cols[0]] + df[stay_cols[1]]
        result["total_stays_le_0_count"] = int((total_stays <= 0).sum())
        result["total_stays_max"] = int(total_stays.max())

    date_parse_failures = {}
    if "reservation_status_date" in df.columns:
        parsed_status_date = pd.to_datetime(
            df["reservation_status_date"],
            errors="coerce",
        )
        date_parse_failures["reservation_status_date"] = int(
            parsed_status_date.isna().sum()
        )

    arrival_cols = [
        "arrival_date_year",
        "arrival_date_month",
        "arrival_date_day_of_month",
    ]
    if all(col in df.columns for col in arrival_cols):
        # 入住日期由年月日三个字段拼接生成，用于检查日期组合是否可解析。
        arrival_date = pd.to_datetime(
            df["arrival_date_year"].astype(str)
            + "-"
            + df["arrival_date_month"].astype(str)
            + "-"
            + df["arrival_date_day_of_month"].astype(str),
            errors="coerce",
        )
        date_parse_failures["arrival_date"] = int(arrival_date.isna().sum())

    result["date_parse_failures"] = date_parse_failures
    return result


def find_id_candidates(columns: list[str]) -> list[str]:
    """根据字段名查找可能代表唯一标识的字段。"""
    candidates = []
    for col in columns:
        lower_col = col.lower()
        # 当前数据没有明确订单 ID；这里保留通用规则，方便检查后续同结构数据。
        if lower_col in ID_KEYWORDS or lower_col.endswith("_id"):
            candidates.append(col)
    return candidates


def check_uniqueness(df: pd.DataFrame) -> dict[str, Any]:
    """检查完全重复行，并判断候选 ID 字段是否唯一。"""
    id_candidates = find_id_candidates(df.columns.tolist())
    id_uniqueness = {col: bool(df[col].is_unique) for col in id_candidates}

    return {
        "duplicate_row_count": int(df.duplicated().sum()),
        "id_candidates": id_candidates,
        "id_uniqueness": id_uniqueness,
        "has_clear_unique_id": any(id_uniqueness.values()),
    }


def run_quality_checks(path: Path) -> dict[str, Any]:
    """执行完整性、一致性和唯一性三类质量校验。"""
    df = load_data(path)
    return {
        "input_path": path,
        "completeness": check_completeness(df),
        "consistency": check_consistency(df),
        "uniqueness": check_uniqueness(df),
    }


def print_quality_report(report: dict[str, Any]) -> None:
    """将质量校验结果以简洁的中文报告形式输出到控制台。"""
    completeness = report["completeness"]
    consistency = report["consistency"]
    uniqueness = report["uniqueness"]
    input_path = report["input_path"]
    try:
        display_path = input_path.relative_to(PROJECT_ROOT)
    except ValueError:
        display_path = input_path

    print("数据质量校验报告")
    print(f"输入文件：{display_path}")
    print()
    print("[完整性检查]")
    print(f"数据行数：{completeness['row_count']}")
    print(f"实际字段数：{completeness['column_count']}")
    print(f"预期字段数：{completeness['expected_column_count']}")
    print(f"缺少字段：{completeness['missing_columns']}")
    print(f"额外字段：{completeness['extra_columns']}")
    print(f"是否为空数据：{completeness['is_empty']}")
    print()
    print("缺失值最多的字段：")
    missing_summary = completeness["missing_summary"].rename(
        columns={
            "dtype": "数据类型",
            "missing_count": "缺失数量",
            "missing_ratio": "缺失比例",
            "unique_count": "唯一值数量",
        }
    )
    print(missing_summary.head(10).to_string())

    print()
    print("[一致性检查]")
    consistency_labels = {
        "target_values": "目标变量取值",
        "target_invalid_count": "目标变量非法取值数量",
        "target_missing_count": "目标变量缺失数量",
        "adr_negative_count": "adr 负数数量",
        "adults_negative_count": "adults 负数数量",
        "children_negative_count": "children 负数数量",
        "babies_negative_count": "babies 负数数量",
        "stays_in_weekend_nights_negative_count": "周末入住晚数负数数量",
        "stays_in_week_nights_negative_count": "工作日入住晚数负数数量",
        "total_stays_le_0_count": "总入住晚数小于等于 0 数量",
        "total_stays_max": "总入住晚数最大值",
        "date_parse_failures": "日期解析失败数量",
    }
    for key, value in consistency.items():
        print(f"{consistency_labels.get(key, key)}：{value}")

    print()
    print("[唯一性检查]")
    uniqueness_labels = {
        "duplicate_row_count": "完全重复行数量",
        "id_candidates": "可能的 ID 字段",
        "id_uniqueness": "ID 字段唯一性",
        "has_clear_unique_id": "是否存在明确唯一 ID",
    }
    for key, value in uniqueness.items():
        print(f"{uniqueness_labels.get(key, key)}：{value}")


def parse_args() -> argparse.Namespace:
    """解析命令行参数，支持传入待检查的数据文件路径。"""
    parser = argparse.ArgumentParser(
        description="Run automated quality checks for hotel booking data."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=RAW_DATA_PATH,
        help="Path to the raw CSV data file.",
    )
    return parser.parse_args()


def main() -> None:
    """数据质量校验脚本的命令行入口函数。"""
    args = parse_args()
    report = run_quality_checks(args.input)
    print_quality_report(report)


if __name__ == "__main__":
    main()
