# 数据预处理与中间表说明

本阶段基于清洗后的数据文件 `data/processed/hotel_bookings_cleaned.csv` 继续进行数据工程处理。

## 1. 数据类型压缩

脚本会对数值字段进行类型压缩：

- 整数字段使用 `downcast="integer"` 压缩。
- 浮点字段使用 `downcast="float"` 压缩。
- 低基数文本字段转换为 `category` 类型。
- `reservation_status_date` 和 `arrival_date` 转换为 datetime。

## 2. 非必要字段筛选

完整清洗数据会保存为：

```text
data/processed/hotel_bookings_cleaned.parquet
```

建模基础数据会保存为：

```text
data/processed/modeling_base.parquet
```

其中 `reservation_status` 和 `reservation_status_date` 属于订单结果相关字段，后续建模时可能造成数据泄漏，因此在建模基础表中先移除。

## 3. 中间表

### 用户维度表

输出路径：

```text
data/intermediate/customer_profile_table.parquet
```

当前数据没有明确 `user_id`，因此该表不是严格意义上的单用户画像表，而是基于 `customer_type`、`is_repeated_guest`、`market_segment`、`distribution_channel` 聚合的客户群体画像表。

### 酒店维度表

输出路径：

```text
data/intermediate/hotel_summary_table.parquet
```

按 `hotel` 和 `city` 聚合，统计预订量、取消率、平均房价、平均提前预订天数和平均入住晚数。

### 时间维度表

输出路径：

```text
data/intermediate/time_dimension_table.parquet
```

基于 `arrival_date` 构建年、月、周、日、星期和是否周末字段。当前未引入外部节假日数据，因此不构造节假日字段。

### 预订行为表

输出路径：

```text
data/intermediate/booking_behavior_by_arrival_date.parquet
```

按 `arrival_date` 聚合，统计每日预订数、取消数、取消率、平均房价、平均提前预订天数和平均入住晚数。

## 4. 运行方式

```bash
python src/data/build_intermediate_tables.py
```
