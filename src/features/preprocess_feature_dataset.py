"""预处理特征数据集，并生成特征有效性评估报告。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold, mutual_info_classif
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import FEATURE_PARQUET_PATH, PROJECT_ROOT, TARGET_COLUMN  # noqa: E402


RANDOM_STATE = 42
plt.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
plt.rcParams["axes.unicode_minus"] = False
MODELING_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset.parquet"
TRAIN_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_train.parquet"
VALIDATION_DATASET_PATH = (
    PROJECT_ROOT / "data" / "processed" / "modeling_dataset_validation.parquet"
)
TEST_DATASET_PATH = PROJECT_ROOT / "data" / "processed" / "modeling_dataset_test.parquet"
PREPROCESSING_SUMMARY_PATH = PROJECT_ROOT / "reports" / "feature_preprocessing_summary.csv"
FEATURE_SELECTION_REPORT_PATH = PROJECT_ROOT / "reports" / "feature_selection_report.csv"
FEATURE_IMPORTANCE_REPORT_PATH = PROJECT_ROOT / "reports" / "feature_importance_preview.csv"
CORRELATION_HEATMAP_PATH = PROJECT_ROOT / "reports" / "feature_correlation_heatmap.png"
FEATURE_IMPORTANCE_FIGURE_PATH = PROJECT_ROOT / "reports" / "feature_importance_top20.png"


def sanitize_column_name(name: str) -> str:
    """清理编码后的列名，避免特殊字符影响后续保存和建模。"""
    return re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fff]+", "_", str(name)).strip("_")


def load_feature_data(path: Path = FEATURE_PARQUET_PATH) -> pd.DataFrame:
    """读取特征工程结果。"""
    if not path.exists():
        raise FileNotFoundError(f"特征工程数据不存在：{path}")
    return pd.read_parquet(path)


def select_candidate_features(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """剔除目标变量、结果字段和日期原值，得到建模候选特征。"""
    drop_columns = [
        TARGET_COLUMN,
        "reservation_status",
        "reservation_status_date",
        "arrival_date",
    ]
    existing_drop_columns = [col for col in drop_columns if col in data.columns]
    candidate_features = data.drop(columns=existing_drop_columns).copy()
    datetime_columns = candidate_features.select_dtypes(include=["datetime"]).columns
    if len(datetime_columns) > 0:
        candidate_features = candidate_features.drop(columns=datetime_columns)
    target = data[TARGET_COLUMN].astype("int8")
    return candidate_features, target


def split_data(
    features: pd.DataFrame,
    target: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """按 7/2/1 分层划分训练集、验证集和测试集。"""
    x_train, x_temp, y_train, y_temp = train_test_split(
        features,
        target,
        test_size=0.3,
        random_state=RANDOM_STATE,
        stratify=target,
    )
    x_validation, x_test, y_validation, y_test = train_test_split(
        x_temp,
        y_temp,
        test_size=1 / 3,
        random_state=RANDOM_STATE,
        stratify=y_temp,
    )
    return x_train, x_validation, x_test, y_train, y_validation, y_test


def fit_target_encoding(
    train_frame: pd.DataFrame,
    target: pd.Series,
    columns: list[str],
    smoothing: int = 20,
) -> tuple[dict[str, dict[object, float]], float]:
    """在训练集上拟合平滑 Target Encoding 映射。"""
    global_mean = float(target.mean())
    mappings = {}
    train_target = train_frame.copy()
    train_target[TARGET_COLUMN] = target.values

    for column in columns:
        stats = train_target.groupby(column, dropna=False, observed=False)[
            TARGET_COLUMN
        ].agg(["mean", "count"])
        smooth_value = (
            stats["mean"] * stats["count"] + global_mean * smoothing
        ) / (stats["count"] + smoothing)
        mappings[column] = smooth_value.to_dict()
    return mappings, global_mean


def transform_target_encoding(
    frame: pd.DataFrame,
    columns: list[str],
    mappings: dict[str, dict[object, float]],
    global_mean: float,
) -> pd.DataFrame:
    """使用训练集映射转换类别字段，未知类别填充训练集目标均值。"""
    encoded = pd.DataFrame(index=frame.index)
    for column in columns:
        encoded[f"{column}_target_encoded"] = (
            frame[column].map(mappings[column]).fillna(global_mean).astype("float32")
        )
    return encoded


def encode_categorical_features(
    x_train: pd.DataFrame,
    x_validation: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str], list[str]]:
    """对高维类别字段做 Target Encoding，对低维类别字段做 One-Hot。"""
    categorical_columns = x_train.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()
    target_encoding_columns = [
        col for col in ["country", "agent", "hotel", "customer_group_key"] if col in x_train.columns
    ]
    low_cardinality_columns = [
        col for col in categorical_columns if col not in target_encoding_columns
    ]

    mappings, global_mean = fit_target_encoding(
        x_train,
        y_train,
        target_encoding_columns,
    )
    target_train = transform_target_encoding(
        x_train,
        target_encoding_columns,
        mappings,
        global_mean,
    )
    target_validation = transform_target_encoding(
        x_validation,
        target_encoding_columns,
        mappings,
        global_mean,
    )
    target_test = transform_target_encoding(
        x_test,
        target_encoding_columns,
        mappings,
        global_mean,
    )

    one_hot_train = pd.get_dummies(
        x_train[low_cardinality_columns].astype(str),
        prefix=[sanitize_column_name(col) for col in low_cardinality_columns],
        dummy_na=False,
        dtype="int8",
    )
    one_hot_validation = pd.get_dummies(
        x_validation[low_cardinality_columns].astype(str),
        prefix=[sanitize_column_name(col) for col in low_cardinality_columns],
        dummy_na=False,
        dtype="int8",
    )
    one_hot_test = pd.get_dummies(
        x_test[low_cardinality_columns].astype(str),
        prefix=[sanitize_column_name(col) for col in low_cardinality_columns],
        dummy_na=False,
        dtype="int8",
    )
    one_hot_train, one_hot_validation = one_hot_train.align(
        one_hot_validation,
        join="left",
        axis=1,
        fill_value=0,
    )
    one_hot_train, one_hot_test = one_hot_train.align(
        one_hot_test,
        join="left",
        axis=1,
        fill_value=0,
    )
    one_hot_validation = one_hot_validation.reindex(
        columns=one_hot_train.columns,
        fill_value=0,
    ).astype("int8")
    one_hot_test = one_hot_test.reindex(
        columns=one_hot_train.columns,
        fill_value=0,
    ).astype("int8")

    encoded_train = pd.concat([target_train, one_hot_train], axis=1)
    encoded_validation = pd.concat([target_validation, one_hot_validation], axis=1)
    encoded_test = pd.concat([target_test, one_hot_test], axis=1)
    return (
        encoded_train,
        encoded_validation,
        encoded_test,
        target_encoding_columns,
        low_cardinality_columns,
    )


def scale_numeric_features(
    x_train: pd.DataFrame,
    x_validation: pd.DataFrame,
    x_test: pd.DataFrame,
    target_encoding_columns: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    """对数值字段做缺失检查，并使用训练集拟合 StandardScaler。"""
    numeric_columns = x_train.select_dtypes(include=["number", "bool"]).columns.tolist()
    numeric_columns = [col for col in numeric_columns if col not in target_encoding_columns]
    numeric_train = x_train[numeric_columns].copy()
    numeric_validation = x_validation[numeric_columns].copy()
    numeric_test = x_test[numeric_columns].copy()

    missing_summary = pd.DataFrame(
        {
            "train_missing": numeric_train.isna().sum(),
            "validation_missing": numeric_validation.isna().sum(),
            "test_missing": numeric_test.isna().sum(),
        }
    )
    missing_summary = missing_summary[
        (missing_summary["train_missing"] > 0)
        | (missing_summary["validation_missing"] > 0)
        | (missing_summary["test_missing"] > 0)
    ]
    if not missing_summary.empty:
        raise ValueError("数值字段仍存在缺失值，请先回到数据清洗或特征工程阶段处理。")

    scaler = StandardScaler()
    scaled_train = pd.DataFrame(
        scaler.fit_transform(numeric_train),
        columns=[f"{col}_scaled" for col in numeric_columns],
        index=x_train.index,
    )
    scaled_validation = pd.DataFrame(
        scaler.transform(numeric_validation),
        columns=[f"{col}_scaled" for col in numeric_columns],
        index=x_validation.index,
    )
    scaled_test = pd.DataFrame(
        scaler.transform(numeric_test),
        columns=[f"{col}_scaled" for col in numeric_columns],
        index=x_test.index,
    )
    return scaled_train, scaled_validation, scaled_test, numeric_columns


def apply_variance_threshold(
    x_train: pd.DataFrame,
    x_validation: pd.DataFrame,
    x_test: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """使用方差阈值删除常量特征。"""
    selector = VarianceThreshold(threshold=0.0)
    selector.fit(x_train)
    variance_report = pd.DataFrame(
        {
            "feature_name": x_train.columns,
            "variance": selector.variances_,
            "kept_by_variance_threshold": selector.get_support(),
        }
    )
    kept_features = variance_report.loc[
        variance_report["kept_by_variance_threshold"],
        "feature_name",
    ].tolist()
    return (
        x_train[kept_features],
        x_validation[kept_features],
        x_test[kept_features],
        variance_report,
    )


def evaluate_features(
    x_train: pd.DataFrame,
    x_validation: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_validation: pd.Series,
    y_test: pd.Series,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    """生成相关性、互信息和随机森林重要性评估结果。"""
    correlation_report = (
        x_train.corrwith(y_train)
        .fillna(0)
        .rename("target_correlation")
        .reset_index()
        .rename(columns={"index": "feature_name"})
    )
    correlation_report["abs_target_correlation"] = (
        correlation_report["target_correlation"].abs()
    )

    sample_size = min(30000, x_train.shape[0])
    mi_sample = x_train.sample(n=sample_size, random_state=RANDOM_STATE)
    y_mi_sample = y_train.loc[mi_sample.index]
    mutual_information = mutual_info_classif(
        mi_sample,
        y_mi_sample,
        discrete_features=False,
        random_state=RANDOM_STATE,
    )
    mi_report = pd.DataFrame(
        {
            "feature_name": mi_sample.columns,
            "mutual_information": mutual_information,
        }
    )

    model = RandomForestClassifier(
        n_estimators=120,
        max_depth=8,
        min_samples_leaf=50,
        n_jobs=-1,
        random_state=RANDOM_STATE,
        class_weight="balanced_subsample",
    )
    model.fit(x_train, y_train)
    auc_scores = {
        "random_forest_preview_train_auc": roc_auc_score(
            y_train,
            model.predict_proba(x_train)[:, 1],
        ),
        "random_forest_preview_validation_auc": roc_auc_score(
            y_validation,
            model.predict_proba(x_validation)[:, 1],
        ),
        "random_forest_preview_test_auc": roc_auc_score(
            y_test,
            model.predict_proba(x_test)[:, 1],
        ),
    }
    importance_report = pd.DataFrame(
        {
            "feature_name": x_train.columns,
            "rf_importance": model.feature_importances_,
        }
    ).sort_values("rf_importance", ascending=False)

    feature_report = (
        correlation_report.merge(mi_report, on="feature_name", how="left")
        .merge(importance_report, on="feature_name", how="left")
        .fillna(0)
    )
    return feature_report, importance_report, auc_scores


def save_evaluation_figures(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    feature_report: pd.DataFrame,
    importance_report: pd.DataFrame,
) -> None:
    """保存相关性热力图和特征重要性排序图。"""
    REPORT_FIGURE_DIR = CORRELATION_HEATMAP_PATH.parent
    REPORT_FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    top_corr_features = (
        feature_report.sort_values("abs_target_correlation", ascending=False)
        .head(20)["feature_name"]
        .tolist()
    )
    heatmap_data = x_train[top_corr_features].copy()
    heatmap_data[TARGET_COLUMN] = y_train.values
    plt.figure(figsize=(12, 10))
    sns.heatmap(
        heatmap_data.corr(),
        cmap="RdBu_r",
        center=0,
        linewidths=0.2,
        cbar_kws={"label": "相关系数"},
    )
    plt.title("Top 20 特征与目标变量相关性热力图")
    plt.tight_layout()
    plt.savefig(CORRELATION_HEATMAP_PATH, dpi=160, bbox_inches="tight")
    plt.close()

    top_importance = importance_report.head(20).sort_values("rf_importance")
    plt.figure(figsize=(10, 7))
    sns.barplot(
        data=top_importance,
        x="rf_importance",
        y="feature_name",
        color="#4C78A8",
    )
    plt.title("随机森林特征重要性 Top 20")
    plt.xlabel("重要性")
    plt.ylabel("特征")
    plt.tight_layout()
    plt.savefig(FEATURE_IMPORTANCE_FIGURE_PATH, dpi=160, bbox_inches="tight")
    plt.close()


def save_outputs(
    x_train: pd.DataFrame,
    x_validation: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_validation: pd.Series,
    y_test: pd.Series,
    feature_selection_report: pd.DataFrame,
    importance_report: pd.DataFrame,
    preprocessing_summary: pd.DataFrame,
) -> None:
    """保存建模数据和评估报告。"""
    train_output = x_train.copy()
    train_output[TARGET_COLUMN] = y_train.values
    train_output["dataset_split"] = "train"

    validation_output = x_validation.copy()
    validation_output[TARGET_COLUMN] = y_validation.values
    validation_output["dataset_split"] = "validation"

    test_output = x_test.copy()
    test_output[TARGET_COLUMN] = y_test.values
    test_output["dataset_split"] = "test"

    modeling_dataset = pd.concat([train_output, validation_output, test_output], axis=0)
    modeling_dataset = modeling_dataset.sort_index()

    TRAIN_DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREPROCESSING_SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    train_output.to_parquet(TRAIN_DATASET_PATH, index=False)
    validation_output.to_parquet(VALIDATION_DATASET_PATH, index=False)
    test_output.to_parquet(TEST_DATASET_PATH, index=False)
    modeling_dataset.to_parquet(MODELING_DATASET_PATH, index=False)
    feature_selection_report.to_csv(
        FEATURE_SELECTION_REPORT_PATH,
        index=False,
        encoding="utf-8-sig",
    )
    importance_report.to_csv(
        FEATURE_IMPORTANCE_REPORT_PATH,
        index=False,
        encoding="utf-8-sig",
    )
    preprocessing_summary.to_csv(
        PREPROCESSING_SUMMARY_PATH,
        index=False,
        encoding="utf-8-sig",
    )


def preprocess_features() -> None:
    """执行特征预处理与有效性评估主流程。"""
    data = load_feature_data()
    candidates, target = select_candidate_features(data)
    x_train, x_validation, x_test, y_train, y_validation, y_test = split_data(
        candidates,
        target,
    )
    (
        encoded_train,
        encoded_validation,
        encoded_test,
        target_encoding_columns,
        low_cardinality_columns,
    ) = encode_categorical_features(x_train, x_validation, x_test, y_train)
    scaled_train, scaled_validation, scaled_test, numeric_columns = scale_numeric_features(
        x_train,
        x_validation,
        x_test,
        target_encoding_columns,
    )

    processed_train = pd.concat([scaled_train, encoded_train], axis=1)
    processed_validation = pd.concat([scaled_validation, encoded_validation], axis=1)
    processed_test = pd.concat([scaled_test, encoded_test], axis=1)
    processed_train.columns = [sanitize_column_name(col) for col in processed_train.columns]
    processed_validation.columns = [
        sanitize_column_name(col) for col in processed_validation.columns
    ]
    processed_test.columns = [sanitize_column_name(col) for col in processed_test.columns]

    x_train_final, x_validation_final, x_test_final, variance_report = (
        apply_variance_threshold(processed_train, processed_validation, processed_test)
    )
    feature_report, importance_report, auc_scores = evaluate_features(
        x_train_final,
        x_validation_final,
        x_test_final,
        y_train,
        y_validation,
        y_test,
    )
    feature_selection_report = variance_report.merge(
        feature_report,
        on="feature_name",
        how="left",
    ).fillna(0)
    feature_selection_report["has_target_encoded_source"] = feature_selection_report[
        "feature_name"
    ].str.contains("target_encoded", regex=False)
    feature_selection_report["is_target_derived_feature"] = feature_selection_report[
        "feature_name"
    ].str.contains("hist_cancel_rate|risk_score|high_risk", regex=True)
    feature_selection_report["overall_preview_rank"] = (
        feature_selection_report["abs_target_correlation"].rank(ascending=False)
        + feature_selection_report["mutual_information"].rank(ascending=False)
        + feature_selection_report["rf_importance"].rank(ascending=False)
    )
    feature_selection_report = feature_selection_report.sort_values(
        "overall_preview_rank"
    )

    preprocessing_summary = pd.DataFrame(
        [
            ("input_rows", data.shape[0]),
            ("input_columns", data.shape[1]),
            ("candidate_features", candidates.shape[1]),
            ("train_rows", x_train.shape[0]),
            ("validation_rows", x_validation.shape[0]),
            ("test_rows", x_test.shape[0]),
            ("numeric_scaled_features", len(numeric_columns)),
            ("target_encoded_features", len(target_encoding_columns)),
            ("one_hot_source_features", len(low_cardinality_columns)),
            ("one_hot_output_features", encoded_train.shape[1] - len(target_encoding_columns)),
            ("processed_train_features_before_variance", processed_train.shape[1]),
            ("processed_train_features_after_variance", x_train_final.shape[1]),
            *[(key, round(value, 6)) for key, value in auc_scores.items()],
        ],
        columns=["metric", "value"],
    )

    save_evaluation_figures(
        x_train_final,
        y_train,
        feature_selection_report,
        importance_report,
    )
    save_outputs(
        x_train_final,
        x_validation_final,
        x_test_final,
        y_train,
        y_validation,
        y_test,
        feature_selection_report,
        importance_report,
        preprocessing_summary,
    )

    print("特征预处理与有效性评估已完成")
    print(f"训练集：{TRAIN_DATASET_PATH.relative_to(PROJECT_ROOT)}")
    print(f"验证集：{VALIDATION_DATASET_PATH.relative_to(PROJECT_ROOT)}")
    print(f"测试集：{TEST_DATASET_PATH.relative_to(PROJECT_ROOT)}")
    print(f"特征筛选报告：{FEATURE_SELECTION_REPORT_PATH.relative_to(PROJECT_ROOT)}")
    print(f"相关性热力图：{CORRELATION_HEATMAP_PATH.relative_to(PROJECT_ROOT)}")
    print(f"重要性排序图：{FEATURE_IMPORTANCE_FIGURE_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    preprocess_features()
