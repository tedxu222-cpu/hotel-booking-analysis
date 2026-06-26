-- name: booking_overview
-- 酒店预订总量、取消量、取消率和平均房价
SELECT
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(lead_time), 2) AS avg_lead_time,
    ROUND(AVG(total_stays), 2) AS avg_total_stays
FROM booking_analysis_view;

-- name: cancel_rate_by_hotel
-- 不同酒店的预订量、取消率和平均房价
SELECT
    hotel,
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY hotel
ORDER BY booking_count DESC;

-- name: market_segment_share
-- 各市场细分的预订占比、取消率和平均房价
SELECT
    market_segment,
    COUNT(*) AS booking_count,
    ROUND(
        COUNT(*) * 1.0 / (SELECT COUNT(*) FROM booking_analysis_view),
        4
    ) AS booking_share,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY market_segment
ORDER BY booking_count DESC;

-- name: distribution_channel_share
-- 各分销渠道的预订占比、取消率和平均房价
SELECT
    distribution_channel,
    COUNT(*) AS booking_count,
    ROUND(
        COUNT(*) * 1.0 / (SELECT COUNT(*) FROM booking_analysis_view),
        4
    ) AS booking_share,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY distribution_channel
ORDER BY booking_count DESC;

-- name: monthly_booking_trend
-- 月度预订趋势、取消率和平均房价
SELECT
    strftime('%Y-%m', arrival_date) AS arrival_month,
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(lead_time), 2) AS avg_lead_time
FROM booking_analysis_view
GROUP BY strftime('%Y-%m', arrival_date)
ORDER BY arrival_month;

-- name: quarterly_booking_trend
-- 季度预订趋势、取消率和平均房价
SELECT
    arrival_year AS year,
    ((CAST(strftime('%m', arrival_date) AS INTEGER) - 1) / 3 + 1) AS quarter,
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY
    arrival_year,
    ((CAST(strftime('%m', arrival_date) AS INTEGER) - 1) / 3 + 1)
ORDER BY year, quarter;

-- name: cancellation_rate_time_trend
-- 预订取消率的月度时间趋势分析
SELECT
    t.year,
    t.month,
    COUNT(b.booking_id) AS booking_count,
    SUM(b.is_canceled) AS cancellation_count,
    ROUND(AVG(b.is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(b.adr), 2) AS avg_adr,
    ROUND(AVG(b.lead_time), 2) AS avg_lead_time
FROM time_dimension AS t
JOIN bookings AS b
    ON t.date_id = b.date_id
GROUP BY
    t.year,
    t.month
ORDER BY
    t.year,
    t.month;

-- name: room_type_distribution
-- 不同预订房型的预订分布、取消率和平均房价
SELECT
    reserved_room_type,
    COUNT(*) AS booking_count,
    ROUND(
        COUNT(*) * 1.0 / (SELECT COUNT(*) FROM booking_analysis_view),
        4
    ) AS booking_share,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY reserved_room_type
ORDER BY booking_count DESC;

-- name: meal_distribution
-- 不同餐饮类型的预订分布、取消率和平均房价
SELECT
    meal,
    COUNT(*) AS booking_count,
    ROUND(
        COUNT(*) * 1.0 / (SELECT COUNT(*) FROM booking_analysis_view),
        4
    ) AS booking_share,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY meal
ORDER BY booking_count DESC;

-- name: country_booking_behavior_top20
-- 预订量最高的 20 个国家或地区的预订行为差异
SELECT
    country,
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(lead_time), 2) AS avg_lead_time
FROM booking_analysis_view
WHERE country IS NOT NULL
GROUP BY country
ORDER BY booking_count DESC
LIMIT 20;

-- name: lead_time_cancel_rate
-- 提前预订天数分组与取消率
SELECT
    CASE
        WHEN lead_time <= 7 THEN '0-7'
        WHEN lead_time <= 30 THEN '8-30'
        WHEN lead_time <= 90 THEN '31-90'
        WHEN lead_time <= 180 THEN '91-180'
        ELSE '181+'
    END AS lead_time_group,
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY
    CASE
        WHEN lead_time <= 7 THEN '0-7'
        WHEN lead_time <= 30 THEN '8-30'
        WHEN lead_time <= 90 THEN '31-90'
        WHEN lead_time <= 180 THEN '91-180'
        ELSE '181+'
    END
ORDER BY MIN(lead_time);

-- name: repeated_guest_behavior
-- 回头客与新客户的预订行为对比
SELECT
    CASE
        WHEN is_repeated_guest = 1 THEN 'repeated_guest'
        ELSE 'new_guest'
    END AS guest_type,
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr,
    ROUND(AVG(total_of_special_requests), 2) AS avg_special_requests
FROM booking_analysis_view
GROUP BY is_repeated_guest
ORDER BY is_repeated_guest DESC;

-- name: deposit_type_cancel_rate
-- 不同押金类型的预订量、取消率和平均房价
SELECT
    deposit_type,
    COUNT(*) AS booking_count,
    SUM(is_canceled) AS cancellation_count,
    ROUND(AVG(is_canceled), 4) AS cancellation_rate,
    ROUND(AVG(adr), 2) AS avg_adr
FROM booking_analysis_view
GROUP BY deposit_type
ORDER BY booking_count DESC;
