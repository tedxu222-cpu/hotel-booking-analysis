"""深度学习模型辅助工具，用于 MLP 和 Embedding MLP 实验复用。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def import_keras():
    """延迟导入 TensorFlow/Keras，避免未安装时影响传统模型工具。"""
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras import layers
    except ImportError as exc:
        raise ImportError(
            "当前环境缺少 TensorFlow。请先安装 requirements.txt 中的依赖，"
            "再运行深度学习模型相关功能。"
        ) from exc
    return tf, keras, layers


def build_training_history_records(
    history: Any,
    model_name: str,
    config_id: int,
    config: dict,
    extra_config: dict | None = None,
) -> list[dict]:
    """把 Keras history 转换为逐 epoch 训练曲线记录。"""
    records = []
    extra_config = extra_config or {}
    epoch_count = len(history.history.get("loss", []))
    for epoch_index in range(epoch_count):
        record = {
            "model": model_name,
            "config_id": config_id,
            "epoch": epoch_index + 1,
            "loss": history.history.get("loss", [np.nan] * epoch_count)[epoch_index],
            "auc": history.history.get("auc", [np.nan] * epoch_count)[epoch_index],
            "val_loss": history.history.get("val_loss", [np.nan] * epoch_count)[epoch_index],
            "val_auc": history.history.get("val_auc", [np.nan] * epoch_count)[epoch_index],
            "hidden_units": str(config.get("hidden_units")),
            "dropout_rate": config.get("dropout_rate"),
            "learning_rate": config.get("learning_rate"),
            "batch_size": config.get("batch_size"),
            "epochs_planned": config.get("epochs"),
        }
        record.update(extra_config)
        records.append(record)
    return records


def replace_model_rows(
    output_path: Path,
    new_data: pd.DataFrame,
    model_names: list[str],
) -> pd.DataFrame:
    """用当前模型的新结果替换旧结果，避免重复运行后产生重复行。"""
    new_data = new_data.copy()
    if output_path.exists():
        previous_data = pd.read_csv(output_path)
        if "model" in previous_data.columns:
            previous_data = previous_data[~previous_data["model"].isin(model_names)]
        return pd.concat([previous_data, new_data], ignore_index=True)
    return new_data


def summarize_early_stopping_effect(
    model_history: pd.DataFrame,
    model_name: str,
) -> dict:
    """根据训练历史汇总早停位置和训练/验证 AUC 差距。"""
    if model_history.empty:
        return {
            "model": model_name,
            "best_epoch": np.nan,
            "last_epoch": np.nan,
            "best_val_auc": np.nan,
            "last_val_auc": np.nan,
            "last_train_auc": np.nan,
            "train_validation_auc_gap": np.nan,
            "early_stopping_effect": "没有训练历史，无法判断",
        }

    best_row = model_history.loc[model_history["val_auc"].idxmax()]
    last_row = model_history.sort_values("epoch").iloc[-1]
    auc_gap = float(last_row["auc"] - last_row["val_auc"])
    if abs(auc_gap) <= 0.01:
        effect = "训练集和验证集 AUC 接近，无明显严重过拟合"
    elif auc_gap > 0.01:
        effect = "训练集 AUC 高于验证集，需要关注过拟合"
    else:
        effect = "验证集 AUC 高于训练集，可能与正则化或样本差异有关"

    return {
        "model": model_name,
        "best_epoch": int(best_row["epoch"]),
        "last_epoch": int(last_row["epoch"]),
        "best_val_auc": round(float(best_row["val_auc"]), 4),
        "last_val_auc": round(float(last_row["val_auc"]), 4),
        "last_train_auc": round(float(last_row["auc"]), 4),
        "train_validation_auc_gap": round(auc_gap, 4),
        "early_stopping_effect": effect,
    }


def build_mlp_model(
    input_dim: int,
    hidden_units: tuple[int, int] = (128, 64),
    dropout_rate: float = 0.3,
    learning_rate: float = 0.001,
):
    """构建用于结构化特征二分类的普通 MLP 模型。"""
    _, keras, layers = import_keras()
    model = keras.Sequential(
        [
            layers.Input(shape=(input_dim,)),
            layers.Dense(hidden_units[0]),
            layers.LeakyReLU(negative_slope=0.01),
            layers.BatchNormalization(),
            layers.Dropout(dropout_rate),
            layers.Dense(hidden_units[1]),
            layers.LeakyReLU(negative_slope=0.01),
            layers.BatchNormalization(),
            layers.Dropout(dropout_rate),
            layers.Dense(1, activation="sigmoid"),
        ]
    )
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[keras.metrics.AUC(name="auc")],
    )
    return model


def build_embedding_mlp_model(
    categorical_columns: list[str],
    categorical_cardinality: dict[str, int],
    numeric_dim: int,
    embedding_dim: int = 8,
    hidden_units: tuple[int, int] = (128, 64),
    dropout_rate: float = 0.3,
    learning_rate: float = 0.001,
):
    """构建类别 Embedding 与数值特征拼接后的 MLP 模型。"""
    _, keras, layers = import_keras()
    inputs = {}
    embeddings = []
    for column in categorical_columns:
        input_layer = keras.Input(shape=(1,), name=column)
        inputs[column] = input_layer
        cardinality = int(categorical_cardinality[column])
        embedding_layer = layers.Embedding(
            input_dim=cardinality,
            output_dim=min(embedding_dim, max(2, cardinality // 2)),
            name=f"{column}_embedding",
        )(input_layer)
        embeddings.append(layers.Flatten()(embedding_layer))

    numeric_input = keras.Input(shape=(numeric_dim,), name="numeric_features")
    inputs["numeric_features"] = numeric_input
    merged_features = layers.Concatenate()(embeddings + [numeric_input])
    x = layers.Dense(hidden_units[0])(merged_features)
    x = layers.LeakyReLU(negative_slope=0.01)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(dropout_rate)(x)
    x = layers.Dense(hidden_units[1])(x)
    x = layers.LeakyReLU(negative_slope=0.01)(x)
    x = layers.BatchNormalization()(x)
    x = layers.Dropout(dropout_rate)(x)
    output = layers.Dense(1, activation="sigmoid")(x)

    model = keras.Model(inputs=inputs, outputs=output)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss="binary_crossentropy",
        metrics=[keras.metrics.AUC(name="auc")],
    )
    return model


def build_training_callbacks(patience: int = 5, lr_patience: int = 3):
    """构建早停和学习率衰减回调。"""
    _, keras, _ = import_keras()
    return [
        keras.callbacks.EarlyStopping(
            monitor="val_auc",
            mode="max",
            patience=patience,
            restore_best_weights=True,
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=lr_patience,
            min_lr=1e-5,
        ),
    ]
