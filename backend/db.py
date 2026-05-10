"""
Database connection helper — mirrors the connection logic from the notebooks.
For Docker, returns mock data if database is unavailable.
"""

import pandas as pd
from datetime import datetime, timedelta
import os

SERVER = 'HEDIRE\\MSSQLSERVER05'
DATABASE = 'dw_pi'

# Check if we're in Docker (no database available)
IN_DOCKER = os.environ.get('FLASK_ENV') == 'production'


def get_connection():
    """Return a live pyodbc connection, trying ODBC Driver 17 first."""
    if IN_DOCKER:
        return None  # No database in Docker
    
    try:
        import pyodbc
        conn_str = (
            f'DRIVER={{ODBC Driver 17 for SQL Server}};'
            f'SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes'
        )
        return pyodbc.connect(conn_str, timeout=30)
    except Exception:
        try:
            import pyodbc
            conn_str = (
                f'DRIVER={{SQL Server}};'
                f'SERVER={SERVER};DATABASE={DATABASE};Trusted_Connection=yes'
            )
            return pyodbc.connect(conn_str, timeout=30)
        except:
            return None


def query_df(sql: str) -> pd.DataFrame:
    """Execute *sql* and return a DataFrame. Returns mock data if database unavailable."""
    conn = get_connection()
    
    if conn is None:
        # Return mock data for testing
        return _get_mock_data()
    
    try:
        return pd.read_sql(sql, conn)
    finally:
        conn.close()


def _get_mock_data() -> pd.DataFrame:
    """Return mock sales data for testing."""
    dates = pd.date_range(start='2023-01-01', periods=52, freq='W')
    quantities = [100 + i * 2 + (i % 5) * 10 for i in range(52)]
    return pd.DataFrame({
        'full_date': dates,
        'quantity': quantities
    })
