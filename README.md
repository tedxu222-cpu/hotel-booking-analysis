# 酒店预订行为与取消预测

本项目围绕酒店预订订单数据，分析订单取消行为规律，并构建用于预测酒店预订是否取消的机器学习模型。项目当前已完成数据清洗、SQLite 数据库与 SQL 分析、特征工程、探索性数据分析、特征预处理、多模型建模、模型解释和业务落地模拟。

## 项目目标

- 对原始酒店预订数据进行质量检查、缺失值处理、异常值处理、去重和时间字段统一。
- 构建 SQLite 数据库，完成基础 SQL 统计分析和取消行为分析。
- 构建时间、预订行为、客户群体、价格、收益管理和风险相关特征。
- 按入住日期时间窗口划分训练集、验证集和测试集，完成编码、标准化和特征有效性评估。
- 构建逻辑回归、随机森林、XGBoost、LightGBM、MLP 和 Embedding MLP 模型，比较预测效果。
- 结合逻辑回归系数和 SHAP 值解释模型，识别影响预订取消的核心特征。
- 基于模型预测结果设计业务风险分层、干预阈值模拟、收益管理建议和 A/B 测试方案。
- 将建模、评估、融合、预测推理和业务模拟逻辑封装为可复用 Python 模块。

## 当前进度

### 第一阶段：项目启动与初步数据探索

已完成：

- Python 数据分析环境与项目目录搭建。
- Git 版本管理规范和分支管理策略说明。
- 原始数据读取、字段完整性检查、缺失值检查、重复值检查和目标变量确认。
- 数据清洗：缺失值填补、ADR 异常值处理、入住天数异常值处理、去重和时间格式统一。
- 清洗后数据保存。

### 第二阶段：数据库、特征工程与 EDA

已完成：

- SQLite 数据库搭建，包含预订主表、客户维度表、酒店维度表和时间维度表。
- SQL 查询脚本集，覆盖基础统计、取消率、渠道、市场细分、时间趋势、房型、餐饮、国家/地区、提前预订天数和回头客分析。
- 全维度特征体系构建。
- 特征预处理与有效性验证，包括按 `arrival_date` 时间窗口划分数据、Target Encoding、One-Hot Encoding、StandardScaler、方差阈值、相关性分析、互信息法和随机森林重要性预评估。
- 多维度 EDA 和第二阶段实验报告。

### 第三阶段：多模型建模与性能优化

已完成：

- 样本构建与数据集划分复核，沿用第二阶段按时间窗口划分的训练集、验证集和测试集。
- 样本不平衡处理方案对比，包括原始训练集、SMOTE 过采样、欠采样和类别权重调整。
- 逻辑回归、随机森林、XGBoost、LightGBM 四类传统机器学习模型构建与 Optuna 调优。
- MLP 和 Embedding MLP 深度学习模型构建，包含早停和学习率衰减策略。
- 模型融合方案构建，包含加权平均融合和多组 Stacking 融合方案，并对比不同融合策略的效果。
- 模型解释：逻辑回归系数、XGBoost/LightGBM SHAP 值、Top 10 核心特征。
- 预测错误样本分析，重点观察历史行为信息较少订单和特殊日期近似场景。
- 业务落地模拟：风险分层、A/B 测试方案、干预阈值收益测算、动态定价建议、渠道库存分配建议和取消政策优化建议。

### 第四阶段：代码工程化封装

已完成：

- 初步封装建模数据读取、样本统计、酒店类型样本拆分等工具函数。
- 初步封装二分类模型统一评估函数。
- 初步封装传统机器学习模型构建、Optuna 搜索空间、模型保存和模型加载工具。
- 初步封装加权平均融合、Stacking 融合和业务收益模拟工具。
- 开发批量预测与单条预测接口，输出取消概率、预测标签、风险等级和建议动作。
- 编写 Python 工具包使用说明和基础单元测试。

## 目录结构

```text
hotel-booking-analysis/
├── data/
│   ├── raw/                 # 原始数据，本地保存，不提交到 GitHub
│   ├── processed/           # 清洗后数据、特征数据和建模数据，本地生成
│   ├── intermediate/        # 中间聚合表
│   └── database/            # SQLite 数据库，本地生成
├── docs/                    # Git 规范、数据库设计和交付清单
├── notebooks/               # 数据清洗、特征工程、EDA、建模 Notebook
├── reports/                 # 阶段报告、分析结果、图表和模型解释结果
├── sql/                     # SQL 查询脚本
├── src/
│   ├── data/                # 数据质量检查、清洗和中间表脚本
│   ├── database/            # SQLite 建库和 SQL 分析脚本
│   ├── features/            # 特征工程、特征预处理和特征字典脚本
│   ├── models/              # 模型训练、评估、融合和预测推理模块
│   ├── business/            # 业务风险分层和收益模拟模块
│   └── pipeline.py          # 特征工程与特征预处理统一入口
├── tests/                   # 基础单元测试
├── requirements.txt
└── README.md
```

## 主要交付物

### 数据库与 SQL

- 数据库设计说明：`docs/sqlite_database_design.md`
- SQLite 建库脚本：`src/database/build_sqlite_database.py`
- SQL 分析脚本：`src/database/run_sql_analysis.py`
- SQL 查询脚本：`sql/basic_analysis.sql`
- SQL 查询结果：`reports/sql_analysis/`

### 特征工程与 EDA

- 特征工程 Notebook：`notebooks/feature_engineering.ipynb`
- 特征预处理 Notebook：`notebooks/feature_preprocessing_validation.ipynb`
- EDA Notebook：`notebooks/eda_analysis.ipynb`
- 特征工程脚本：`src/features/build_feature_dataset.py`
- 特征预处理脚本：`src/features/preprocess_feature_dataset.py`
- 详细特征字典脚本：`src/features/build_detailed_feature_dictionary.py`
- 特征字典：`reports/feature_dictionary.csv`
- 特征筛选报告：`reports/feature_selection_report.csv`
- EDA 图表：`reports/eda_figures/`

### 第三阶段建模

- 建模 Notebook：`notebooks/modeling_sample_construction.ipynb`
- 第三阶段实验报告：`reports/第三阶段实验报告.docx`
- 样本构建与划分结果：`reports/stage3_sample_split_summary.csv`、`reports/stage3_sampling_strategy_comparison.csv`、`reports/stage3_hotel_type_split_summary.csv`
- 传统模型结果：`reports/traditional_model_performance_comparison.csv`、`reports/traditional_model_tuning_comparison.csv`
- 深度学习结果：`reports/deep_learning_model_comparison.csv`
- 融合模型结果：`reports/ensemble_model_metrics.csv`、`reports/ensemble_model_comparison.csv`
- 模型解释结果：`reports/logistic_regression_coefficients.csv`、`reports/shap_feature_importance.csv`、`reports/core_feature_top10.csv`
- 错误样本分析：`reports/prediction_error_samples.csv`、`reports/prediction_error_scenario_summary.csv`
- 业务模拟结果：`reports/business_risk_scores.csv`、`reports/business_risk_segment_summary.csv`、`reports/business_threshold_simulation.csv`

### 第四阶段工程化封装

- Python 工具包使用说明：`docs/api_usage.md`
- 用户手册：`docs/user_manual.md`
- 项目总报告：`reports/项目总报告.docx`
- 统一流程入口：`src/pipeline.py`
- 建模数据工具：`src/models/dataset.py`
- 模型评估工具：`src/models/evaluation.py`
- 传统模型工具：`src/models/traditional.py`
- 模型融合工具：`src/models/ensemble.py`
- 预测推理接口：`src/models/predict.py`
- 业务模拟工具：`src/business/simulation.py`
- 基础单元测试：`tests/test_model_package.py`

## 运行方式

安装依赖：

```bash
pip install -r requirements.txt
```

构建 SQLite 数据库：

```bash
python src/database/build_sqlite_database.py
```

运行 SQL 分析并导出结果：

```bash
python src/database/run_sql_analysis.py
```

构建特征工程数据集：

```bash
python src/features/build_feature_dataset.py
```

运行特征预处理和有效性评估：

```bash
python src/features/preprocess_feature_dataset.py
```

也可以通过统一入口依次运行特征工程和特征预处理：

```bash
python src/pipeline.py --step feature_pipeline
```

生成详细特征字典：

```bash
python src/features/build_detailed_feature_dictionary.py
```

第三阶段建模、调优、融合、解释性分析和业务模拟主要在以下 Notebook 中完成：

```text
notebooks/modeling_sample_construction.ipynb
```

运行基础单元测试：

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## 数据与 Git 说明

原始数据、SQLite 数据库、清洗后数据和建模数据体积较大，且可以通过脚本在本地复现，因此不直接提交到 GitHub。当前 `.gitignore` 已忽略：

- `data/raw/*.csv`
- `data/raw/*.zip`
- `data/database/*.db`
- `data/processed/hotel_bookings_cleaned.csv`
- `data/processed/hotel_bookings_cleaned.parquet`
- `data/processed/hotel_booking_features.parquet`
- `data/processed/modeling_base.parquet`
- `data/processed/modeling_dataset*.parquet`
- `data/processed/stage3_*.parquet`
- `models/*.pkl`
- `models/*.joblib`
- `__pycache__/`
- Office 临时锁文件，如 `~$*.docx`

如需在本地复现完整结果，请先准备原始数据，再依次运行数据清洗、数据库构建、特征工程和特征预处理脚本。

## 注意事项

- 当前数据是订单级数据，没有真实 `user_id`。因此 RFM 分群和用户价值分析是基于客户类型、市场细分、分销渠道和是否回头客构造的客户群体近似，不代表真实单个用户画像。
- 节假日特征当前使用周末和相邻日期代理，没有接入外部法定节假日数据。
