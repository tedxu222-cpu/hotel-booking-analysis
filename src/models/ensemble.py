"""模型融合工具，包括加权平均和 Stacking。"""

from __future__ import annotations

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from src.models.traditional import (
    RANDOM_STATE,
    TRADITIONAL_MODEL_NAMES,
    build_best_model,
    params_for_model,
)


def fit_best_traditional_models(
    best_params: pd.DataFrame,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    model_names: list[str] | None = None,
) -> dict[str, object]:
    """用 Optuna 最优参数训练一组传统机器学习模型。"""
    fitted_models = {}
    for model_name in model_names or TRADITIONAL_MODEL_NAMES:
        params = params_for_model(best_params, model_name)
        model = build_best_model(model_name, params, y_train=y_train)
        model.fit(x_train, y_train)
        fitted_models[model_name] = model
    return fitted_models


def predict_probability_table(
    fitted_models: dict[str, object],
    x_data: pd.DataFrame,
) -> pd.DataFrame:
    """汇总多个模型对同一批样本输出的取消概率。"""
    probability_data = {
        model_name: model.predict_proba(x_data)[:, 1]
        for model_name, model in fitted_models.items()
    }
    return pd.DataFrame(probability_data, index=x_data.index)


def weighted_probability(
    probability_table: pd.DataFrame,
    weights: dict[str, float],
) -> np.ndarray:
    """按指定权重计算多模型预测概率的加权平均。"""
    missing_models = [name for name in weights if name not in probability_table.columns]
    if missing_models:
        raise KeyError(f"概率表缺少模型列：{missing_models}")

    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        raise ValueError("融合权重之和必须大于 0。")

    output = np.zeros(probability_table.shape[0])
    for model_name, weight in weights.items():
        output += probability_table[model_name].to_numpy() * (weight / weight_sum)
    return output


def build_meta_model(meta_model_name: str):
    """构建 Stacking 第二层元学习器。"""
    if meta_model_name == "Logistic Regression":
        return LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
    if meta_model_name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=200,
            max_depth=5,
            min_samples_leaf=30,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )
    if meta_model_name == "LightGBM":
        return LGBMClassifier(
            n_estimators=120,
            num_leaves=15,
            max_depth=4,
            learning_rate=0.05,
            min_child_samples=80,
            class_weight="balanced",
            objective="binary",
            verbosity=-1,
            random_state=RANDOM_STATE,
        )
    raise ValueError(f"未知元学习器：{meta_model_name}")


def fit_stacking_model(
    validation_probability_table: pd.DataFrame,
    y_validation: pd.Series,
    base_models: list[str],
    meta_model_name: str,
):
    """用验证集基模型概率训练 Stacking 元学习器。"""
    meta_model = build_meta_model(meta_model_name)
    meta_model.fit(validation_probability_table[base_models], y_validation)
    return meta_model


def predict_stacking_probability(
    meta_model,
    probability_table: pd.DataFrame,
    base_models: list[str],
) -> np.ndarray:
    """使用训练好的 Stacking 元学习器输出融合概率。"""
    return meta_model.predict_proba(probability_table[base_models])[:, 1]

