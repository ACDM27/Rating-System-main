# 数据库场次隔离完整方案

## 当前状态 ✅

数据库已经具备完整的场次隔离架构，所有关键数据都通过 `class_id` 或 `contest_id` 实现隔离。

## 数据模型结构

### 隔离层次结构

```
Workspace (工作空间)
  ├─ Admin (管理员)
  └─ Class (场次/班级) ← 【主隔离层】
      ├─ Contest (比赛配置)
      │   ├─ topic (辩题)
      │   ├─ pro_team_name / con_team_name (正反方队名)
      │   ├─ pro_topic / con_topic (正反方立场)
      │   ├─ VoteRecord (投票记录) ← 通过contest_id隔离
      │   └─ JudgeScore (评委评分) ← 通过contest_id隔离
      ├─ User (用户)
      │   ├─ debater_position (辩手位置)
      │   └─ team_side (队伍方向)
      └─ SystemSettings (系统设置)
```

### 关键表的隔离字段

| 表名 | 隔离字段 | 说明 |
|------|----------|------|
| `contests` | `class_id` | 直接关联场次 |
| `users` | `class_id` | 辩手、观众、评委都绑定场次 |
| `vote_records` | `contest_id → class_id` | 通过比赛间接隔离 |
| `judge_scores` | `contest_id → class_id` | 通过比赛间接隔离 |
| `system_settings` | `class_id` | 每个场次独立的系统状态 |

## 数据隔离保证

### 1. 创建新场次时

当管理员创建新场次时，会自动：
- 创建新的 `Class` 记录
- 创建对应的 `SystemSettings`
- 所有后续数据（比赛、辩手、投票、评分）都绑定到该 `class_id`

### 2. 切换场次时

当管理员切换场次时：
- 前端更新 `currentClassId`
- 所有API请求都携带正确的 `class_id` 参数
- 后端查询自动过滤到对应场次的数据

### 3. 数据保留策略

**✅ 已实现：** 所有历史数据都保留

- 场次切换不删除任何数据
- 每个场次的完整数据独立存储
- 可随时切换回历史场次查看数据

### 4. 数据删除策略

**级联删除：** 删除场次时会自动删除：
- 该场次的所有比赛 (`Contest`)
- 相关的投票记录 (`VoteRecord`)
- 相关的评分记录 (`JudgeScore`)
- 该场次的辩手用户 (`User` where role=student)
- 系统设置 (`SystemSettings`)

**保留数据：**
- 评委账号（可跨场次使用）
- 观众账号（class_id置空）
- 工作空间和管理员信息

## 优化措施

### 1. 数据库索引

为了提升查询性能和加强数据完整性，建议添加以下索引：

```sql
-- 投票记录唯一性约束
CREATE UNIQUE INDEX idx_vote_unique_per_voter_phase 
ON vote_records(contest_id, voter_id, vote_phase);

-- 评分记录唯一性约束
CREATE UNIQUE INDEX idx_score_unique_per_judge_debater 
ON judge_scores(contest_id, judge_id, debater_id);

-- 用户查询性能优化
CREATE INDEX idx_users_class_id_role 
ON users(class_id, role);

CREATE INDEX idx_users_class_id_team_side 
ON users(class_id, team_side, debater_position);

-- 比赛查询性能优化
CREATE INDEX idx_contests_class_id 
ON contests(class_id);
```

### 2. API层面保证

所有查询API都必须：
- 接受 `class_id` 参数
- 在WHERE子句中使用 `class_id` 过滤
- 验证用户权限（是否属于该场次）

### 3. 前端层面保证

- 路由守卫检查 `currentClassId`
- API调用自动附加当前场次ID
- 切换场次时刷新所有数据

## 验证方法

### 运行验证脚本

```bash
cd backend
python verify_data_isolation.py
```

### 手动验证步骤

1. **创建两个场次**
   - 场次A：初赛
   - 场次B：决赛

2. **在场次A添加数据**
   - 创建比赛配置
   - 分配辩手
   - 进行投票和评分

3. **切换到场次B**
   - 验证看不到场次A的数据
   - 创建独立的比赛配置
   - 验证数据完全隔离

4. **切换回场次A**
   - 验证所有数据完整保留
   - 可以继续使用

## 已知问题和解决方案

### 问题1：评委跨场次使用

**问题：** 评委账号可能需要在多个场次使用

**解决方案：** 
- 评委账号通过 `TeacherClass` 关联表管理
- 可以将同一评委添加到多个场次
- 每个场次的评分记录独立

### 问题2：观众账号迁移

**问题：** 观众可能从一个场次转移到另一个场次

**解决方案：**
- 修改观众的 `class_id`
- 历史投票记录仍然保留（通过contest_id关联）

### 问题3：数据清理

**问题：** 如何清理过期场次数据

**解决方案：**
```python
# 使用重置系统API（仅清空当前场次）
POST /admin/debate/reset?class_id=1

# 或者直接删除场次（级联删除所有数据）
DELETE /admin/classes/{class_id}
```

## 下一步工作

1. ✅ 运行验证脚本确认隔离完整性
2. ✅ 应用数据库索引优化
3. 🔄 增强前端场次切换体验
4. 🔄 添加场次数据统计仪表板
5. 🔄 实现场次数据导出功能
