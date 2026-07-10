"""传统机器学习模型构建、调优和持久化工具。"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd
from lightgbm import LGBMClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from xgboost import XGBClassifier

from src.models.evaluation import evaluate_model


RANDOM_STATE = 42
TRADITIONAL_MODEL_NAMES = [
    "Logistic Regression",
    "Random Forest",
    "XGBoost",
    "LightGBM",
]


def calculate_scale_pos_weight(y_train: pd.Series) -> float:
    """计算 XGBoost 使用的正负样本权重比例。"""
    negative_count = int((y_train == 0).sum())
    positive_count = int((y_train == 1).sum())
    if positive_count == 0:
        raise ValueError("训练集中没有正类样本，无法计算 scale_pos_weight。")
    return negative_count / positive_count


def build_baseline_models(y_train: pd.Series) -> dict[str, object]:
    """构建传统机器学习默认基线模型。"""
    scale_pos_weight = calculate_scale_pos_weight(y_train)
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000,
            solver="liblinear",
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=160,
            max_depth=14,
            min_samples_leaf=30,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=180,
            max_depth=5,
            learning_rate=0.08,
            subsample=0.9,
            colsample_bytree=0.9,
            objective="binary:logistic",
            eval_metric="auc",
            tree_method="hist",
            scale_pos_weight=scale_pos_weight,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        ),
        "LightGBM": LGBMClassifier(
            n_estimators=180,
            max_depth=-1,
            learning_rate=0.08,
            num_leaves=31,
            subsample=0.9,
            colsample_bytree=0.9,
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
            verbose=-1,
        ),
    }


def params_for_model(best_params: pd.DataFrame, model_name: str) -> dict:
    """从 Optuna 最优参数表中读取指定模型的参数。"""
    model_params = best_params[best_params["model"] == model_name]
    params = {}
    for _, row in model_params.iterrows():
        value = row["value"]
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
        params[row["parameter"]] = value
    return params


def build_best_model(
    model_name: str,
    params: dict,
    y_train: pd.Series | None = None,
) -> object:
    """根据保存的最优参数构建传统机器学习模型。"""
    scale_pos_weight = (
        calculate_scale_pos_weight(y_train)
        if y_train is not None
        else float(params.get("scale_pos_weight", 1.0))
    )
    if model_name == "Logistic Regression":
        return LogisticRegression(
            penalty=params.get("penalty", "l2"),
            C=float(params.get("C", 1.0)),
            solver="liblinear",
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
    if model_name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=int(params.get("n_estimators", 160)),
            max_depth=int(params.get("max_depth", 14)),
            min_samples_leaf=int(params.get("min_samples_leaf", 30)),
            min_samples_split=int(params.get("min_samples_split", 10)),
            max_features=params.get("max_features", "sqrt"),
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )
    if model_name == "XGBoost":
        return XGBClassifier(
            n_estimators=int(params.get("n_estimators", 180)),
            max_depth=int(params.get("max_depth", 5)),
            learning_rate=float(params.get("learning_rate", 0.08)),
            subsample=float(params.get("subsample", 0.9)),
            colsample_bytree=float(params.get("colsample_bytree", 0.9)),
            min_child_weight=float(params.get("min_child_weight", 1.0)),
            gamma=float(params.get("gamma", 0.0)),
            reg_alpha=float(params.get("reg_alpha", 0.0)),
            reg_lambda=float(params.get("reg_lambda", 1.0)),
            objective="binary:logistic",
            eval_metric="auc",
            tree_method="hist",
            scale_pos_weight=scale_pos_weight,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )
    if model_name == "LightGBM":
        return LGBMClassifier(
            n_estimators=int(params.get("n_estimators", 180)),
            num_leaves=int(params.get("num_leaves", 31)),
            max_depth=int(params.get("max_depth", -1)),
            learning_rate=float(params.get("learning_rate", 0.08)),
            subsample=float(params.get("subsample", 0.9)),
            colsample_bytree=float(params.get("colsample_bytree", 0.9)),
            min_child_samples=int(params.get("min_child_samples", 20)),
            reg_alpha=float(params.get("reg_alpha", 0.0)),
            reg_lambda=float(params.get("reg_lambda", 1.0)),
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
            verbose=-1,
        )
    raise ValueError(f"未知模型：{model_name}")


def build_tuned_model(
    model_name: str,
    trial,
    y_train: pd.Series,
) -> object:
    """根据 Optuna trial 构建指定模型。"""
    scale_pos_weight = calculate_scale_pos_weight(y_train)
    if model_name == "Logistic Regression":
        return LogisticRegression(
            penalty=trial.suggest_categorical("penalty", ["l1", "l2"]),
            C=trial.suggest_float("C", 0.01, 20.0, log=True),
            solver="liblinear",
            max_iter=2000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        )
    if model_name == "Random Forest":
        return RandomForestClassifier(
            n_estimators=trial.suggest_int("n_estimators", 160, 400, step=40),
            max_depth=trial.suggest_int("max_depth", 8, 24),
            min_samples_leaf=trial.suggest_int("min_samples_leaf", 8, 80),
            min_samples_split=trial.suggest_int("min_samples_split", 10, 120),
            max_features=trial.suggest_categorical("max_features", ["sqrt", "log2", 0.5]),
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )
    if model_name == "XGBoost":
        return XGBClassifier(
            n_estimators=trial.suggest_int("n_estimators", 250, 800, step=50),
            max_depth=trial.suggest_int("max_depth", 3, 8),
            learning_rate=trial.suggest_float("learning_rate", 0.02, 0.16, log=True),
            subsample=trial.suggest_float("subsample", 0.7, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.7, 1.0),
            min_child_weight=trial.suggest_float("min_child_weight", 1.0, 10.0),
            gamma=trial.suggest_float("gamma", 0.0, 4.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-4, 1.5, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 0.2, 8.0, log=True),
            objective="binary:logistic",
            eval_metric="auc",
            tree_method="hist",
            scale_pos_weight=scale_pos_weight,
            n_jobs=-1,
            random_state=RANDOM_STATE,
        )
    if model_name == "LightGBM":
        return LGBMClassifier(
            n_estimators=trial.suggest_int("n_estimators", 250, 800, step=50),
            num_leaves=trial.suggest_int("num_leaves", 16, 96),
            max_depth=trial.suggest_int("max_depth", 3, 14),
            learning_rate=trial.suggest_float("learning_rate", 0.02, 0.16, log=True),
            subsample=trial.suggest_float("subsample", 0.7, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.7, 1.0),
            min_child_samples=trial.suggest_int("min_child_samples", 20, 180),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-4, 1.5, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 0.2, 8.0, log=True),
            class_weight="balanced",
            n_jobs=-1,
            random_state=RANDOM_STATE,
            verbose=-1,
        )
    raise ValueError(f"未知模型：{model_name}")


def make_objective(
    model_name: str,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_validation: pd.DataFrame,
    y_validation: pd.Series,
):
    """返回以验证集 AUC 为优化目标的 Optuna objective。"""

    def objective(trial) -> float:
        model = build_tuned_model(model_name, trial, y_train)
        model.fit(x_train, y_train)
        validation_probability = model.predict_proba(x_validation)[:, 1]
        return roc_auc_score(y_validation, validation_probability)

    return objective


def fit_and_evaluate_model(
    model_name: str,
    model,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    datasets: dict[str, tuple[pd.DataFrame, pd.Series]],
) -> list[dict]:
    """训练一个模型，并在多个数据集上输出统一指标。"""
    model.fit(x_train, y_train)
    records = []
    for dataset_name, (x_data, y_data) in datasets.items():
        metrics = evaluate_model(model, x_data, y_data, dataset_name)
        records.append({"model": model_name, **metrics})
    return records


def save_model_artifact(
    model,
    feature_columns: list[str],
    output_path: Path,
    metadata: dict | None = None,
) -> None:
    """保存模型、特征列和元数据，供预测推理复用。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": model,
            "feature_columns": feature_columns,
            "metadata": metadata or {},
        },
        output_path,
    )


def load_model_artifact(model_path: Path) -> dict:
    """读取 save_model_artifact 保存的模型文件。"""
    if not model_path.exists():
        raise FileNotFoundError(f"模型文件不存在：{model_path}")
    return joblib.load(model_path)

