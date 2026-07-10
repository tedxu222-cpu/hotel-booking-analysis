import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import src.pipeline as pipeline
from src.models.dataset import build_split_summary, prepare_xy
from src.models.evaluation import classification_metrics_from_probability
from src.models.predict import assign_risk_segment, predict_batch, predict_dataframe
from src.models.traditional import save_model_artifact


class DummyProbabilityModel:
    """用于测试预测接口的简化二分类模型。"""

    def predict_proba(self, x_data):
        probability = np.clip(x_data["feature_a"].to_numpy(), 0, 1)
        return np.column_stack([1 - probability, probability])


class ModelPackageTest(unittest.TestCase):
    def test_prepare_xy_removes_target_and_split_column(self):
        data = pd.DataFrame(
            {
                "feature_a": [0.1, 0.8],
                "dataset_split": ["train", "train"],
                "is_canceled": [0, 1],
            }
        )

        x_data, y_data = prepare_xy(data)

        self.assertEqual(x_data.columns.tolist(), ["feature_a"])
        self.assertEqual(y_data.tolist(), [0, 1])

    def test_build_split_summary_counts_target_distribution(self):
        data = pd.DataFrame({"is_canceled": [0, 0, 1, 1]})

        summary = build_split_summary({"test": data})

        self.assertEqual(int(summary.loc[0, "total_count"]), 4)
        self.assertEqual(int(summary.loc[0, "canceled_count"]), 2)
        self.assertEqual(float(summary.loc[0, "canceled_ratio"]), 0.5)

    def test_classification_metrics_from_probability(self):
        metrics = classification_metrics_from_probability(
            y_true=np.array([0, 1, 1, 0]),
            positive_probability=np.array([0.1, 0.8, 0.7, 0.2]),
        )

        self.assertEqual(metrics["auc"], 1.0)
        self.assertEqual(metrics["f1"], 1.0)

    def test_predict_dataframe_adds_prediction_columns(self):
        data = pd.DataFrame({"feature_a": [0.2, 0.9]})

        result = predict_dataframe(
            data=data,
            model=DummyProbabilityModel(),
            feature_columns=["feature_a"],
        )

        self.assertIn("cancel_probability", result.columns)
        self.assertIn("predicted_cancel", result.columns)
        self.assertIn("risk_segment", result.columns)
        self.assertIn("suggested_action", result.columns)

    def test_predict_batch_with_saved_artifact(self):
        data = pd.DataFrame({"feature_a": [0.2, 0.9]})
        with tempfile.TemporaryDirectory() as temp_dir:
            model_path = Path(temp_dir) / "dummy_model.pkl"
            save_model_artifact(
                model=DummyProbabilityModel(),
                feature_columns=["feature_a"],
                output_path=model_path,
            )

            result = predict_batch(data, model_artifact_path=model_path)

        self.assertEqual(result["predicted_cancel"].tolist(), [0, 1])

    def test_assign_risk_segment(self):
        result = assign_risk_segment(np.array([0.1, 0.4, 0.6, 0.9]))

        self.assertEqual(result.tolist(), ["低风险", "中风险", "高风险", "极高风险"])

    def test_pipeline_dispatch(self):
        called_steps = []

        original_run_features = pipeline.run_features
        original_run_preprocess = pipeline.run_preprocess
        try:
            pipeline.run_features = lambda: called_steps.append("features")
            pipeline.run_preprocess = lambda: called_steps.append("preprocess")

            pipeline.run_pipeline("feature_pipeline")
        finally:
            pipeline.run_features = original_run_features
            pipeline.run_preprocess = original_run_preprocess

        self.assertEqual(called_steps, ["features", "preprocess"])


if __name__ == "__main__":
    unittest.main()
