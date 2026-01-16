"""
检查数据库中是否存在黄坤用户
"""
import asyncio
import sqlite3

def check_user_huangkun():
    """检查黄坤用户"""
    try:
        conn = sqlite3.connect('vote.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("检查用户：黄坤")
        print("=" * 60)
        
        # 查询包含"黄坤"的用户
        cursor.execute("""
            SELECT id, username, display_name, role, class_id 
            FROM users 
            WHERE username LIKE '%黄坤%' OR display_name LIKE '%黄坤%'
        """)
        users = cursor.fetchall()
        
        if users:
            print(f"\n找到 {len(users)} 个相关用户：")
            for user in users:
                print(f"  ID: {user[0]}, 用户名: {user[1]}, 显示名: {user[2]}, 角色: {user[3]}, 场次ID: {user[4]}")
        else:
            print("\n未找到'黄坤'相关的用户")
        
        # 查看所有用户
        cursor.execute("SELECT COUNT(*) FROM users")
        total = cursor.fetchone()[0]
        print(f"\n数据库中共有 {total} 个用户")
        
        cursor.execute("""
            SELECT role, COUNT(*) 
            FROM users 
            GROUP BY role
        """)
        role_stats = cursor.fetchall()
        print("\n用户角色分布：")
        for role, count in role_stats:
            print(f"  {role}: {count} 人")
        
        conn.close()
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_user_huangkun()
