"""模型预测推理接口，支持批量预测和单条预测。"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.models.traditional import load_model_artifact


RISK_SEGMENT_BINS = [0.0, 0.3, 0.5, 0.7, 1.000001]
RISK_SEGMENT_LABELS = ["低风险", "中风险", "高风险", "极高风险"]


def assign_risk_segment(probabilities: pd.Series | np.ndarray) -> pd.Series:
    """把取消概率转换为业务可读的风险等级。"""
    probability_series = pd.Series(probabilities)
    return pd.cut(
        probability_series,
        bins=RISK_SEGMENT_BINS,
        labels=RISK_SEGMENT_LABELS,
        include_lowest=True,
        right=False,
    ).astype(str)


def suggest_action(risk_segment: str) -> str:
    """根据风险等级给出简化业务动作建议。"""
    action_map = {
        "低风险": "维持常规服务，避免过度打扰。",
        "中风险": "发送入住提醒或确认短信。",
        "高风险": "加强确认，并提供灵活改期选项。",
        "极高风险": "考虑人工确认、押金或信用卡担保。",
    }
    return action_map.get(risk_segment, "待人工复核。")


def _read_input_data(input_data: pd.DataFrame | str | Path) -> pd.DataFrame:
    """读取 DataFrame、CSV 或 Parquet 格式的预测输入。"""
    if isinstance(input_data, pd.DataFrame):
        return input_data.copy()

    input_path = Path(input_data)
    if not input_path.exists():
        raise FileNotFoundError(f"预测输入文件不存在：{input_path}")
    if input_path.suffix.lower() == ".csv":
        return pd.read_csv(input_path)
    if input_path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(input_path)
    raise ValueError("预测输入仅支持 DataFrame、CSV 或 Parquet。")


def _prepare_prediction_features(
    data: pd.DataFrame,
    feature_columns: list[str],
) -> pd.DataFrame:
    """按训练时的特征列顺序整理预测输入。"""
    missing_columns = [col for col in feature_columns if col not in data.columns]
    if missing_columns:
        raise KeyError(f"预测输入缺少特征字段：{missing_columns}")
    return data[feature_columns].copy()


def predict_dataframe(
    data: pd.DataFrame,
    model,
    feature_columns: list[str],
    threshold: float = 0.5,
) -> pd.DataFrame:
    """对已经加载到内存的数据进行批量预测。"""
    x_data = _prepare_prediction_features(data, feature_columns)
    cancel_probability = model.predict_proba(x_data)[:, 1]
    result = data.copy()
    result["cancel_probability"] = cancel_probability
    result["predicted_cancel"] = (cancel_probability >= threshold).astype(int)
    result["risk_segment"] = assign_risk_segment(cancel_probability).to_numpy()
    result["suggested_action"] = result["risk_segment"].map(suggest_action)
    return result


def predict_batch(
    input_data: pd.DataFrame | str | Path,
    model_artifact_path: str | Path,
    output_path: str | Path | None = None,
    threshold: float = 0.5,
) -> pd.DataFrame:
    """批量预测订单取消概率，可选择把结果保存到文件。"""
    artifact = load_model_artifact(Path(model_artifact_path))
    data = _read_input_data(input_data)
    result = predict_dataframe(
        data,
        artifact["model"],
        artifact["feature_columns"],
        threshold=threshold,
    )

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if output_path.suffix.lower() == ".csv":
            result.to_csv(output_path, index=False, encoding="utf-8-sig")
        elif output_path.suffix.lower() in {".parquet", ".pq"}:
            result.to_parquet(output_path, index=False)
        else:
            raise ValueError("预测输出仅支持 CSV 或 Parquet。")
    return result


def predict_single(
    order_data: dict | pd.Series,
    model_artifact_path: str | Path,
    threshold: float = 0.5,
) -> dict:
    """预测单条订单，并返回取消概率、预测标签、风险等级和建议动作。"""
    one_row = pd.DataFrame([dict(order_data)])
    result = predict_batch(
        one_row,
        model_artifact_path=model_artifact_path,
        threshold=threshold,
    )
    output = result[
        [
            "cancel_probability",
            "predicted_cancel",
            "risk_segment",
            "suggested_action",
        ]
    ].iloc[0]
    return output.to_dict()

