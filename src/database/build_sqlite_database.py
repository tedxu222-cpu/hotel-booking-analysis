"""创建 SQLite 数据库，并导入符合第三范式思路的基础表。"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# 允许从 src/database 目录直接运行脚本，同时仍能导入 src/config.py。
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from config import (  # noqa: E402
    CLEANED_PARQUET_PATH,
    PROJECT_ROOT,
    SQLITE_DATABASE_PATH,
)


HOTEL_DIM_COLUMNS = ["hotel", "city"]
CUSTOMER_DIM_COLUMNS = [
    "customer_type",
    "market_segment",
    "distribution_channel",
    "is_repeated_guest",
]
TIME_DIM_COLUMNS = [
    "arrival_date",
    "arrival_date_year",
    "arrival_date_week_number",
    "arrival_date_day_of_month",
]

DROP_FROM_BOOKINGS = [
    "hotel",
    "city",
    "arrival_date",
    "arrival_date_year",
    "arrival_date_month",
    "arrival_date_week_number",
    "arrival_date_day_of_month",
    "customer_type",
    "market_segment",
    "distribution_channel",
    "is_repeated_guest",
]

INDEX_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_bookings_hotel_id ON bookings(hotel_id)",
    "CREATE INDEX IF NOT EXISTS idx_bookings_customer_id ON bookings(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_bookings_date_id ON bookings(date_id)",
    "CREATE INDEX IF NOT EXISTS idx_bookings_is_canceled ON bookings(is_canceled)",
    "CREATE INDEX IF NOT EXISTS idx_bookings_lead_time ON bookings(lead_time)",
    "CREATE INDEX IF NOT EXISTS idx_bookings_deposit_type ON bookings(deposit_type)",
    "CREATE INDEX IF NOT EXISTS idx_hotel_summary_hotel ON hotel_summary(hotel)",
    (
        "CREATE INDEX IF NOT EXISTS idx_time_dimension_date "
        "ON time_dimension(arrival_date)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_customer_profile_type_channel "
        "ON customer_profile(customer_type, market_segment, distribution_channel)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_customer_profile_segment_channel "
        "ON customer_profile(market_segment, distribution_channel)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_hotel_summary_type_city "
        "ON hotel_summary(hotel_type, city)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_time_dimension_year_month "
        "ON time_dimension(year, month)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_bookings_hotel_cancel "
        "ON bookings(hotel_id, is_canceled)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_bookings_date_cancel "
        "ON bookings(date_id, is_canceled)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_bookings_customer_cancel "
        "ON bookings(customer_id, is_canceled)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_bookings_deposit_lead_cancel "
        "ON bookings(deposit_type, lead_time, is_canceled)"
    ),
]

# 显式建表而不是直接使用 pandas.to_sql(replace)，是为了保留主键、唯一约束和外键关系。
SCHEMA_SQL = [
    "DROP VIEW IF EXISTS booking_analysis_view",
    "DROP TABLE IF EXISTS bookings",
    "DROP TABLE IF EXISTS customer_profile",
    "DROP TABLE IF EXISTS hotel_summary",
    "DROP TABLE IF EXISTS time_dimension",
    """
    CREATE TABLE hotel_summary (
        hotel_id INTEGER PRIMARY KEY,
        hotel TEXT NOT NULL,
        city TEXT,
        hotel_type TEXT,
        UNIQUE (hotel, city)
    )
    """,
    """
    CREATE TABLE customer_profile (
        customer_id INTEGER PRIMARY KEY,
        customer_type TEXT NOT NULL,
        market_segment TEXT NOT NULL,
        distribution_channel TEXT NOT NULL,
        is_repeated_guest INTEGER NOT NULL,
        UNIQUE (
            customer_type,
            market_segment,
            distribution_channel,
            is_repeated_guest
        )
    )
    """,
    """
    CREATE TABLE time_dimension (
        date_id INTEGER PRIMARY KEY,
        arrival_date TIMESTAMP NOT NULL UNIQUE,
        year INTEGER NOT NULL,
        month INTEGER NOT NULL,
        week INTEGER NOT NULL,
        day INTEGER NOT NULL,
        day_of_week INTEGER NOT NULL,
        is_weekend INTEGER NOT NULL
    )
    """,
    """
    CREATE TABLE bookings (
        booking_id INTEGER PRIMARY KEY,
        hotel_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        date_id INTEGER NOT NULL,
        is_canceled INTEGER NOT NULL,
        lead_time INTEGER,
        stays_in_weekend_nights INTEGER,
        stays_in_week_nights INTEGER,
        adults INTEGER,
        children REAL,
        babies INTEGER,
        meal TEXT,
        country TEXT,
        previous_cancellations INTEGER,
        previous_bookings_not_canceled INTEGER,
        reserved_room_type TEXT,
        assigned_room_type TEXT,
        booking_changes INTEGER,
        deposit_type TEXT,
        agent REAL,
        company REAL,
        days_in_waiting_list INTEGER,
        adr REAL,
        required_car_parking_spaces INTEGER,
        total_of_special_requests INTEGER,
        reservation_status TEXT,
        reservation_status_date TIMESTAMP,
        total_stays INTEGER,
        FOREIGN KEY (hotel_id) REFERENCES hotel_summary(hotel_id),
        FOREIGN KEY (customer_id) REFERENCES customer_profile(customer_id),
        FOREIGN KEY (date_id) REFERENCES time_dimension(date_id)
    )
    """,
]

# 基础表保持第三范式结构；分析视图只负责临时 JOIN 维度字段，便于 SQL 统计复用。
ANALYSIS_VIEW_SQL = """
CREATE VIEW IF NOT EXISTS booking_analysis_view AS
SELECT
    b.booking_id,
    h.hotel,
    h.city,
    h.hotel_type,
    t.arrival_date,
    t.year AS arrival_year,
    t.month AS arrival_month_number,
    t.week AS arrival_week_number,
    t.day AS arrival_day_of_month,
    t.day_of_week,
    t.is_weekend,
    c.customer_type,
    c.market_segment,
    c.distribution_channel,
    c.is_repeated_guest,
    b.is_canceled,
    b.lead_time,
    b.stays_in_weekend_nights,
    b.stays_in_week_nights,
    b.adults,
    b.children,
    b.babies,
    b.meal,
    b.country,
    b.previous_cancellations,
    b.previous_bookings_not_canceled,
    b.reserved_room_type,
    b.assigned_room_type,
    b.booking_changes,
    b.deposit_type,
    b.agent,
    b.company,
    b.days_in_waiting_list,
    b.adr,
    b.required_car_parking_spaces,
    b.total_of_special_requests,
    b.reservation_status,
    b.reservation_status_date,
    b.total_stays
FROM bookings AS b
JOIN hotel_summary AS h
    ON b.hotel_id = h.hotel_id
JOIN time_dimension AS t
    ON b.date_id = t.date_id
JOIN customer_profile AS c
    ON b.customer_id = c.customer_id
"""


def format_relative_path(path: Path) -> str:
    """将项目内路径转换为相对路径，便于命令行输出。"""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def read_cleaned_data(path: Path = CLEANED_PARQUET_PATH) -> pd.DataFrame:
    """读取第一阶段清洗后的 Parquet 数据。"""
    if not path.exists():
        raise FileNotFoundError(f"数据文件不存在：{format_relative_path(path)}")
    return pd.read_parquet(path)


def infer_hotel_type(hotel_name: str) -> str:
    """从酒店名称中提取酒店类型。"""
    if str(hotel_name).startswith("City Hotel"):
        return "City Hotel"
    if str(hotel_name).startswith("Resort Hotel"):
        return "Resort Hotel"
    return "Unknown"


def build_hotel_summary(df: pd.DataFrame) -> pd.DataFrame:
    """构建酒店维度表，每个酒店和城市组合只保留一行。"""
    hotel_summary = df[HOTEL_DIM_COLUMNS].drop_duplicates().reset_index(drop=True)
    # 原始数据没有 hotel_id，因此按去重后的酒店维度行生成技术主键。
    hotel_summary.insert(0, "hotel_id", range(1, len(hotel_summary) + 1))
    hotel_summary["hotel_type"] = hotel_summary["hotel"].map(infer_hotel_type)
    return hotel_summary


def build_customer_profile(df: pd.DataFrame) -> pd.DataFrame:
    """构建客户维度表，存储不同客户类型和渠道组合。"""
    customer_profile = (
        df[CUSTOMER_DIM_COLUMNS].drop_duplicates().reset_index(drop=True)
    )
    # customer_id 表示客户类型和渠道组合，不代表单个真实客户。
    customer_profile.insert(0, "customer_id", range(1, len(customer_profile) + 1))
    return customer_profile


def build_time_dimension(df: pd.DataFrame) -> pd.DataFrame:
    """构建时间维度表，每个入住日期只保留一行。"""
    time_dimension = df[TIME_DIM_COLUMNS].drop_duplicates().reset_index(drop=True)
    time_dimension["arrival_date"] = pd.to_datetime(time_dimension["arrival_date"])
    time_dimension = time_dimension.sort_values("arrival_date").reset_index(drop=True)
    # date_id 用于把订单表和时间维度表关联起来。
    time_dimension.insert(0, "date_id", range(1, len(time_dimension) + 1))
    time_dimension["year"] = time_dimension["arrival_date"].dt.year
    time_dimension["month"] = time_dimension["arrival_date"].dt.month
    time_dimension["week"] = (
        time_dimension["arrival_date"].dt.isocalendar().week.astype(int)
    )
    time_dimension["day"] = time_dimension["arrival_date"].dt.day
    time_dimension["day_of_week"] = time_dimension["arrival_date"].dt.dayofweek
    time_dimension["is_weekend"] = time_dimension["day_of_week"].isin([5, 6]).astype(
        int
    )
    return time_dimension[
        [
            "date_id",
            "arrival_date",
            "year",
            "month",
            "week",
            "day",
            "day_of_week",
            "is_weekend",
        ]
    ]


def build_bookings(
    df: pd.DataFrame,
    hotel_summary: pd.DataFrame,
    customer_profile: pd.DataFrame,
    time_dimension: pd.DataFrame,
) -> pd.DataFrame:
    """构建预订主表，只保留维度外键和订单事实字段。"""
    bookings = df.reset_index(drop=True).copy()
    # 原始数据没有预订唯一标识，因此按清洗后行顺序生成技术主键。
    bookings.insert(0, "booking_id", range(1, len(bookings) + 1))

    # validate="many_to_one" 用于保证每条订单只匹配到一条维度记录。
    bookings = bookings.merge(
        hotel_summary[["hotel_id", *HOTEL_DIM_COLUMNS]],
        on=HOTEL_DIM_COLUMNS,
        how="left",
        validate="many_to_one",
    )
    bookings = bookings.merge(
        customer_profile[["customer_id", *CUSTOMER_DIM_COLUMNS]],
        on=CUSTOMER_DIM_COLUMNS,
        how="left",
        validate="many_to_one",
    )
    bookings = bookings.merge(
        time_dimension[["date_id", "arrival_date"]],
        on="arrival_date",
        how="left",
        validate="many_to_one",
    )

    if bookings[["hotel_id", "customer_id", "date_id"]].isna().any().any():
        raise ValueError("维度表关联失败，存在无法匹配的外键。")

    bookings = bookings.drop(columns=DROP_FROM_BOOKINGS)
    id_columns = ["booking_id", "hotel_id", "customer_id", "date_id"]
    other_columns = [col for col in bookings.columns if col not in id_columns]
    return bookings[id_columns + other_columns]


def write_table(
    connection: sqlite3.Connection,
    table_name: str,
    df: pd.DataFrame,
) -> tuple[int, int]:
    """将 DataFrame 写入 SQLite 表。"""
    df.to_sql(table_name, connection, if_exists="append", index=False)
    return df.shape


def create_schema(connection: sqlite3.Connection) -> None:
    """创建带主键和外键约束的 SQLite 表结构。"""
    # 重建表结构时先关闭外键检查，避免 DROP 旧表时受依赖顺序影响。
    connection.execute("PRAGMA foreign_keys = OFF")
    for sql in SCHEMA_SQL:
        connection.execute(sql)
    connection.execute("PRAGMA foreign_keys = ON")


def create_indexes(connection: sqlite3.Connection) -> None:
    """为常用查询字段创建单字段索引和复合索引。"""
    for sql in INDEX_SQL:
        connection.execute(sql)


def create_analysis_view(connection: sqlite3.Connection) -> None:
    """创建便于 SQL 分析使用的关联视图。"""
    connection.execute("DROP VIEW IF EXISTS booking_analysis_view")
    connection.execute(ANALYSIS_VIEW_SQL)


def build_sqlite_database() -> None:
    """创建 SQLite 数据库并导入第三范式结构表。"""
    SQLITE_DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw_df = read_cleaned_data()
    hotel_summary = build_hotel_summary(raw_df)
    customer_profile = build_customer_profile(raw_df)
    time_dimension = build_time_dimension(raw_df)
    bookings = build_bookings(
        raw_df,
        hotel_summary,
        customer_profile,
        time_dimension,
    )

    with sqlite3.connect(SQLITE_DATABASE_PATH) as connection:
        create_schema(connection)
        table_shapes = {
            "customer_profile": write_table(
                connection,
                "customer_profile",
                customer_profile,
            ),
            "hotel_summary": write_table(connection, "hotel_summary", hotel_summary),
            "time_dimension": write_table(
                connection,
                "time_dimension",
                time_dimension,
            ),
            "bookings": write_table(connection, "bookings", bookings),
        }
        create_indexes(connection)
        create_analysis_view(connection)
        connection.commit()

    print("SQLite 数据库已创建")
    print(f"数据库路径：{format_relative_path(SQLITE_DATABASE_PATH)}")
    print("已导入表：")
    for table_name, shape in table_shapes.items():
        print(f"- {table_name}: {shape[0]} 行，{shape[1]} 列")
    print("已创建分析视图：booking_analysis_view")


if __name__ == "__main__":
    build_sqlite_database()
