import os
import psycopg

conn = psycopg.connect(
    dbname=os.getenv("PGDATABASE", "testdb"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.environ["PGPASSWORD"],
    host=os.getenv("PGHOST", "localhost"),
    port=int(os.getenv("PGPORT", "5432"))
)

print("Connected successfully!")
conn.close()