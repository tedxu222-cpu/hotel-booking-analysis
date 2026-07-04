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
- Stacking 融合模型构建，融合 XGBoost、LightGBM 与 MLP 的预测结果。
- 模型解释：逻辑回归系数、XGBoost/LightGBM SHAP 值、Top 10 核心特征。
- 预测错误样本分析，重点观察历史行为信息较少订单和特殊日期近似场景。
- 业务落地模拟：风险分层、A/B 测试方案、干预阈值收益测算、动态定价建议、渠道库存分配建议和取消政策优化建议。

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
│   └── features/            # 特征工程、特征预处理和特征字典脚本
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
- 传统模型结果：`reports/traditional_model_performance_comparison.csv`
- 深度学习结果：`reports/deep_learning_model_comparison.csv`
- 融合模型结果：`reports/ensemble_model_metrics.csv`
- 模型解释结果：`reports/logistic_regression_coefficients.csv`、`reports/shap_feature_importance.csv`、`reports/core_feature_top10.csv`
- 错误样本分析：`reports/prediction_error_samples.csv`、`reports/prediction_error_scenario_summary.csv`
- 业务模拟结果：`reports/business_threshold_simulation.csv`、`reports/business_expected_benefit_summary.csv`、`reports/business_revenue_management_recommendations.csv`

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

生成详细特征字典：

```bash
python src/features/build_detailed_feature_dictionary.py
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
- `__pycache__/`
- Office 临时锁文件，如 `~$*.docx`

如需在本地复现完整结果，请先准备原始数据，再依次运行数据清洗、数据库构建、特征工程和特征预处理脚本。

## 注意事项

- 当前数据是订单级数据，没有真实 `user_id`。因此 RFM 分群和用户价值分析是基于客户类型、市场细分、分销渠道和是否回头客构造的客户群体近似，不代表真实单个用户画像。
- 节假日特征当前使用周末和相邻日期代理，没有接入外部法定节假日数据。
