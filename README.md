# 酒店预订行为与取消预测

本项目围绕酒店预订行为数据，分析订单取消规律，并构建用于后续取消预测建模的数据基础。当前项目已完成第一阶段的数据加载、质量检查和清洗，以及第二阶段的 SQLite 数据库搭建、SQL 分析、特征工程、特征预处理和多维度探索性数据分析。

## 项目目标

- 对酒店预订原始数据进行质量检查、缺失值处理、异常值处理、去重和时间字段统一。
- 搭建 SQLite 数据库，完成基础 SQL 统计分析和取消行为分析。
- 构建时间、预订行为、客户群体、价格、收益管理和风险相关特征。
- 完成训练集、验证集、测试集划分，以及类别编码、数值标准化和特征有效性评估。
- 通过 EDA 总结用户行为规律、取消风险因素和业务优化建议。

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
- 特征预处理与有效性验证，包括 Target Encoding、One-Hot Encoding、StandardScaler、方差阈值、相关性分析、互信息法和随机森林重要性预评估。
- 多维度 EDA 和第二阶段实验报告。

## 目录结构

```text
hotel-booking-analysis/
├── data/
│   ├── raw/                 # 原始数据，本地保存
│   ├── processed/           # 清洗后数据、特征数据和建模数据，本地生成
│   ├── intermediate/        # 中间聚合表
│   └── database/            # SQLite 数据库，本地生成
├── docs/                    # 项目说明、Git 规范、数据库设计和交付清单
├── notebooks/               # 数据清洗、特征工程、特征预处理和 EDA Notebook
├── reports/                 # 阶段报告、SQL 结果、特征评估结果和 EDA 图表
├── sql/                     # SQL 查询脚本
├── src/
│   ├── data/                # 数据质量检查、清洗和中间表脚本
│   ├── database/            # SQLite 建库和 SQL 分析脚本
│   └── features/            # 特征工程、特征预处理和详细特征字典脚本
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

### 特征工程与特征评估

- 特征工程 Notebook：`notebooks/feature_engineering.ipynb`
- 特征预处理 Notebook：`notebooks/feature_preprocessing_validation.ipynb`
- 特征工程脚本：`src/features/build_feature_dataset.py`
- 特征预处理脚本：`src/features/preprocess_feature_dataset.py`
- 详细特征字典脚本：`src/features/build_detailed_feature_dictionary.py`
- 特征字典：`reports/feature_dictionary.csv`
- 特征筛选报告：`reports/feature_selection_report.csv`
- 特征重要性报告：`reports/feature_importance_preview.csv`
- 相关性热力图：`reports/feature_correlation_heatmap.png`
- 特征重要性 Top 20 图：`reports/feature_importance_top20.png`

### EDA 与实验报告

- EDA Notebook：`notebooks/eda_analysis.ipynb`
- EDA 图表：`reports/eda_figures/`
- 第一阶段实验报告：`reports/阶段一实验报告.docx`
- 第二阶段实验报告：`reports/第二阶段实验报告.docx`
- 第二阶段交付清单：`docs/stage2_deliverables_checklist.md`

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

项目中的原始数据、SQLite 数据库和部分 Parquet 建模数据体积较大，其中数据库和建模数据集可以由脚本复现，因此不直接提交到 GitHub。

当前 `.gitignore` 已忽略：

- `data/database/*.db`
- `data/processed/hotel_booking_features.parquet`
- `data/processed/modeling_dataset*.parquet`
- Office 临时锁文件，如 `~$*.docx`

如果需要在本地复现完整结果，请先准备原始数据，再依次运行数据清洗、数据库构建、特征工程和特征预处理脚本。

## 重要说明

- 当前数据是订单级数据，没有真实 `user_id`。因此 RFM 分群和用户价值分析是基于客户类型、市场细分、分销渠道和是否回头客构造的客户群体近似，不代表真实单个用户画像。
- 节假日特征当前使用周末作为代理，没有接入外部法定节假日数据。
- 历史取消率、Target Encoding 和取消风险评分均与目标变量有关，后续正式建模时必须继续使用训练集内拟合或严格时间顺序计算，避免数据泄露。
- 第二阶段中的随机森林仅用于特征重要性预评估，不代表最终模型。
