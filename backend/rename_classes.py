import asyncio
from sqlalchemy import select, update
from app.database import async_session
from app.models.class_ import Class

async def rename_classes():
    async with async_session() as db:
        # 获取所有班级
        result = await db.execute(select(Class).order_by(Class.id))
        classes = result.scalars().all()
        
        if not classes:
            print("没有找到班级数据")
            return

        updates = {
            "22大数据一区": "初赛",
            "22大数据二区": "决赛"
        }
        
        count = 0
        for cls in classes:
            # 如果是旧名称，进行更新
            if cls.name in updates:
                new_name = updates[cls.name]
                print(f"正在重命名: {cls.name} -> {new_name}")
                cls.name = new_name
                count += 1
            # 如果已经是新名称，或者不匹配，可以选择按顺序强制重命名（可选）
            elif cls.name not in ["初赛", "决赛"] and count < 2:
                 # 如果名字既不是旧的也不是新的，按顺序赋予新名字
                 new_names = ["初赛", "决赛"]
                 if count < len(new_names):
                     new_name = new_names[count]
                     print(f"重命名未知班级: {cls.name} -> {new_name}")
                     cls.name = new_name
                     count += 1
        
        await db.commit()
        print("班级名称更新完成！")

if __name__ == "__main__":
    asyncio.run(rename_classes())
