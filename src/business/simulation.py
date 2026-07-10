"""取消风险分层和干预阈值收益模拟工具。"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.config import TARGET_COLUMN


RISK_SEGMENT_BINS = [0.0, 0.3, 0.5, 0.7, 1.000001]
RISK_SEGMENT_LABELS = ["低风险", "中风险", "高风险", "极高风险"]


def assign_risk_segment(
    risk_scores: pd.DataFrame,
    score_column: str = "cancel_risk_score",
) -> pd.DataFrame:
    """根据取消风险分数生成风险等级。"""
    output = risk_scores.copy()
    output["risk_segment"] = pd.cut(
        output[score_column],
        bins=RISK_SEGMENT_BINS,
        labels=RISK_SEGMENT_LABELS,
        include_lowest=True,
        right=False,
    ).astype(str)
    return output


def build_risk_segment_summary(
    risk_scores: pd.DataFrame,
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """统计不同风险等级的订单量、取消率和收入表现。"""
    data = (
        risk_scores
        if "risk_segment" in risk_scores.columns
        else assign_risk_segment(risk_scores)
    )
    summary = (
        data.groupby("risk_segment", observed=False)
        .agg(
            order_count=(target_column, "size"),
            canceled_count=(target_column, "sum"),
            actual_cancel_rate=(target_column, "mean"),
            avg_risk_score=("cancel_risk_score", "mean"),
            avg_adr=("adr", "mean"),
            avg_estimated_revenue=("estimated_revenue", "mean"),
        )
        .reset_index()
    )
    summary["order_share"] = summary["order_count"] / data.shape[0]
    return summary


def simulate_business_thresholds(
    risk_scores: pd.DataFrame,
    thresholds: np.ndarray,
    intervention_cost: float = 5.0,
    save_rate: float = 0.15,
    revenue_save_ratio: float = 0.5,
    target_column: str = TARGET_COLUMN,
) -> pd.DataFrame:
    """在不同干预阈值下模拟覆盖率、召回率和净收益。"""
    records = []
    actual_canceled = risk_scores[target_column].astype(int)
    total_canceled = int(actual_canceled.sum())

    for threshold in thresholds:
        intervention_mask = risk_scores["cancel_risk_score"] >= threshold
        touched_orders = int(intervention_mask.sum())
        touched_canceled_orders = int((actual_canceled & intervention_mask).sum())
        estimated_saved_orders = touched_canceled_orders * save_rate
        estimated_saved_revenue = (
            risk_scores.loc[
                intervention_mask & actual_canceled.astype(bool),
                "estimated_revenue",
            ].sum()
            * save_rate
            * revenue_save_ratio
        )
        cost = touched_orders * intervention_cost
        records.append(
            {
                "threshold": round(float(threshold), 2),
                "touched_orders": touched_orders,
                "touch_rate": round(touched_orders / risk_scores.shape[0], 4),
                "touched_canceled_orders": touched_canceled_orders,
                "cancel_recall": round(touched_canceled_orders / total_canceled, 4),
                "precision": round(
                    touched_canceled_orders / touched_orders if touched_orders else 0,
                    4,
                ),
                "estimated_saved_orders": round(estimated_saved_orders, 2),
                "estimated_saved_revenue": round(float(estimated_saved_revenue), 2),
                "intervention_cost": round(cost, 2),
                "estimated_net_benefit": round(
                    float(estimated_saved_revenue - cost),
                    2,
                ),
            }
        )
    return pd.DataFrame(records)

