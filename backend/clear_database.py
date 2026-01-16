"""
清空数据库脚本 - 保留管理员账号和工作空间

警告：此脚本会删除所有数据！
保留：
- 管理员账号（role=admin）
- 工作空间（workspaces）

删除：
- 所有场次（classes）
- 所有观众账号（role=audience）
- 所有评委账号（role=judge）
- 所有辩手数据
- 所有比赛记录（contests）
- 所有投票记录（vote_records）
- 所有评分记录（judge_scores）
- 所有系统设置（system_settings）
"""

import asyncio
import sqlite3
from datetime import datetime

def clear_database():
    """清空数据库，仅保留管理员账号"""
    try:
        conn = sqlite3.connect('vote.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("数据库清空操作")
        print("=" * 60)
        print("警告：此操作将删除所有数据（管理员账号除外）")
        print("=" * 60)
        
        # 备份当前数据统计
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM classes")
        class_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contests")
        contest_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM vote_records")
        vote_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM judge_scores")
        score_count = cursor.fetchone()[0]
        
        print(f"\n当前数据统计:")
        print(f"  用户总数: {total_users}")
        print(f"  管理员数: {admin_count}")
        print(f"  场次数: {class_count}")
        print(f"  比赛数: {contest_count}")
        print(f"  投票记录: {vote_count}")
        print(f"  评分记录: {score_count}")
        
        # 确认操作
        print(f"\n将要删除:")
        print(f"  - {total_users - admin_count} 个非管理员用户")
        print(f"  - {class_count} 个场次")
        print(f"  - {contest_count} 个比赛")
        print(f"  - {vote_count} 条投票记录")
        print(f"  - {score_count} 条评分记录")
        print(f"\n保留:")
        print(f"  - {admin_count} 个管理员账号")
        print(f"  - 工作空间数据")
        
        confirm = input("\n确认执行清空操作？(输入 YES 确认): ")
        if confirm != "YES":
            print("操作已取消")
            conn.close()
            return
        
        print("\n开始清空数据...")
        
        # 1. 删除系统设置
        cursor.execute("DELETE FROM system_settings")
        print("✓ 已删除所有系统设置")
        
        # 2. 删除评分记录
        cursor.execute("DELETE FROM judge_scores")
        print("✓ 已删除所有评分记录")
        
        # 3. 删除投票记录
        cursor.execute("DELETE FROM vote_records")
        print("✓ 已删除所有投票记录")
        
        # 4. 删除比赛
        cursor.execute("DELETE FROM contests")
        print("✓ 已删除所有比赛")
        
        # 5. 删除评委-场次关联
        cursor.execute("DELETE FROM teacher_classes")
        print("✓ 已删除所有评委-场次关联")
        
        # 6. 删除场次
        cursor.execute("DELETE FROM classes")
        print("✓ 已删除所有场次")
        
        # 7. 删除非管理员用户
        cursor.execute("DELETE FROM users WHERE role != 'admin'")
        affected = cursor.rowcount
        print(f"✓ 已删除 {affected} 个非管理员用户")
        
        # 提交更改
        conn.commit()
        
        print("\n" + "=" * 60)
        print("数据库清空完成！")
        print("=" * 60)
        
        # 显示剩余数据
        cursor.execute("SELECT id, username, display_name, role FROM users WHERE role = 'admin'")
        admins = cursor.fetchall()
        
        print(f"\n保留的管理员账号:")
        for admin in admins:
            print(f"  ID: {admin[0]}, 用户名: {admin[1]}, 显示名: {admin[2]}")
        
        cursor.execute("SELECT COUNT(*) FROM workspaces")
        workspace_count = cursor.fetchone()[0]
        print(f"\n保留的工作空间数: {workspace_count}")
        
        conn.close()
        
        print("\n清空操作成功完成！")
        print("提示：重启后端服务以使更改生效")
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    clear_database()
