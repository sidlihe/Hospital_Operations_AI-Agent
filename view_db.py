import sqlite3

conn = sqlite3.connect("data/hospital.db")
cursor = conn.cursor()

cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table';"
)

tables = cursor.fetchall()

for table in tables:
    table_name = table[0]

    print(f"\n{'='*50}")
    print(f"TABLE: {table_name}")
    print(f"{'='*50}")

    cursor.execute(f"SELECT * FROM {table_name}")

    rows = cursor.fetchall()

    for row in rows:
        print(row)

conn.close()