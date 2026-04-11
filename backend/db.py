"""
Database connection helper — mirrors the connection logic from the notebooks.
"""

import pyodbc
import pandas as pd

SERVER = 'HEDIRE\\MSSQLSERVER05'
DATABASE = 'dw_pi'


def get_connection():
    """Return a live pyodbc connection, trying ODBC Driver 17 first."""
    try:
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes'
        )
        return pyodbc.connect(conn_str, timeout=30)
    except Exception:
        conn_str = (
            f'DRIVER={{SQL Server}};'
            f'SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes'
        )
        return pyodbc.connect(conn_str, timeout=30)


def query_df(sql: str) -> pd.DataFrame:
    """Execute *sql* and return a DataFrame. Closes the connection automatically."""
    conn = get_connection()
    try:
        return pd.read_sql(sql, conn)
    finally:
        conn.close()
