# 数据库场次隔离架构说明

## 核心概念澄清

### "场次" = "Class"

在本系统中，**`Class`（班级）实际上就是"场次"**的概念。

```
术语对应：
- Class (数据库表名) = 场次/赛事
- class_id (外键字段) = 场次ID
- Class.name (如"初赛"、"决赛") = 场次名称
```

## 正确的数据隔离架构

### 表结构对应关系

```
Workspace (工作空间)
  └─ Class (场次) ← id就是场次ID
      ├─ name: "初赛"/"决赛"/"半决赛" 等
      ├─ Contest (该场次的比赛配置)
      │   ├─ class_id → Class.id (场次ID)
      │   ├─ topic (辩题)
      │   ├─ pro_team_name / con_team_name
      │   └─ 关联数据：
      │       ├─ VoteRecord (投票记录)
      │       └─ JudgeScore (评分记录)
      ├─ User (该场次的参与者)
      │   ├─ class_id → Class.id (场次ID)
      │   ├─ 辩手 (role=student, 有team_side和debater_position)
      │   ├─ 观众 (role=audience)
      │   └─ 评委 (role=judge, 通过TeacherClass关联)
      └─ SystemSettings (该场次的系统状态)
          └─ class_id → Class.id (场次ID)
```

### 场次数据包含

每个场次(Class)包含：

1. **基础信息**
   - `id`: 场次ID
   - `name`: 场次名称（如"初赛"）
   - `workspace_id`: 所属工作空间

2. **比赛配置** (Contest)
   - 辩题
   - 正反方队名
   - 正反方立场

3. **参与者** (User where class_id = Class.id)
   - 辩手及其分配（位置、队伍）
   - 观众
   - 评委（通过TeacherClass关联表）

4. **比赛数据**
   - 投票记录 (VoteRecord)
   - 评委评分 (JudgeScore)

5. **系统状态** (SystemSettings)
   - 当前阶段
   - 投票/评分开关状态

## 数据隔离实现

### 通过 class_id 实现隔离

所有需要隔离的数据都包含 `class_id` 字段或通过 `contest_id` 间接关联到 `class_id`：

```sql
-- 直接通过 class_id 隔离
SELECT * FROM contests WHERE class_id = ?;
SELECT * FROM users WHERE class_id = ? AND team_side IS NOT NULL;
SELECT * FROM system_settings WHERE class_id = ?;

-- 通过 contest_id 间接隔离（contest.class_id）
SELECT * FROM vote_records WHERE contest_id IN (
    SELECT id FROM contests WHERE class_id = ?
);

SELECT * FROM judge_scores WHERE contest_id IN (
    SELECT id FROM contests WHERE class_id = ?
);
```

### 场次切换流程

1. 管理员在控制台选择"初赛"或"决赛"等场次
2. 前端更新 `currentClassId = Class.id`
3. 所有后续API请求携带该 `class_id`
4. 后端自动过滤返回该场次的数据

### 数据保留策略

- ✅ **创建新场次**: 创建新的Class记录，所有数据独立
- ✅ **切换场次**: 只改变前端的currentClassId，所有历史数据保留
- ✅ **删除场次**: 删除Class记录，级联删除所有相关数据

## 实际使用示例

### 示例1: 创建两个场次

```python
# 创建"初赛"场次
class_1 = Class(name="初赛", workspace_id=1)  # id=1

# 创建"决赛"场次  
class_2 = Class(name="决赛", workspace_id=1)  # id=2
```

### 示例2: 在"初赛"中创建比赛

```python
# 在初赛(class_id=1)创建比赛
contest_1 = Contest(
    class_id=1,  # 绑定到"初赛"
    topic="人工智能的发展利大于弊",
    pro_team_name="正方队",
    con_team_name="反方队"
)
```

### 示例3: 切换到"决赛"

```javascript
// 前端切换场次
authStore.switchClass(2, "决赛")  // class_id=2

// 所有API调用自动使用class_id=2
getCurrentContest(2)  // 只获取决赛的比赛
getTeams(2)  // 只获取决赛的辩手
```

## 总结

✅ **场次 = Class表**
- Class.id 就是场次ID
- Class.name 就是场次名称

✅ **数据隔离通过 class_id 实现**
- 所有场次相关数据都包含或关联到 class_id
- 切换场次就是切换 class_id

✅ **一个工作空间可以有多个场次**
- 每个场次的数据完全独立
- 可以同时进行，互不影响
- 历史数据永久保留
