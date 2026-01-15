import sqlite3
import os

# 使用绝对路径确保找到文件
db_path = r"d:\辩论赛投票系统\Rating-System-main\backend\vote.db"

def add_columns():
    print("Script started...")
    print(f"Target DB: {db_path}")
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查 pro_topic 是否存在
        cursor.execute("PRAGMA table_info(contests)")
        columns = [info[1] for info in cursor.fetchall()]
        
        with open("fix_result.txt", "w") as f:
            f.write(f"Current columns: {columns}\n")
        
            if 'pro_topic' not in columns:
                f.write("Adding pro_topic column...\n")
                cursor.execute("ALTER TABLE contests ADD COLUMN pro_topic TEXT")
            else:
                f.write("pro_topic already exists.\n")
                
            if 'con_topic' not in columns:
                f.write("Adding con_topic column...\n")
                cursor.execute("ALTER TABLE contests ADD COLUMN con_topic TEXT")
            else:
                f.write("con_topic already exists.\n")
            
            conn.commit()
            f.write("Database schema updated successfully.\n")
            
        conn.close()
    except Exception as e:
        with open("fix_result.txt", "w") as f:
            f.write(f"Error updating database: {e}\n")

if __name__ == "__main__":
    add_columns()
