# Python 工具包使用说明

本文档说明第四阶段封装后的 Python 模块如何使用。示例均假设当前工作目录为项目根目录 `hotel-booking-analysis/`。

## 0. 统一流程入口

项目提供统一 pipeline 入口，用于调用已有特征工程和特征预处理脚本。

```bash
python src/pipeline.py --step features
python src/pipeline.py --step preprocess
python src/pipeline.py --step feature_pipeline
```

三种模式含义：

- `features`：只运行特征工程，生成 `data/processed/hotel_booking_features.parquet`。
- `preprocess`：只运行特征预处理，生成训练集、验证集和测试集。
- `feature_pipeline`：先运行特征工程，再运行特征预处理。

Python 调用方式：

```python
from src.pipeline import run_feature_pipeline

run_feature_pipeline()
```

## 1. 建模数据读取与样本统计

```python
from src.models.dataset import (
    build_split_summary,
    compare_sampling_strategies,
    load_modeling_datasets,
    prepare_xy,
)

train_df, validation_df, test_df = load_modeling_datasets()

split_summary = build_split_summary(
    {
        "train": train_df,
        "validation": validation_df,
        "test": test_df,
    }
)

X_train, y_train = prepare_xy(train_df)
sampling_summary = compare_sampling_strategies(y_train)
```

主要用途：

- 读取第二阶段产出的训练集、验证集和测试集。
- 拆分特征矩阵 `X` 和目标变量 `y`。
- 检查训练集、验证集、测试集的样本量和取消率。
- 对比原始训练集、SMOTE、欠采样和类别权重调整方案的样本口径。

## 2. 传统模型训练与评估

```python
from src.models.dataset import load_modeling_datasets, prepare_xy
from src.models.traditional import build_baseline_models, fit_and_evaluate_model

train_df, validation_df, test_df = load_modeling_datasets()
X_train, y_train = prepare_xy(train_df)
X_validation, y_validation = prepare_xy(validation_df)
X_test, y_test = prepare_xy(test_df)

models = build_baseline_models(y_train)

records = fit_and_evaluate_model(
    "LightGBM",
    models["LightGBM"],
    X_train,
    y_train,
    {
        "validation": (X_validation, y_validation),
        "test": (X_test, y_test),
    },
)
```

主要用途：

- 构建逻辑回归、随机森林、XGBoost 和 LightGBM 基线模型。
- 使用统一指标评估模型，包括 AUC、accuracy、precision、recall 和 F1。
- 后续可以在 Notebook 中直接调用这些函数，减少重复代码。

## 3. 使用 Optuna 最优参数重建模型

```python
import pandas as pd

from src.config import PROJECT_ROOT
from src.models.dataset import load_modeling_datasets, prepare_xy
from src.models.traditional import build_best_model, params_for_model

train_df, validation_df, test_df = load_modeling_datasets()
X_train, y_train = prepare_xy(train_df)

best_params = pd.read_csv(PROJECT_ROOT / "reports" / "optuna_best_params.csv")
lightgbm_params = params_for_model(best_params, "LightGBM")

model = build_best_model("LightGBM", lightgbm_params, y_train=y_train)
model.fit(X_train, y_train)
```

主要用途：

- 复用第三阶段 Optuna 调优得到的最优参数。
- 避免每次复现实验都重新调参。

## 4. 保存模型供预测推理使用

```python
from src.config import BEST_MODEL_ARTIFACT_PATH
from src.models.traditional import save_model_artifact

save_model_artifact(
    model=model,
    feature_columns=X_train.columns.tolist(),
    output_path=BEST_MODEL_ARTIFACT_PATH,
    metadata={
        "model_name": "LightGBM",
        "target": "is_canceled",
    },
)
```

保存内容包括：

- 已训练模型对象。
- 训练时使用的特征列顺序。
- 模型名称、目标变量等元数据。

模型文件默认保存在 `models/` 目录，并已加入 `.gitignore`，避免把大文件提交到 GitHub。

## 5. 批量预测

```python
from src.config import BEST_MODEL_ARTIFACT_PATH
from src.models.predict import predict_batch

prediction_result = predict_batch(
    input_data="data/processed/modeling_dataset_test.parquet",
    model_artifact_path=BEST_MODEL_ARTIFACT_PATH,
    output_path="reports/batch_prediction_result.csv",
)
```

输出字段包括：

- `cancel_probability`：模型预测的取消概率。
- `predicted_cancel`：按默认阈值 `0.5` 得到的预测标签。
- `risk_segment`：低风险、中风险、高风险或极高风险。
- `suggested_action`：基于风险等级的简化业务动作建议。

## 6. 单条预测

```python
from src.config import BEST_MODEL_ARTIFACT_PATH
from src.models.predict import predict_single

one_order = {
    "lead_time_scaled": 0.5,
    "adr_scaled": 0.1,
    "total_stays_scaled": -0.2,
    # 这里需要补齐训练模型使用的全部特征字段。
}

prediction = predict_single(
    order_data=one_order,
    model_artifact_path=BEST_MODEL_ARTIFACT_PATH,
)
```

单条预测要求输入字段与训练模型时的特征字段一致。实际使用时，建议先通过特征工程和特征预处理脚本生成标准化后的建模字段，再调用预测接口。

## 7. 模型融合

```python
from src.models.ensemble import (
    fit_best_traditional_models,
    predict_probability_table,
    weighted_probability,
)

fitted_models = fit_best_traditional_models(best_params, X_train, y_train)
test_probability_table = predict_probability_table(fitted_models, X_test)

weighted_prob = weighted_probability(
    test_probability_table,
    {
        "XGBoost": 0.4,
        "LightGBM": 0.5,
        "MLP": 0.1,
    },
)
```

主要用途：

- 汇总多个模型的预测概率。
- 进行加权平均融合。
- 构建 Stacking 元学习器。

## 8. 业务模拟

```python
import numpy as np

from src.business.simulation import (
    assign_risk_segment,
    build_risk_segment_summary,
    simulate_business_thresholds,
)

risk_scores = assign_risk_segment(prediction_result)
risk_summary = build_risk_segment_summary(risk_scores)
threshold_result = simulate_business_thresholds(
    risk_scores,
    thresholds=np.arange(0.30, 0.81, 0.05),
)
```

主要用途：

- 将取消概率转换为业务风险等级。
- 统计不同风险层的订单量、取消率和收入表现。
- 模拟不同干预阈值下的覆盖率、召回率和净收益。
