import pyodbc

conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=HEDIRE\\MSSQLSERVER05;'
    'DATABASE=dw_pi;'
    'Trusted_Connection=yes'
)

cursor = conn.cursor()
cursor.execute("SELECT TOP 1 * FROM dim_date")
columns = [col[0] for col in cursor.description]
print("dim_date columns:", columns)

cursor.execute("SELECT TOP 1 * FROM fact_sale")
columns = [col[0] for col in cursor.description]
print("fact_sale columns:", columns)

conn.close()
