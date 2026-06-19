"""Build optimized Parquet datasets and intermediate analysis tables."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# 允许从 src/data 目录直接运行脚本，同时还能导入 src/config.py。
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from config import (
    BOOKING_BEHAVIOR_TABLE_PATH,
    CLEANED_PARQUET_PATH,
    CUSTOMER_PROFILE_TABLE_PATH,
    HOTEL_SUMMARY_TABLE_PATH,
    MODELING_BASE_PARQUET_PATH,
    PROCESSED_DATA_PATH,
    PROJECT_ROOT,
    TARGET_COLUMN,
    TIME_DIMENSION_TABLE_PATH,
)


# 这两个字段描述订单最终状态，后续建模时可能造成数据泄漏。
LEAKAGE_COLUMNS = ["reservation_status", "reservation_status_date"]


def load_cleaned_data(path: Path = PROCESSED_DATA_PATH) -> pd.DataFrame:
    """读取清洗后的 CSV 数据集。"""
    if not path.exists():
        raise FileNotFoundError(f"Cleaned data file does not exist: {path}")
    return pd.read_csv(path)


def optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """压缩字段数据类型，降低后续读写和聚合的内存占用。"""
    optimized = df.copy()

    # 数值字段向下压缩，降低后续读写和聚合的内存占用。
    for col in optimized.select_dtypes(include=["int", "int64"]).columns:
        optimized[col] = pd.to_numeric(optimized[col], downcast="integer")

    for col in optimized.select_dtypes(include=["float", "float64"]).columns:
        optimized[col] = pd.to_numeric(optimized[col], downcast="float")

    for col in ["reservation_status_date", "arrival_date"]:
        if col in optimized.columns:
            optimized[col] = pd.to_datetime(optimized[col], errors="coerce")

    # 低基数字符串字段转为 category，Parquet 存储和分组统计更高效。
    object_cols = [
        col
        for col in optimized.columns
        if (
            pd.api.types.is_object_dtype(optimized[col])
            or pd.api.types.is_string_dtype(optimized[col])
        )
    ]
    for col in object_cols:
        unique_ratio = optimized[col].nunique(dropna=True) / max(len(optimized), 1)
        if unique_ratio < 0.5:
            optimized[col] = optimized[col].astype("category")

    return optimized


def build_modeling_base(df: pd.DataFrame) -> pd.DataFrame:
    """移除明显结果字段，构建后续建模使用的基础表。"""
    # 保留完整清洗数据，同时单独输出去除结果字段的建模基础表。
    drop_cols = [col for col in LEAKAGE_COLUMNS if col in df.columns]
    return df.drop(columns=drop_cols)


def build_customer_profile_table(df: pd.DataFrame) -> pd.DataFrame:
    """按客户类型和渠道字段构建客户群体画像表。

    """
    group_cols = [
        "customer_type",
        "is_repeated_guest",
        "market_segment",
        "distribution_channel",
    ]
    return (
        df.groupby(group_cols, observed=True)
        .agg(
            booking_count=(TARGET_COLUMN, "size"),
            cancellation_count=(TARGET_COLUMN, "sum"),
            cancellation_rate=(TARGET_COLUMN, "mean"),
            avg_lead_time=("lead_time", "mean"),
            avg_adr=("adr", "mean"),
            avg_total_stays=("total_stays", "mean"),
            avg_special_requests=("total_of_special_requests", "mean"),
        )
        .reset_index()
    )


def build_hotel_summary_table(df: pd.DataFrame) -> pd.DataFrame:
    """按酒店和城市维度构建酒店统计汇总表。"""
    group_cols = ["hotel"]
    if "city" in df.columns:
        group_cols.append("city")

    return (
        df.groupby(group_cols, observed=True)
        .agg(
            booking_count=(TARGET_COLUMN, "size"),
            cancellation_count=(TARGET_COLUMN, "sum"),
            cancellation_rate=(TARGET_COLUMN, "mean"),
            avg_adr=("adr", "mean"),
            avg_lead_time=("lead_time", "mean"),
            avg_total_stays=("total_stays", "mean"),
        )
        .reset_index()
    )


def build_time_dimension_table(df: pd.DataFrame) -> pd.DataFrame:
    """基于 arrival_date 构建时间维度表。"""
    if "arrival_date" not in df.columns:
        raise ValueError("arrival_date column is required for time dimension.")

    dates = pd.Series(df["arrival_date"].dropna().unique(), name="arrival_date")
    time_dim = pd.DataFrame({"arrival_date": pd.to_datetime(dates)})
    time_dim = time_dim.sort_values("arrival_date").reset_index(drop=True)
    iso_calendar = time_dim["arrival_date"].dt.isocalendar()

    time_dim["year"] = time_dim["arrival_date"].dt.year
    time_dim["month"] = time_dim["arrival_date"].dt.month
    time_dim["week"] = iso_calendar.week.astype("int16")
    time_dim["day"] = time_dim["arrival_date"].dt.day
    time_dim["day_of_week"] = time_dim["arrival_date"].dt.dayofweek
    time_dim["is_weekend"] = time_dim["day_of_week"].isin([5, 6])
    return time_dim


def build_booking_behavior_table(df: pd.DataFrame) -> pd.DataFrame:
    """按 arrival_date 聚合构建每日预订行为统计表。"""
    if "arrival_date" not in df.columns:
        raise ValueError("arrival_date column is required for booking behavior.")

    return (
        df.groupby("arrival_date", observed=True)
        .agg(
            booking_count=(TARGET_COLUMN, "size"),
            cancellation_count=(TARGET_COLUMN, "sum"),
            cancellation_rate=(TARGET_COLUMN, "mean"),
            avg_adr=("adr", "mean"),
            avg_lead_time=("lead_time", "mean"),
            avg_total_stays=("total_stays", "mean"),
        )
        .reset_index()
        .sort_values("arrival_date")
    )


def save_parquet(df: pd.DataFrame, path: Path) -> None:
    """将 DataFrame 保存为 Parquet 文件。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        df.to_parquet(path, index=False)
    except (ImportError, OSError) as exc:
        raise RuntimeError(f"Failed to save Parquet file: {path}") from exc


def build_all_tables() -> dict[str, Path]:
    """统一构建所有预处理数据集和中间表。"""
    cleaned = load_cleaned_data()
    optimized = optimize_dtypes(cleaned)

    modeling_base = build_modeling_base(optimized)
    customer_profile = build_customer_profile_table(optimized)
    hotel_summary = build_hotel_summary_table(optimized)
    time_dimension = build_time_dimension_table(optimized)
    booking_behavior = build_booking_behavior_table(optimized)

    outputs = {
        "cleaned_parquet": CLEANED_PARQUET_PATH,
        "modeling_base": MODELING_BASE_PARQUET_PATH,
        "customer_profile": CUSTOMER_PROFILE_TABLE_PATH,
        "hotel_summary": HOTEL_SUMMARY_TABLE_PATH,
        "time_dimension": TIME_DIMENSION_TABLE_PATH,
        "booking_behavior": BOOKING_BEHAVIOR_TABLE_PATH,
    }

    save_parquet(optimized, CLEANED_PARQUET_PATH)
    save_parquet(modeling_base, MODELING_BASE_PARQUET_PATH)
    save_parquet(customer_profile, CUSTOMER_PROFILE_TABLE_PATH)
    save_parquet(hotel_summary, HOTEL_SUMMARY_TABLE_PATH)
    save_parquet(time_dimension, TIME_DIMENSION_TABLE_PATH)
    save_parquet(booking_behavior, BOOKING_BEHAVIOR_TABLE_PATH)

    return outputs


def main() -> None:
    """中间表构建脚本的命令行入口函数。"""
    outputs = build_all_tables()
    print("数据预处理与中间表构建完成")
    for name, path in outputs.items():
        try:
            display_path = path.relative_to(PROJECT_ROOT)
        except ValueError:
            display_path = path
        print(f"{name}: {display_path}")


if __name__ == "__main__":
    main()
