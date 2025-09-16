from pathlib import Path
from typing import List, Tuple
import duckdb
import os
import re

DEFAULT_DB_PATH = os.getenv("DUCKDB_PATH", "./db/nl2sql.duckdb")


def get_connection(db_path: str | None = None) -> duckdb.DuckDBPyConnection:
    path = db_path or DEFAULT_DB_PATH
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(path)


def setup_sample_data(csv_path: str = "./data/orders.csv", table_name: str = "orders", db_path: str | None = None) -> int:
    con = get_connection(db_path)
    # Use DuckDB's read_csv_auto to infer schema and create/replace the table
    con.execute(
        f"""
        CREATE OR REPLACE TABLE {table_name} AS
        SELECT * FROM read_csv_auto('{csv_path}', header=True);
        """
    )
    rows = con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    return int(rows)


def list_tables_and_columns(db_path: str | None = None) -> List[Tuple[str, str]]:
    con = get_connection(db_path)
    rows = con.execute(
        """
        SELECT table_name, string_agg(column_name, ', ' ORDER BY ordinal_position) AS columns
        FROM information_schema.columns
        WHERE table_schema = 'main'
        GROUP BY table_name
        ORDER BY table_name
        """
    ).fetchall()
    return [(r[0], r[1]) for r in rows]


def schema_ddl(db_path: str | None = None) -> str:
    con = get_connection(db_path)
    ddl_rows = con.execute(
        """
        SELECT 'CREATE TABLE ' || table_name || ' AS -- columns: ' ||
               string_agg(column_name || ' ' || data_type, ', ' ORDER BY ordinal_position)
        FROM information_schema.columns
        WHERE table_schema = 'main'
        GROUP BY table_name
        ORDER BY table_name
        """
    ).fetchall()
    return "\n".join(r[0] for r in ddl_rows)


BLOCKED_KEYWORDS = [
    ";",  # block multiple statements
    " INSERT ", " UPDATE ", " DELETE ", " DROP ", " CREATE ", " ALTER ", " COPY ",
    " PRAGMA ", " ATTACH ", " DETACH ", " SYSTEM ", " LOAD ", " REPLACE ", " MERGE ",
]


def is_safe_select(sql: str) -> bool:
    s = " " + sql.strip().upper() + " "
    if not (s.lstrip().startswith("WITH ") or s.lstrip().startswith("SELECT ")):
        return False
    return not any(kw in s for kw in BLOCKED_KEYWORDS)


def ensure_limit(sql: str, default_limit: int = 50) -> str:
    # If the query already contains a LIMIT anywhere (simple heuristic), don't add another
    # Handles cases like '... LIMIT 5', '...\nLIMIT 5', with or without trailing semicolon
    if re.search(r"(?i)\blimit\b", sql):
        return sql
    # Add a LIMIT at the end, mindful of trailing semicolons
    sql_no_sc = sql.rstrip().removesuffix(";")
    return f"{sql_no_sc} LIMIT {default_limit}"


def run_select(sql: str, db_path: str | None = None):
    if not is_safe_select(sql):
        raise ValueError("Consulta SQL insegura ou não-SELECT bloqueada.")
    sql = ensure_limit(sql)
    con = get_connection(db_path)
    return con.execute(sql).fetch_df()
