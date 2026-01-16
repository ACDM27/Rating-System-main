import sqlite3
import os

db_path = "vote.db"
log_path = "result.log"

with open(log_path, "w", encoding="utf-8") as f:
    if not os.path.exists(db_path):
        f.write(f"Database file {db_path} not found.\n")
        exit(1)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        f.write("--- Database Table Counts ---\n")
        for table in tables:
            table_name = table[0]
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                f.write(f"{table_name}: {count}\n")
                
                # If it's the users table, let's breakdown by role
                if table_name == 'users':
                    f.write("  User Roles Breakdown:\n")
                    cursor.execute(f"SELECT role, COUNT(*) FROM users GROUP BY role")
                    roles = cursor.fetchall()
                    for role in roles:
                         f.write(f"    - {role[0]}: {role[1]}\n")
                         
            except Exception as e:
                f.write(f"{table_name}: Error ({e})\n")

        conn.close()

    except Exception as e:
        f.write(f"Error connecting to database: {e}\n")
