"""Notebook 使用的数据质量检查辅助函数。"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

# 允许从 src/data 目录直接运行脚本，同时还能导入 src/config.py。
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import (
    EXPECTED_COLUMNS,
    RAW_DATA_PATH,
    TARGET_COLUMN,
)


def load_raw_data(path: Path = RAW_DATA_PATH) -> pd.DataFrame:
    """读取原始 CSV 数据。"""
    if not path.exists():
        raise FileNotFoundError(f"数据文件不存在：{path}")
    return pd.read_csv(path)


def validate_schema(df: pd.DataFrame) -> None:
    """检查关键字段是否存在。"""
    # 预期字段来自项目说明；实际多出的字段只提示，不在这里删除。
    missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(f"数据缺少预期字段：{missing_columns}")

    unexpected_columns = [col for col in df.columns if col not in EXPECTED_COLUMNS]
    if unexpected_columns:
        print(f"发现项目说明之外的字段，暂不删除：{unexpected_columns}")

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"目标变量不存在：{TARGET_COLUMN}")


def build_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """生成字段级数据质量概览。"""
    return pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "missing_count": df.isna().sum(),
            "missing_ratio": df.isna().mean(),
            "unique_count": df.nunique(dropna=True),
        }
    ).sort_values(["missing_count", "missing_ratio"], ascending=False)
