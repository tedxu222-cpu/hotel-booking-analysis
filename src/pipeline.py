"""项目流程统一入口。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.build_feature_dataset import main as build_feature_dataset  # noqa: E402
from src.features.preprocess_feature_dataset import preprocess_features  # noqa: E402


VALID_STEPS = {
    "features",
    "preprocess",
    "feature_pipeline",
}


def run_features() -> None:
    """运行特征工程，生成包含业务特征的 Parquet 数据。"""
    build_feature_dataset()


def run_preprocess() -> None:
    """运行特征预处理，生成训练集、验证集和测试集。"""
    preprocess_features()


def run_feature_pipeline() -> None:
    """依次运行特征工程和特征预处理。"""
    run_features()
    run_preprocess()


def run_pipeline(step: str) -> None:
    """根据指定步骤运行项目流程。"""
    if step == "features":
        run_features()
        return
    if step == "preprocess":
        run_preprocess()
        return
    if step == "feature_pipeline":
        run_feature_pipeline()
        return
    raise ValueError(f"未知流程步骤：{step}")


def parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="酒店预订取消预测项目流程统一入口。"
    )
    parser.add_argument(
        "--step",
        choices=sorted(VALID_STEPS),
        required=True,
        help=(
            "运行步骤：features=特征工程；"
            "preprocess=特征预处理；feature_pipeline=二者依次运行。"
        ),
    )
    return parser.parse_args()


def main() -> None:
    """命令行入口函数。"""
    args = parse_args()
    run_pipeline(args.step)


if __name__ == "__main__":
    main()
