"""二分类模型评估工具。"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics_from_probability(
    y_true: pd.Series | np.ndarray,
    positive_probability: pd.Series | np.ndarray,
    threshold: float = 0.5,
) -> dict[str, float]:
    """根据正类概率计算 AUC、准确率、精确率、召回率和 F1。"""
    probabilities = np.asarray(positive_probability)
    y_pred = (probabilities >= threshold).astype(int)
    return {
        "auc": round(roc_auc_score(y_true, probabilities), 4),
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, zero_division=0), 4),
        "f1": round(f1_score(y_true, y_pred, zero_division=0), 4),
    }


def evaluate_model(
    model,
    x_data: pd.DataFrame,
    y_true: pd.Series,
    dataset_name: str,
    threshold: float = 0.5,
) -> dict:
    """使用统一指标评估支持 predict_proba 的二分类模型。"""
    positive_probability = model.predict_proba(x_data)[:, 1]
    metrics = classification_metrics_from_probability(
        y_true,
        positive_probability,
        threshold=threshold,
    )
    return {"dataset": dataset_name, **metrics}


def evaluate_probability_series(
    y_true: pd.Series,
    positive_probability: pd.Series | np.ndarray,
    model_name: str,
    dataset_name: str = "test",
    model_type: str = "single",
    description: str = "",
    threshold: float = 0.5,
) -> dict:
    """直接基于预测概率评估单模型或融合模型。"""
    metrics = classification_metrics_from_probability(
        y_true,
        positive_probability,
        threshold=threshold,
    )
    return {
        "model": model_name,
        "model_type": model_type,
        "dataset": dataset_name,
        **metrics,
        "description": description,
    }

