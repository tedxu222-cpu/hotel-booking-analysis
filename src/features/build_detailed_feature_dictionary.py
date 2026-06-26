"""生成包含计算逻辑、预处理方式和区分度评估的详细特征字典。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd


SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import PROJECT_ROOT  # noqa: E402


FEATURE_DICTIONARY_PATH = PROJECT_ROOT / "reports" / "feature_dictionary.csv"
FEATURE_SELECTION_REPORT_PATH = PROJECT_ROOT / "reports" / "feature_selection_report.csv"


TARGET_ENCODING_FEATURES = {
    "country",
    "agent",
    "hotel",
    "customer_group_key",
}
ONE_HOT_FEATURES = {
    "hotel_type",
    "arrival_month",
    "arrival_quarter_label",
    "holiday_proxy",
    "season_type",
    "lead_time_group",
    "special_request_group",
    "rfm_segment",
}


def sanitize_column_name(name: str) -> str:
    """清理字段名，保持与特征预处理脚本中的编码列名规则一致。"""
    return re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fff]+", "_", str(name)).strip("_")


def infer_calculation_logic(row: pd.Series) -> str:
    """根据特征名称和来源字段生成计算逻辑说明。"""
    feature_name = row["feature_name"]
    source = row["source"]
    category = row["feature_category"]

    if feature_name.startswith("arrival_"):
        return f"由 {source} 拆分或格式化得到。"
    if feature_name in {"is_weekend", "is_holiday_proxy", "holiday_proxy"}:
        return "由入住日期星期几判断，周六和周日记为周末/节假日代理。"
    if feature_name == "is_near_holiday_proxy":
        return "由入住日期星期几判断，周五和周一记为靠近周末节假日代理。"
    if feature_name in {"season_type", "is_peak_season", "is_low_season"}:
        return "按月度预订量分位数划分淡季、平季和旺季，再生成对应标记。"
    if feature_name == "total_guests":
        return "adults、children、babies 三个字段求和。"
    if feature_name == "total_stays":
        return "stays_in_weekend_nights 与 stays_in_week_nights 求和。"
    if feature_name == "room_type_matched":
        return "比较 reserved_room_type 与 assigned_room_type 是否一致。"
    if feature_name.startswith("has_"):
        return f"根据 {source} 是否大于 0 或是否满足条件生成 0/1 标记。"
    if feature_name.endswith("_group"):
        return f"根据 {source} 做业务分组或合并低频/极端取值。"
    if feature_name in {"customer_group_key", "rfm_value_score", "rfm_segment"}:
        return "按客户类型、市场细分、分销渠道和是否回头客构造客户群体，再基于群体 RFM 规则计算。"
    if "hist_cancel_rate" in feature_name:
        return f"按 {source} 分组，按时间顺序计算当前记录之前的历史取消率。"
    if "hist_booking_count" in feature_name:
        return f"按 {source} 分组，按时间顺序累计当前记录之前的历史订单数。"
    if feature_name.startswith("is_high_risk"):
        return "在历史订单数达到阈值的前提下，按历史取消率上四分位数生成高风险标记。"
    if feature_name.startswith("price_to_"):
        return "当前 ADR 除以对应维度的历史平均 ADR。"
    if feature_name == "price_volatility_index":
        return "按酒店和入住月份计算 ADR 标准差与均值的比值。"
    if feature_name == "price_sensitivity_score":
        return "按客户群体历史价格比值的百分位进行 1-5 分打分。"
    if feature_name == "estimated_revenue":
        return "ADR 乘以总入住晚数，最低按 1 晚估算。"
    if feature_name in {"estimated_occupancy_proxy", "demand_pressure_score"}:
        return "按同酒店同入住日预订量构造需求代理，再进行比例化或百分位打分。"
    if feature_name == "cancellation_risk_score":
        return "加权合成历史取消率、提前预订天数、订金类型和特殊需求等风险信号。"
    if "评分" in category:
        return "基于业务规则或百分位打分规则计算。"
    return f"由 {source} 派生，具体含义见 description。"


def infer_preprocessing_method(feature_name: str) -> str:
    """说明该特征在建模预处理阶段的处理方式。"""
    if feature_name in TARGET_ENCODING_FEATURES:
        return "高维类别字段，使用平滑 Target Encoding。"
    if feature_name in ONE_HOT_FEATURES:
        return "低维类别字段，使用 One-Hot Encoding。"
    if feature_name in {"customer_group_key"}:
        return "高维客户群体键，使用平滑 Target Encoding。"
    if feature_name in {"reservation_status", "reservation_status_date"}:
        return "结果相关字段，建模阶段剔除。"
    return "数值型或布尔型字段，使用训练集拟合 StandardScaler 后标准化。"


def find_processed_rows(
    feature_name: str,
    selection_report: pd.DataFrame,
) -> pd.DataFrame:
    """在特征筛选报告中寻找与原始特征对应的预处理后字段。"""
    sanitized = sanitize_column_name(feature_name)
    candidates = {
        feature_name,
        sanitized,
        f"{feature_name}_scaled",
        f"{sanitized}_scaled",
        f"{feature_name}_target_encoded",
        f"{sanitized}_target_encoded",
    }
    matched = selection_report[selection_report["feature_name"].isin(candidates)]
    if not matched.empty:
        return matched

    prefix = f"{sanitized}_"
    return selection_report[
        selection_report["feature_name"].astype(str).str.startswith(prefix)
    ]


def summarize_discrimination(
    feature_name: str,
    selection_report: pd.DataFrame,
) -> str:
    """基于相关性、互信息和随机森林重要性生成区分度评估说明。"""
    matched = find_processed_rows(feature_name, selection_report)
    if matched.empty:
        return "未在预处理后特征评估报告中匹配到对应字段。"

    best = matched.sort_values(
        ["abs_target_correlation", "mutual_information", "rf_importance"],
        ascending=False,
    ).iloc[0]
    return (
        f"匹配 {len(matched)} 个预处理后字段；最高 |相关系数|="
        f"{best['abs_target_correlation']:.4f}，互信息="
        f"{best['mutual_information']:.4f}，随机森林重要性="
        f"{best['rf_importance']:.4f}。"
    )


def build_detailed_feature_dictionary() -> pd.DataFrame:
    """生成并保存详细特征字典。"""
    if not FEATURE_DICTIONARY_PATH.exists():
        raise FileNotFoundError(f"特征字典不存在：{FEATURE_DICTIONARY_PATH}")
    if not FEATURE_SELECTION_REPORT_PATH.exists():
        raise FileNotFoundError(f"特征评估报告不存在：{FEATURE_SELECTION_REPORT_PATH}")

    dictionary = pd.read_csv(FEATURE_DICTIONARY_PATH)
    selection_report = pd.read_csv(FEATURE_SELECTION_REPORT_PATH)
    dictionary["calculation_logic"] = dictionary.apply(infer_calculation_logic, axis=1)
    dictionary["preprocessing_method"] = dictionary["feature_name"].map(
        infer_preprocessing_method
    )
    dictionary["discrimination_evaluation"] = dictionary["feature_name"].map(
        lambda name: summarize_discrimination(name, selection_report)
    )
    dictionary["evaluation_source"] = "reports/feature_selection_report.csv"
    dictionary.to_csv(FEATURE_DICTIONARY_PATH, index=False, encoding="utf-8-sig")
    return dictionary


def main() -> None:
    """生成详细特征字典。"""
    dictionary = build_detailed_feature_dictionary()
    print("详细特征字典已生成")
    print(f"输出路径：{FEATURE_DICTIONARY_PATH.relative_to(PROJECT_ROOT)}")
    print(f"字段数量：{dictionary.shape[0]:,}，说明列数：{dictionary.shape[1]:,}")


if __name__ == "__main__":
    main()
