# 用户手册

本文档面向需要复现、维护或使用本项目工具包的团队成员，说明项目目录、运行顺序、主要脚本和模型预测接口的使用方法。

## 1. 项目简介

本项目用于分析酒店预订行为，并预测订单是否会被取消。项目已经覆盖数据清洗、SQLite 数据库构建、SQL 分析、特征工程、探索性数据分析、模型训练、模型解释、业务模拟和工程化封装。

目标变量为 `is_canceled`，表示订单是否取消。

## 2. 目录结构

```text
hotel-booking-analysis/
├── data/                    # 本地数据目录，原始数据和中间数据不提交到 GitHub
├── docs/                    # 项目说明、API 文档、用户手册和数据库设计说明
├── notebooks/               # 分阶段 Notebook
├── reports/                 # 阶段报告、图表、指标结果和分析输出
├── sql/                     # SQL 查询脚本
├── src/                     # 可复用 Python 代码
├── tests/                   # 单元测试
├── requirements.txt         # Python 依赖
└── README.md                # 项目总览
```

## 3. 环境安装

建议在项目根目录下安装依赖：

```bash
pip install -r requirements.txt
```

主要依赖包括：

- `pandas`、`numpy`
- `matplotlib`、`seaborn`
- `scikit-learn`
- `xgboost`、`lightgbm`
- `optuna`
- `tensorflow`
- `shap`
- `pyarrow`

## 4. 数据准备

原始数据文件需要放在：

```text
data/raw/hotel_bookings_updated_2024.csv
```

原始数据、清洗后数据、建模数据和 SQLite 数据库体积较大，当前不提交到 GitHub。团队成员需要在本地准备数据，然后按流程生成中间文件。

## 5. 推荐运行顺序

### 5.1 数据清洗

主要 Notebook：

```text
notebooks/data_preprocessing.ipynb
```

相关脚本：

```text
src/data/data_quality_check.py
src/data/data_preprocessing.py
```

主要输出：

```text
data/processed/hotel_bookings_cleaned.csv
data/processed/hotel_bookings_cleaned.parquet
```

### 5.2 构建 SQLite 数据库

```bash
python src/database/build_sqlite_database.py
```

主要输出：

```text
data/database/hotel_booking.db
```

### 5.3 运行 SQL 分析

```bash
python src/database/run_sql_analysis.py
```

主要输出：

```text
reports/sql_analysis/
```

### 5.4 构建特征工程数据集

```bash
python src/features/build_feature_dataset.py
```

主要输出：

```text
data/processed/hotel_booking_features.parquet
```

### 5.5 特征预处理与数据划分

```bash
python src/features/preprocess_feature_dataset.py
```

主要输出：

```text
data/processed/modeling_dataset_train.parquet
data/processed/modeling_dataset_validation.parquet
data/processed/modeling_dataset_test.parquet
```

也可以使用统一流程入口依次运行特征工程和特征预处理：

```bash
python src/pipeline.py --step feature_pipeline
```

### 5.6 模型训练、融合、解释和业务模拟

主要 Notebook：

```text
notebooks/modeling_sample_construction.ipynb
```

该 Notebook 负责完成样本构建复核、传统模型训练与调优、深度学习模型、模型融合、解释性分析、错误样本分析和业务落地模拟。

## 6. Python 工具包说明

### 6.1 数据集工具

位置：

```text
src/models/dataset.py
```

主要函数：

- `load_modeling_datasets()`：读取训练集、验证集和测试集。
- `prepare_xy()`：拆分特征矩阵和目标变量。
- `build_split_summary()`：统计数据集样本量和取消率。
- `compare_sampling_strategies()`：对比样本不平衡处理方案。
- `split_by_hotel_type()`：按城市酒店和度假酒店拆分样本。

### 6.2 模型评估工具

位置：

```text
src/models/evaluation.py
```

主要函数：

- `classification_metrics_from_probability()`：根据预测概率计算 AUC、accuracy、precision、recall 和 F1。
- `evaluate_model()`：评估支持 `predict_proba` 的模型。
- `evaluate_probability_series()`：评估单模型或融合模型的预测概率。

### 6.3 传统模型工具

位置：

```text
src/models/traditional.py
```

主要函数：

- `build_baseline_models()`：构建逻辑回归、随机森林、XGBoost 和 LightGBM 基线模型。
- `build_best_model()`：根据 Optuna 最优参数重建模型。
- `make_objective()`：构建 Optuna 调优目标函数。
- `save_model_artifact()`：保存模型、特征列和元数据。
- `load_model_artifact()`：加载已保存模型。

### 6.4 深度学习辅助工具

位置：

```text
src/models/deep_learning.py
```

主要函数：

- `build_mlp_model()`：构建普通 MLP 模型。
- `build_embedding_mlp_model()`：构建带类别 Embedding 的 MLP 模型。
- `build_training_callbacks()`：构建 Early Stopping 和学习率衰减回调。
- `build_training_history_records()`：将 Keras 训练历史转换为逐 epoch 记录。
- `replace_model_rows()`：重复运行时用新结果替换旧模型结果，避免 CSV 中出现重复行。

### 6.5 模型融合工具

位置：

```text
src/models/ensemble.py
```

主要函数：

- `fit_best_traditional_models()`：用最优参数训练传统模型。
- `predict_probability_table()`：汇总多个模型的预测概率。
- `weighted_probability()`：执行加权平均融合。
- `fit_stacking_model()`：训练 Stacking 元学习器。
- `predict_stacking_probability()`：输出 Stacking 融合概率。

### 6.6 预测推理接口

位置：

```text
src/models/predict.py
```

支持两种预测模式：

- `predict_batch()`：批量预测。
- `predict_single()`：单条预测。

输出字段包括：

- `cancel_probability`：取消概率。
- `predicted_cancel`：预测取消标签。
- `risk_segment`：风险等级。
- `suggested_action`：简化业务动作建议。

### 6.7 业务模拟工具

位置：

```text
src/business/simulation.py
```

主要函数：

- `assign_risk_segment()`：根据取消概率生成风险分层。
- `build_risk_segment_summary()`：统计不同风险层的订单量、取消率和收入表现。
- `simulate_business_thresholds()`：模拟不同干预阈值下的潜在净收益。

## 7. 批量预测示例

批量预测前需要先保存模型文件，例如：

```python
from src.config import BEST_MODEL_ARTIFACT_PATH
from src.models.traditional import save_model_artifact

save_model_artifact(
    model=model,
    feature_columns=X_train.columns.tolist(),
    output_path=BEST_MODEL_ARTIFACT_PATH,
    metadata={"model_name": "LightGBM", "target": "is_canceled"},
)
```

然后执行批量预测：

```python
from src.config import BEST_MODEL_ARTIFACT_PATH
from src.models.predict import predict_batch

result = predict_batch(
    input_data="data/processed/modeling_dataset_test.parquet",
    model_artifact_path=BEST_MODEL_ARTIFACT_PATH,
    output_path="reports/batch_prediction_result.csv",
)
```

## 8. 单条预测示例

```python
from src.config import BEST_MODEL_ARTIFACT_PATH
from src.models.predict import predict_single

one_order = {
    "lead_time_scaled": 0.5,
    "adr_scaled": 0.1,
    "total_stays_scaled": -0.2,
    # 实际使用时需要补齐训练模型使用的全部特征字段。
}

prediction = predict_single(
    order_data=one_order,
    model_artifact_path=BEST_MODEL_ARTIFACT_PATH,
)
```

注意：单条预测输入必须包含训练模型所需的全部特征字段。实际业务使用时，建议先通过特征工程和特征预处理流程生成标准化后的建模字段，再调用预测接口。

## 9. 单元测试

运行基础测试：

```bash
python -m unittest discover -s tests -p "test_*.py"
```

当前测试主要覆盖：

- 建模数据拆分。
- 样本统计。
- 指标计算。
- 批量预测和单条预测相关基础逻辑。
- 风险等级划分。

## 10. 注意事项

### 10.1 数据文件不提交到 GitHub

原始数据和中间数据文件较大，并且可以通过本地脚本复现，因此不提交到 GitHub。

### 10.2 预测前需要先生成标准建模字段

模型训练使用的是经过特征构造、编码和标准化后的建模字段，不是直接使用原始订单字段。项目已经提供批量处理脚本：先运行 `src/features/build_feature_dataset.py` 构建业务特征，再运行 `src/features/preprocess_feature_dataset.py` 完成编码、标准化和数据划分，生成 `modeling_dataset_train/validation/test.parquet` 等标准建模数据。

如果希望一次执行完整的字段批量处理流程，可以运行：

```bash
python src/pipeline.py --step feature_pipeline
```

### 10.3 单条预测需要完整建模特征

当前模型基于完整建模特征训练，预测时必须包含训练模型所需的全部字段。缺少字段会导致模型无法计算；如果输入中包含多余字段，预测接口会按训练时保存的特征列取数，多余字段不会参与模型预测。
