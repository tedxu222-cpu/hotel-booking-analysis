"""执行 SQL 基础分析，并将每个查询结果导出为 CSV。"""

from __future__ import annotations

import re
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
    PROJECT_ROOT,
    SQL_ANALYSIS_REPORT_DIR,
    SQL_BASIC_ANALYSIS_PATH,
    SQLITE_DATABASE_PATH,
)


QUERY_PATTERN = re.compile(
    r"--\s*name:\s*(?P<name>[a-zA-Z0-9_]+)\s*\n(?P<sql>.*?)(?=\n--\s*name:|\Z)",
    re.DOTALL,
)


def format_relative_path(path: Path) -> str:
    """将项目内路径转换为相对路径，便于命令行输出。"""
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def load_named_queries(sql_path: Path = SQL_BASIC_ANALYSIS_PATH) -> dict[str, str]:
    """从 SQL 文件中读取使用 '-- name:' 标记的查询语句。"""
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL 文件不存在：{format_relative_path(sql_path)}")

    sql_text = sql_path.read_text(encoding="utf-8")
    queries = {}
    for match in QUERY_PATTERN.finditer(sql_text):
        name = match.group("name")
        sql = match.group("sql").strip().rstrip(";")
        if sql:
            queries[name] = sql

    if not queries:
        raise ValueError("SQL 文件中没有找到使用 '-- name:' 标记的查询。")
    return queries


def run_query(
    connection: sqlite3.Connection,
    query_name: str,
    sql: str,
    output_dir: Path = SQL_ANALYSIS_REPORT_DIR,
) -> Path:
    """执行单个 SQL 查询，并将结果保存为 CSV。"""
    df = pd.read_sql_query(sql, connection)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{query_name}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    return output_path


def run_sql_analysis() -> None:
    """执行全部 SQL 基础分析查询。"""
    if not SQLITE_DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"SQLite 数据库不存在：{format_relative_path(SQLITE_DATABASE_PATH)}"
        )

    queries = load_named_queries()
    with sqlite3.connect(SQLITE_DATABASE_PATH) as connection:
        outputs = []
        for query_name, sql in queries.items():
            output_path = run_query(connection, query_name, sql)
            outputs.append(output_path)

    print("SQL 基础分析已完成")
    print(f"数据库路径：{format_relative_path(SQLITE_DATABASE_PATH)}")
    print(f"SQL 文件：{format_relative_path(SQL_BASIC_ANALYSIS_PATH)}")
    print("已导出结果：")
    for output_path in outputs:
        print(f"- {format_relative_path(output_path)}")


if __name__ == "__main__":
    run_sql_analysis()
