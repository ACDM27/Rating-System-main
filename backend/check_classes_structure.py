"""
检查数据库表结构
"""
import asyncio
import sqlite3

def check_classes_table():
    """检查classes表的完整结构"""
    try:
        conn = sqlite3.connect('vote.db')
        cursor = conn.cursor()
        
        # 获取表结构
        cursor.execute("PRAGMA table_info(classes)")
        columns = cursor.fetchall()
        
        print("=" * 60)
        print("Classes表结构:")
        print("=" * 60)
        for col in columns:
            print(f"列 {col[1]}: {col[2]} (nullable={not col[3]})")
        
        print("\n" + "=" * 60)
        print("Classes表数据:")
        print("=" * 60)
        cursor.execute("SELECT * FROM classes")
        classes = cursor.fetchall()
        
        column_names = [col[1] for col in columns]
        print(f"列名: {column_names}")
        
        for cls in classes:
            print(f"数据: {cls}")
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_classes_table()
