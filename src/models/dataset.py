"""建模数据集读取、拆分和样本统计工具。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight

from src.config import (
    TARGET_COLUMN,
    TEST_DATASET_PATH,
    TRAIN_DATASET_PATH,
    VALIDATION_DATASET_PATH,
)


HOTEL_TYPE_COLUMNS = {
    "City Hotel": "hotel_type_City_Hotel",
    "Resort Hotel": "hotel_type_Resort_Hotel",
}


def load_modeling_datasets(
    train_path: Path = TRAIN_DATASET_PATH,
    validation_path: Path = VALIDATION_DATASET_PATH,
    test_path: Path = TEST_DATASET_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """读取第二阶段产出的训练集、验证集和测试集。"""
    for path in [train_path, validation_path, test_path]:
        if not path.exists():
            raise FileNotFoundError(f"建模数据不存在：{path}")
    return (
        pd.read_parquet(train_path),
        pd.read_parquet(validation_path),
        pd.read_parquet(test_path),
    )


def prepare_xy(
    data: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
) -> tuple[pd.DataFrame, pd.Series]:
    """从建模数据中拆分特征矩阵 X 和目标变量 y。"""
    if target_column not in data.columns:
        raise KeyError(f"目标变量不存在：{target_column}")
    drop_columns = [target_column, "dataset_split"]
    existing_drop_columns = [col for col in drop_columns if col in data.columns]
    x_data = data.drop(columns=existing_drop_columns).copy()
    y_data = data[target_column].astype("int8")
    return x_data, y_data


def build_split_summary(
    frames: dict[str, pd.DataFrame],
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """统计每个数据集的样本量、取消样本量和取消率。"""
    records = []
    for split_name, split_df in frames.items():
        if target_column not in split_df.columns:
            raise KeyError(f"{split_name} 缺少目标变量：{target_column}")
        class_counts = split_df[target_column].value_counts().to_dict()
        total_count = split_df.shape[0]
        canceled_count = int(class_counts.get(1, 0))
        not_canceled_count = int(class_counts.get(0, 0))
        records.append(
            {
                "dataset": split_name,
                "total_count": total_count,
                "not_canceled_count": not_canceled_count,
                "canceled_count": canceled_count,
                "not_canceled_ratio": round(not_canceled_count / total_count, 4),
                "canceled_ratio": round(canceled_count / total_count, 4),
                "data_source": "second_stage_modeling_dataset",
            }
        )
    return pd.DataFrame(records)


def compare_sampling_strategies(y_train: pd.Series) -> pd.DataFrame:
    """对比原始训练集、SMOTE、欠采样和类别权重四种训练口径。"""
    class_counts = y_train.value_counts().sort_index()
    not_canceled_count = int(class_counts.get(0, 0))
    canceled_count = int(class_counts.get(1, 0))
    max_count = max(not_canceled_count, canceled_count)
    min_count = min(not_canceled_count, canceled_count)
    total_count = not_canceled_count + canceled_count

    classes = np.array([0, 1])
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_train,
    )
    class_weight_map = {
        int(class_label): round(float(weight), 4)
        for class_label, weight in zip(classes, weights)
    }

    return pd.DataFrame(
        [
            {
                "strategy": "原始训练集",
                "not_canceled_count": not_canceled_count,
                "canceled_count": canceled_count,
                "total_count": total_count,
                "canceled_ratio": round(canceled_count / total_count, 4),
                "description": "不改变样本数量，作为基线训练口径。",
            },
            {
                "strategy": "SMOTE过采样",
                "not_canceled_count": max_count,
                "canceled_count": max_count,
                "total_count": max_count * 2,
                "canceled_ratio": 0.5,
                "description": "只对训练集少数类生成合成样本，使正负样本数量一致。",
            },
            {
                "strategy": "欠采样",
                "not_canceled_count": min_count,
                "canceled_count": min_count,
                "total_count": min_count * 2,
                "canceled_ratio": 0.5,
                "description": "只对训练集多数类随机抽样，使正负样本数量一致。",
            },
            {
                "strategy": "类别权重调整",
                "not_canceled_count": not_canceled_count,
                "canceled_count": canceled_count,
                "total_count": total_count,
                "canceled_ratio": round(canceled_count / total_count, 4),
                "description": f"不改变样本数量，class_weight={class_weight_map}。",
            },
        ]
    )


def filter_hotel_type(
    data: pd.DataFrame,
    hotel_type_column: str,
) -> pd.DataFrame:
    """按酒店类型 One-Hot 字段筛选城市酒店或度假酒店样本。"""
    if hotel_type_column not in data.columns:
        raise KeyError(f"缺少酒店类型字段：{hotel_type_column}")
    return data[data[hotel_type_column] == 1].copy()


def split_by_hotel_type(
    data: pd.DataFrame,
    hotel_type_columns: dict[str, str] | None = None,
) -> dict[str, pd.DataFrame]:
    """将一个数据集拆成城市酒店和度假酒店两个独立样本集。"""
    columns = hotel_type_columns or HOTEL_TYPE_COLUMNS
    return {
        hotel_type: filter_hotel_type(data, column)
        for hotel_type, column in columns.items()
    }

