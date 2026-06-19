"""Project configuration for the hotel booking analysis pipeline."""

from pathlib import Path


# 项目根目录统一从 src/config.py 反推，避免在代码中写死本机绝对路径。
PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "hotel_bookings_updated_2024.csv"
PROCESSED_DATA_PATH = (
    PROJECT_ROOT / "data" / "processed" / "hotel_bookings_cleaned.csv"
)
CLEANED_PARQUET_PATH = (
    PROJECT_ROOT / "data" / "processed" / "hotel_bookings_cleaned.parquet"
)
MODELING_BASE_PARQUET_PATH = (
    PROJECT_ROOT / "data" / "processed" / "modeling_base.parquet"
)

CUSTOMER_PROFILE_TABLE_PATH = (
    PROJECT_ROOT / "data" / "intermediate" / "customer_profile_table.parquet"
)
HOTEL_SUMMARY_TABLE_PATH = (
    PROJECT_ROOT / "data" / "intermediate" / "hotel_summary_table.parquet"
)
TIME_DIMENSION_TABLE_PATH = (
    PROJECT_ROOT / "data" / "intermediate" / "time_dimension_table.parquet"
)
BOOKING_BEHAVIOR_TABLE_PATH = (
    PROJECT_ROOT / "data" / "intermediate" / "booking_behavior_by_arrival_date.parquet"
)

TARGET_COLUMN = "is_canceled"

# 字段列表以项目说明中的数据字典为准；实际数据多出的字段会在质量检查中记录。
EXPECTED_COLUMNS = [
    "hotel",
    "is_canceled",
    "lead_time",
    "arrival_date_year",
    "arrival_date_month",
    "arrival_date_week_number",
    "arrival_date_day_of_month",
    "stays_in_weekend_nights",
    "stays_in_week_nights",
    "adults",
    "children",
    "babies",
    "meal",
    "country",
    "market_segment",
    "distribution_channel",
    "is_repeated_guest",
    "previous_cancellations",
    "previous_bookings_not_canceled",
    "reserved_room_type",
    "assigned_room_type",
    "booking_changes",
    "deposit_type",
    "agent",
    "company",
    "days_in_waiting_list",
    "customer_type",
    "adr",
    "required_car_parking_spaces",
    "total_of_special_requests",
    "reservation_status",
    "reservation_status_date",
]
