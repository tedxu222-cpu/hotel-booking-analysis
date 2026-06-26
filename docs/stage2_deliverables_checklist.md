# 第二阶段交付成果清单

## 1. SQLite 数据库文件

- 本地文件：`data/database/hotel_booking.db`
- 建库脚本：`src/database/build_sqlite_database.py`
- 数据库设计说明：`docs/sqlite_database_design.md`

说明：数据库包含 `bookings`、`customer_profile`、`hotel_summary`、`time_dimension` 四张基础表，以及 `booking_analysis_view` 分析视图；已建立日期、酒店、客户、订金类型、提前预订天数和取消状态相关索引。

## 2. SQL 查询脚本集

- SQL 脚本：`sql/basic_analysis.sql`
- 执行脚本：`src/database/run_sql_analysis.py`
- 查询结果：`reports/sql_analysis/*.csv`

覆盖内容包括基础统计、酒店取消率、市场细分、分销渠道、月度/季度趋势、房型与餐饮类型、国家/地区行为差异、提前预订天数、回头客行为和订金类型分析。

## 3. 完整特征字典

- 特征字典：`reports/feature_dictionary.csv`
- 生成脚本：`src/features/build_detailed_feature_dictionary.py`

字段说明包括特征定义、来源字段、计算逻辑、预处理方法、区分度评估和数据泄露/限制说明。

## 4. 特征工程脚本集与预处理后特征数据集

- 特征工程脚本：`src/features/build_feature_dataset.py`
- 特征预处理脚本：`src/features/preprocess_feature_dataset.py`
- 特征工程 Notebook：`notebooks/feature_engineering.ipynb`
- 特征预处理 Notebook：`notebooks/feature_preprocessing_validation.ipynb`
- 本地特征数据集：`data/processed/hotel_booking_features.parquet`
- 本地建模数据集：
  - `data/processed/modeling_dataset_train.parquet`
  - `data/processed/modeling_dataset_validation.parquet`
  - `data/processed/modeling_dataset_test.parquet`
  - `data/processed/modeling_dataset.parquet`

说明：上述 Parquet 数据集为可由脚本复现的本地生成文件，体积较大，已按项目数据管理原则加入 `.gitignore`，不直接提交 GitHub。

## 5. 特征有效性评估报告

- 特征筛选报告：`reports/feature_selection_report.csv`
- 特征重要性排序：`reports/feature_importance_preview.csv`
- 预处理摘要：`reports/feature_preprocessing_summary.csv`
- 相关性热力图：`reports/feature_correlation_heatmap.png`
- 特征重要性 Top 20 图：`reports/feature_importance_top20.png`

评估方法包括方差阈值法、目标变量相关性分析、互信息法和随机森林特征重要性预评估。

## 6. 探索性数据分析报告

- EDA Notebook：`notebooks/eda_analysis.ipynb`
- EDA 图表目录：`reports/eda_figures/`
- 第二阶段实验报告：`reports/第二阶段实验报告.docx`

当前 EDA 图表目录包含 17 张图，覆盖目标变量分布、酒店月度趋势、渠道、客户类型、提前预订天数、订金类型、市场细分、回头客、特殊需求、RFM 分群、价格、房型、淡旺季和周末代理分析。

## 7. 核心数据洞察总结

- 第二阶段实验报告：`reports/第二阶段实验报告.docx`

报告中已补充“核心数据洞察与业务优化建议”章节，覆盖用户行为规律、取消风险因素、用户分群局限、渠道/订金/提前预订相关优化建议和后续建模注意事项。
