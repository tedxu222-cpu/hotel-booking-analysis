# SQLite 数据库表结构设计说明

## 1. 设计目标

第二阶段基于第一阶段清洗后的酒店预订数据，搭建 SQLite 数据库并完成基础 SQL 分析。

数据库设计保留项目要求中的四类核心表：

- `bookings`：预订主表，保存订单层面的事实数据。
- `customer_profile`：客户维度表，保存客户类型、市场细分、分销渠道等客户群体属性。
- `hotel_summary`：酒店维度表，保存酒店名称、城市和酒店类型等酒店属性。
- `time_dimension`：时间维度表，保存入住日期对应的年、月、周、日、星期和周末标识。

此外，数据库中建立了 `booking_analysis_view` 分析视图，用于 SQL 统计分析时统一关联四张基础表，减少重复编写 JOIN 语句。

## 2. 表结构说明

### 2.1 `bookings` 预订主表

`bookings` 是事实表，每一行对应一条预订记录。该表通过技术主键和外键关联到酒店、客户和时间维度表。

主要字段包括：

- `booking_id`：预订记录技术主键，由导入脚本生成。
- `hotel_id`：酒店维度外键，关联 `hotel_summary`。
- `customer_id`：客户维度外键，关联 `customer_profile`。
- `date_id`：时间维度外键，关联 `time_dimension`。
- `is_canceled`：是否取消，是后续建模的目标变量。
- `lead_time`、`adr`、`total_stays`、`total_guests` 等订单行为和价格字段。

### 2.2 `customer_profile` 客户维度表

`customer_profile` 保存客户类型、市场细分、分销渠道和是否回头客等维度属性。当前原始数据没有真实 `user_id`，因此这里的 `customer_id` 是客户维度组合的技术编号，不代表真实单个用户。

主要字段包括：

- `customer_id`：客户维度技术主键。
- `customer_type`：客户类型。
- `market_segment`：市场细分。
- `distribution_channel`：分销渠道。
- `is_repeated_guest`：是否回头客。

### 2.3 `hotel_summary` 酒店维度表

`hotel_summary` 保存酒店相关维度属性。

主要字段包括：

- `hotel_id`：酒店维度技术主键。
- `hotel`：酒店名称或酒店类型字段。
- `city`：城市字段。
- `hotel_type`：根据酒店和城市字段推断得到的酒店类型标签。

### 2.4 `time_dimension` 时间维度表

`time_dimension` 保存入住日期的标准化时间信息。

主要字段包括：

- `date_id`：时间维度技术主键。
- `arrival_date`：标准化入住日期。
- `arrival_date_year`：入住年份。
- `arrival_date_month`：入住月份。
- `arrival_date_week_number`：入住周数。
- `arrival_date_day_of_month`：入住日。
- `day_of_week`：星期几。
- `is_weekend`：是否周末。

## 3. 技术主键说明

原始数据中没有明确的订单唯一标识、用户唯一标识和酒店唯一标识。为了在 SQLite 中建立清晰的表关系，导入脚本生成了以下技术主键：

- `booking_id`：按预订记录生成的订单编号。
- `hotel_id`：按酒店和城市组合生成的酒店编号。
- `customer_id`：按客户类型、市场细分、分销渠道和是否回头客组合生成的客户维度编号。
- `date_id`：按入住日期生成的时间编号。

这些编号用于数据库关联和查询优化，不是原始业务系统中的真实 ID。

## 4. 索引设计

为了优化常用 SQL 查询，数据库建立了单字段索引和复合索引。

单字段索引用于常见过滤条件：

- `bookings(hotel_id)`
- `bookings(customer_id)`
- `bookings(date_id)`
- `bookings(is_canceled)`
- `bookings(lead_time)`
- `bookings(deposit_type)`
- `time_dimension(arrival_date)`

复合索引用于常见组合分析场景：

- `bookings(date_id, hotel_id, is_canceled)`：支持按时间、酒店和取消状态分析。
- `bookings(customer_id, is_canceled)`：支持按客户维度分析取消率。
- `bookings(deposit_type, lead_time, is_canceled)`：支持订金类型、提前预订天数和取消行为分析。
- `customer_profile(customer_type, market_segment, distribution_channel)`：支持客户类型、市场细分和渠道联合查询。
- `hotel_summary(hotel_type, city)`：支持酒店类型和城市联合查询。

## 5. 分析视图

`booking_analysis_view` 将 `bookings`、`hotel_summary`、`customer_profile` 和 `time_dimension` 关联在一起，形成便于分析的宽表视图。

基础 SQL 分析优先基于该视图完成，避免在每个查询中重复书写多表关联逻辑。

## 6. 运行脚本与产出

建库脚本：

```bash
python src/database/build_sqlite_database.py
```

SQL 分析脚本：

```bash
python src/database/run_sql_analysis.py
```

主要产出：

- `data/database/hotel_booking.db`
- `reports/sql_analysis/*.csv`
- `docs/sqlite_database_design.md`
