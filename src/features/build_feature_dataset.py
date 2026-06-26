"""构建酒店预订取消预测的全维度特征数据集。"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import CLEANED_PARQUET_PATH, FEATURE_PARQUET_PATH, PROJECT_ROOT  # noqa: E402


FEATURE_DICTIONARY_PATH = PROJECT_ROOT / "reports" / "feature_dictionary.csv"


def percentile_score(
    series: pd.Series,
    higher_is_better: bool = True,
    score_min: int = 1,
    score_max: int = 5,
) -> pd.Series:
    """按百分位给连续变量打分。"""
    percentile = series.rank(pct=True, method="average")
    if not higher_is_better:
        percentile = 1 - percentile + (1 / len(series))
    score = np.ceil(percentile * score_max).clip(score_min, score_max)
    return score.astype("int8")


def add_historical_rate(
    data: pd.DataFrame,
    group_col: str,
    target_col: str,
    prefix: str,
) -> pd.DataFrame:
    """按分组构造当前记录之前的历史订单数和历史取消率。"""
    ordered = data.sort_values(["arrival_date", "reservation_status_date"]).copy()
    group = ordered.groupby(group_col, observed=False)
    prior_count = group.cumcount()
    prior_target_sum = group[target_col].cumsum() - ordered[target_col]
    prior_rate = prior_target_sum / prior_count.replace(0, np.nan)

    data[f"{prefix}_hist_booking_count"] = (
        prior_count.reindex(data.index).fillna(0).astype("int32")
    )
    data[f"{prefix}_hist_cancel_rate"] = (
        prior_rate.reindex(data.index).fillna(0).astype("float32")
    )
    return data


def add_historical_mean(
    data: pd.DataFrame,
    group_col: str,
    value_col: str,
    prefix: str,
) -> pd.DataFrame:
    """按分组构造当前记录之前的历史均值。"""
    ordered = data.sort_values(["arrival_date", "reservation_status_date"]).copy()
    group = ordered.groupby(group_col, observed=False)
    prior_count = group.cumcount()
    prior_sum = group[value_col].cumsum() - ordered[value_col]
    prior_mean = prior_sum / prior_count.replace(0, np.nan)
    fallback = data[value_col].mean()

    data[f"{prefix}_hist_avg_{value_col}"] = (
        prior_mean.reindex(data.index).fillna(fallback).astype("float32")
    )
    return data


def load_cleaned_data(input_path: Path = CLEANED_PARQUET_PATH) -> pd.DataFrame:
    """读取清洗后数据，并统一日期字段类型。"""
    if not input_path.exists():
        raise FileNotFoundError(f"清洗后数据不存在：{input_path}")

    data = pd.read_parquet(input_path)
    data["arrival_date"] = pd.to_datetime(data["arrival_date"])
    data["reservation_status_date"] = pd.to_datetime(data["reservation_status_date"])
    return data


def add_time_features(features: pd.DataFrame) -> pd.DataFrame:
    """构造酒店类型、时间、周末、节假日代理和淡旺季特征。"""
    features["hotel_type"] = np.where(
        features["hotel"].astype(str).str.startswith("City Hotel"),
        "City Hotel",
        np.where(
            features["hotel"].astype(str).str.startswith("Resort Hotel"),
            "Resort Hotel",
            "Unknown",
        ),
    )
    features["arrival_month_num"] = features["arrival_date"].dt.month.astype("int8")
    features["arrival_month"] = features["arrival_date"].dt.to_period("M").astype(str)
    features["arrival_quarter"] = features["arrival_date"].dt.quarter.astype("int8")
    features["arrival_quarter_label"] = (
        features["arrival_date"].dt.to_period("Q").astype(str)
    )
    features["arrival_day_of_week"] = (
        features["arrival_date"].dt.dayofweek.astype("int8")
    )
    features["is_weekend"] = features["arrival_day_of_week"].isin([5, 6]).astype("int8")
    features["is_holiday_proxy"] = features["is_weekend"]
    features["holiday_proxy"] = np.where(
        features["is_weekend"] == 1,
        "周末/节假日代理",
        "工作日",
    )
    features["is_near_holiday_proxy"] = (
        features["arrival_day_of_week"].isin([0, 4]).astype("int8")
    )

    monthly_count = features.groupby("arrival_month_num").size()
    peak_threshold = monthly_count.quantile(0.75)
    low_threshold = monthly_count.quantile(0.25)
    peak_months = monthly_count[monthly_count >= peak_threshold].index
    low_months = monthly_count[monthly_count <= low_threshold].index

    features["season_type"] = np.select(
        [
            features["arrival_month_num"].isin(peak_months),
            features["arrival_month_num"].isin(low_months),
        ],
        ["旺季", "淡季"],
        default="平季",
    )
    features["is_peak_season"] = (features["season_type"] == "旺季").astype("int8")
    features["is_low_season"] = (features["season_type"] == "淡季").astype("int8")
    return features


def add_booking_features(features: pd.DataFrame) -> pd.DataFrame:
    """构造入住晚数、客人数、房型匹配和需求分组等预订行为特征。"""
    features["total_stays"] = (
        features["stays_in_weekend_nights"] + features["stays_in_week_nights"]
    ).astype("int16")
    features["total_guests"] = (
        features["adults"] + features["children"] + features["babies"]
    ).astype("float32")
    features["has_children_or_babies"] = (
        (features["children"] > 0) | (features["babies"] > 0)
    ).astype("int8")
    features["room_type_matched"] = (
        features["reserved_room_type"].astype(str)
        == features["assigned_room_type"].astype(str)
    ).astype("int8")
    features["has_booking_changes"] = (features["booking_changes"] > 0).astype("int8")
    features["has_special_requests"] = (
        features["total_of_special_requests"] > 0
    ).astype("int8")
    features["has_car_parking_request"] = (
        features["required_car_parking_spaces"] > 0
    ).astype("int8")
    features["lead_time_group"] = pd.cut(
        features["lead_time"],
        bins=[-1, 7, 30, 90, 180, np.inf],
        labels=["0-7", "8-30", "31-90", "91-180", "181+"],
    )
    features["special_request_group"] = (
        features["total_of_special_requests"].clip(upper=5).astype(int).astype(str)
    )
    features.loc[
        features["total_of_special_requests"] >= 5,
        "special_request_group",
    ] = "5+"
    return features


def add_customer_group_features(features: pd.DataFrame) -> pd.DataFrame:
    """基于客户属性组合构造客户群体键和 RFM 近似特征。"""
    customer_group_cols = [
        "customer_type",
        "market_segment",
        "distribution_channel",
        "is_repeated_guest",
    ]
    features["customer_group_key"] = (
        features[customer_group_cols].astype(str).agg("|".join, axis=1)
    )
    features["estimated_revenue"] = features["adr"] * features["total_stays"].clip(
        lower=1
    )

    rfm = (
        features.groupby("customer_group_key")
        .agg(
            group_booking_count=("is_canceled", "size"),
            group_avg_revenue=("estimated_revenue", "mean"),
            group_total_revenue=("estimated_revenue", "sum"),
            last_arrival_date=("arrival_date", "max"),
        )
        .reset_index()
    )
    max_arrival_date = features["arrival_date"].max()
    rfm["group_recency_days"] = (max_arrival_date - rfm["last_arrival_date"]).dt.days
    rfm["r_score"] = percentile_score(rfm["group_recency_days"], False)
    rfm["f_score"] = percentile_score(rfm["group_booking_count"], True)
    rfm["m_score"] = percentile_score(rfm["group_avg_revenue"], True)
    rfm["rfm_value_score"] = rfm["r_score"] + rfm["f_score"] + rfm["m_score"]

    q25, q50, q75 = rfm["rfm_value_score"].quantile([0.25, 0.5, 0.75])
    rfm["rfm_segment"] = np.select(
        [
            rfm["rfm_value_score"] >= q75,
            rfm["rfm_value_score"] >= q50,
            rfm["rfm_value_score"] >= q25,
        ],
        ["高价值", "潜力", "沉睡"],
        default="流失",
    )
    rfm["is_high_value_customer_group"] = (
        rfm["rfm_segment"] == "高价值"
    ).astype("int8")

    return features.merge(
        rfm[
            [
                "customer_group_key",
                "group_recency_days",
                "group_booking_count",
                "group_avg_revenue",
                "rfm_value_score",
                "rfm_segment",
                "is_high_value_customer_group",
            ]
        ],
        on="customer_group_key",
        how="left",
    )


def add_risk_features(features: pd.DataFrame) -> pd.DataFrame:
    """构造历史取消率和高风险国家/代理商标记。"""
    features = add_historical_rate(
        features, "customer_group_key", "is_canceled", "customer_group"
    )
    features = add_historical_rate(features, "country", "is_canceled", "country")
    features = add_historical_rate(features, "agent", "is_canceled", "agent")
    features = add_historical_rate(features, "hotel", "is_canceled", "hotel")

    country_threshold = features.loc[
        features["country_hist_booking_count"] >= 50,
        "country_hist_cancel_rate",
    ].quantile(0.75)
    agent_threshold = features.loc[
        features["agent_hist_booking_count"] >= 30,
        "agent_hist_cancel_rate",
    ].quantile(0.75)
    features["is_high_risk_country"] = (
        (features["country_hist_booking_count"] >= 50)
        & (features["country_hist_cancel_rate"] >= country_threshold)
    ).astype("int8")
    features["is_high_risk_agent"] = (
        (features["agent_hist_booking_count"] >= 30)
        & (features["agent_hist_cancel_rate"] >= agent_threshold)
    ).astype("int8")
    return features


def add_price_features(features: pd.DataFrame) -> pd.DataFrame:
    """构造价格相对水平、价格波动和价格敏感度特征。"""
    features = add_historical_mean(features, "hotel", "adr", "hotel")
    features = add_historical_mean(features, "city", "adr", "city")
    features = add_historical_mean(
        features, "customer_group_key", "adr", "customer_group"
    )

    for prefix in ["hotel", "city", "customer_group"]:
        features[f"price_to_{prefix}_hist_avg"] = (
            features["adr"] / features[f"{prefix}_hist_avg_adr"].replace(0, np.nan)
        ).replace([np.inf, -np.inf], np.nan).fillna(1).astype("float32")

    hotel_month_price = (
        features.groupby(["hotel", "arrival_month_num"], observed=False)["adr"]
        .agg(["mean", "std"])
        .reset_index()
        .rename(columns={"mean": "hotel_month_avg_adr", "std": "hotel_month_std_adr"})
    )
    hotel_month_price["price_volatility_index"] = (
        hotel_month_price["hotel_month_std_adr"]
        / hotel_month_price["hotel_month_avg_adr"].replace(0, np.nan)
    ).fillna(0)

    features = features.merge(
        hotel_month_price[["hotel", "arrival_month_num", "price_volatility_index"]],
        on=["hotel", "arrival_month_num"],
        how="left",
    )
    features["price_volatility_index"] = (
        features["price_volatility_index"].fillna(0).astype("float32")
    )
    features["price_sensitivity_score"] = percentile_score(
        features["price_to_customer_group_hist_avg"].astype("float64"),
        True,
    )
    return features


def add_revenue_management_features(features: pd.DataFrame) -> pd.DataFrame:
    """基于同酒店同入住日订单量构造需求紧张程度代理变量。"""
    hotel_day_demand = (
        features.groupby(["hotel", "arrival_date"], observed=False)
        .agg(hotel_daily_booking_count=("is_canceled", "size"))
        .reset_index()
    )
    hotel_day_demand["hotel_max_daily_booking_count"] = hotel_day_demand.groupby(
        "hotel", observed=False
    )["hotel_daily_booking_count"].transform("max")
    hotel_day_demand["estimated_occupancy_proxy"] = (
        hotel_day_demand["hotel_daily_booking_count"]
        / hotel_day_demand["hotel_max_daily_booking_count"].replace(0, np.nan)
    ).fillna(0)

    features = features.merge(
        hotel_day_demand[
            ["hotel", "arrival_date", "hotel_daily_booking_count", "estimated_occupancy_proxy"]
        ],
        on=["hotel", "arrival_date"],
        how="left",
    )
    features["demand_pressure_score"] = percentile_score(
        features["hotel_daily_booking_count"].astype("float64"),
        True,
    )
    return features


def add_business_score_features(features: pd.DataFrame) -> pd.DataFrame:
    """构造取消风险评分等业务导向评分特征。"""
    lead_time_score = features["lead_time"].rank(pct=True).astype("float32")
    deposit_risk_score = (
        features["deposit_type"]
        .astype(str)
        .map({"No Deposit": 0.3, "Refundable": 0.5, "Non Refund": 0.8})
        .fillna(0.3)
        .astype("float32")
    )
    special_request_protection = (
        1 - features["total_of_special_requests"].clip(upper=5) / 5
    ).astype("float32")
    features["cancellation_risk_score"] = (
        0.30 * features["customer_group_hist_cancel_rate"]
        + 0.20 * features["country_hist_cancel_rate"]
        + 0.15 * features["agent_hist_cancel_rate"]
        + 0.15 * lead_time_score
        + 0.10 * deposit_risk_score
        + 0.10 * special_request_protection
    ).clip(0, 1).astype("float32")
    return features


def build_features(data: pd.DataFrame) -> pd.DataFrame:
    """按第二阶段特征工程流程构造完整特征数据集。"""
    features = data.copy()
    features = add_time_features(features)
    features = add_booking_features(features)
    features = add_customer_group_features(features)
    features = add_risk_features(features)
    features = add_price_features(features)
    features = add_revenue_management_features(features)
    features = add_business_score_features(features)
    return features


def save_outputs(features: pd.DataFrame) -> None:
    """保存特征数据集。"""
    FEATURE_PARQUET_PATH.parent.mkdir(parents=True, exist_ok=True)
    features.to_parquet(FEATURE_PARQUET_PATH, index=False)


def main() -> None:
    """从清洗后数据生成特征工程数据集。"""
    data = load_cleaned_data()
    features = build_features(data)
    save_outputs(features)
    print("特征工程数据集已生成")
    print(f"输入数据：{CLEANED_PARQUET_PATH.relative_to(PROJECT_ROOT)}")
    print(f"输出数据：{FEATURE_PARQUET_PATH.relative_to(PROJECT_ROOT)}")
    print(f"数据规模：{features.shape[0]:,} 行，{features.shape[1]:,} 列")


if __name__ == "__main__":
    main()
