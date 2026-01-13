# 系统启动问题修复记录

## 问题 1: 模型导入错误

### 错误信息
```
ModuleNotFoundError: No module named 'app.models.score_record'
```

### 原因
在删除旧系统代码时，删除了 `score_record.py` 和 `question.py` 模型文件，但以下文件仍在导入它们：
- `app/models/__init__.py`
- `app/schemas/__init__.py`
- `app/schemas/score.py`

### 解决方案
✅ **已修复**：
1. 更新 `app/models/__init__.py` - 删除 `ScoreRecord` 和 `Question` 的导入
2. 更新 `app/schemas/__init__.py` - 删除 `score` 和 `question` schema 的导入

## 问题 2: PowerShell 脚本语法错误

### 错误信息
```
标记"&&"不是此版本中的有效语句分隔符
字符串缺少终止符: "
```

### 原因
1. 旧版本 PowerShell 不支持 `&&` 作为命令分隔符
2. 中文字符可能导致编码问题

### 解决方案
✅ **已修复**：
1. 使用 `&` 代替 `&&` (CMD 命令分隔符)
2. 简化命令结构，使用变量存储命令
3. 使用英文文本避免编码问题

## 问题 3: admin.py 懒加载导入错误

### 错误信息
```
ModuleNotFoundError: No module named 'app.services.score'
```

### 原因
`admin.py` 中的 `get_system_state` 函数内部使用了 lazy import 导入已删除的模块，导致运行时报错。

### 解决方案
✅ **已修复**：
1. **重写 `admin.py`**：彻底重写了该文件，移除了所有与旧评分系统、提问系统相关的逻辑。
2. 只保留了辩论赛系统需要的核心 API：
   - `GET /users`: 获取用户列表
   - `GET /state`: 获取系统状态
   - `POST /stage/set`: 设置比赛阶段
   - `GET /progress`: 获取进度（返回空值）

## 问题 4: 前端界面文案和路由过时

### 问题描述
登录页面仍显示"AI课程答辩评分系统"，且路由跳转指向旧的角色页面（student/teacher）。

### 解决方案
✅ **已修复**：
1. **更新 `AdminLogin.vue`**:
   - 标题改为 "辩论赛管理后台"
   - 副标题改为 "辩论赛智能投票系统"
2. **更新 `Login.vue`**:
   - 标题改为 "辩论赛智能投票系统"
   - 修复路由跳转：观众自动进入 `/audience`
3. **更新 `ClassSelect.vue`**:
   - 修复路由跳转：管理员 -> `/admin/debate`，评委 -> `/judge`，观众 -> `/audience`

## 当前系统状态

### ✅ 可以正常运行的功能

**后端 (FastAPI)**:
- ✅ 认证系统 (`auth.py`)
- ✅ 管理路由 (`admin.py`) - **已重构，纯净版**
- ✅ 投票系统 (`vote.py`)
- ✅ 评委打分 (`judge_score.py`)
- ✅ WebSocket 实时通信

**前端 (Vue 3)**:
- ✅ **登录界面** - 已更新为辩论赛主题
- ✅ 管理后台
- ✅ 评委打分页面
- ✅ 观众投票页面
- ✅ 大屏展示页面

## 业务逻辑变更 (2026-01-13)

### 班级管理 -> 赛场管理
应用户要求，将通用的"班级管理"逻辑修改为辩论赛专用的"初赛/决赛"模式：

1. **界面文案调整**:
   - "班级" -> "比赛场次" / "赛场"
   - "22大数据一区" -> "初赛"
   - "22大数据二区" -> "决赛"

2. **功能调整**:
   - 移除了 `DebateDashboard` 中的"班级管理"跳转按钮，防止用户误操作。
   - 移除了 `ClassSelect` 中管理员创建班级的入口。
   - 修改了数据库初始化逻辑，默认创建"初赛"和"决赛"两个场次。

3. **数据迁移**:
   - 执行了 `rename_classes.py` 脚本，将现有数据库中的班级重命名为新格式。

### 恢复管理功能 (2026-01-13)

### 观众和评委管理
修复了管理端无法跳转到观众管理和评委管理页面的问题：

1. **新页面开发**:
   - 创建 `AudienceManage.vue`: 支持批量生成观众账号、导出账号。
   - 创建 `JudgeManage.vue`: 支持添加现有评委或创建新评委。

2. **后端 API 补全**:
   - 在 `admin.py` 中恢复了用户管理相关的接口。
   - 包括批生成观众、创建评委、添加评委到赛场等功能。

3. **路由配置**:
   - 在前端路由中重新注册了 `/admin/students` 和 `/admin/teachers` 路径。

### 功能增强 (2026-01-14)
**观众管理增强**:
1. **Excel 导入**:
   - 前端引入 `xlsx` 库，支持解析 .xlsx/.xls 文件。
   - 实现前端预览和确认逻辑。
   - 后端新增 `POST /students/import` 接口处理批量数据。
   - **新增**：支持下载标准的 Excel 导入模板，方便管理员操作。
2. **手动添加**:
   - 支持逐个添加观众账号（指定用户名、密码、名称）。

### 功能精简 (2026-01-14)
**观众管理优化**:
1. **移除批量生成**: 删除了基于前缀和数量的批量生成功能，避免从生成错误数据。
2. **简化字段**: 
   - 手动添加和Excel导入时，只需提供**用户名**和**密码**。
   - **显示名称**默认与用户名一致，不再强制要求输入。

### 修复比赛创建功能 (2026-01-14)
**问题**: 管理员后台无法创建比赛。
**原因**: 后端 `admin.py` 重构时遗漏了辩论赛流程控制相关的 API (如 `/debate/contest`, `/debate/stage` 等)。
**修复**: 
1. 引入了 `Contest`, `VoteRecord`, `JudgeScore` 模型。
2. 在 `admin.py` 中补全了所有辩论赛专用接口，包括创建比赛、阶段控制、进度查询和结果揭晓。
3. 修正了文件末尾可能存在的重复代码。

### ⚠️ 保留但不使用的旧功能

以下功能代码仍然存在，但不会被辩论赛系统调用：

**后端**:
- `admin.py` 中的提问系统相关端点
- `admin.py` 中的学生评分相关端点
- `services/calculation.py` 中的旧评分计算逻辑

**前端**:
- 无（已全部清理）

这些代码不会影响辩论赛系统的正常运行，只是在 API 文档中可见。

## 启动系统

### 方法 1: 使用启动脚本 (推荐)
```powershell
.\run_local.ps1
```

### 方法 2: 手动启动

**后端**:
```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**前端**:
```powershell
cd frontend
npm run dev
```

## 访问系统

| 功能 | URL |
|------|-----|
| 前端应用 | http://localhost:3000 |
| 后端 API 文档 | http://localhost:8000/docs |
| 管理后台 | http://localhost:3000/admin/login |
| 评委/观众登录 | http://localhost:3000/login |
| 大屏展示 | http://localhost:3000/screen |

## 默认账号

- **用户名**: admin
- **密码**: 123456

⚠️ **首次登录后请立即修改密码！**

## 已修复的文件列表

### 后端
1. `backend/app/models/__init__.py` - 删除旧模型导入
2. `backend/app/schemas/__init__.py` - 删除旧 schema 导入
3. `backend/app/routers/__init__.py` - 删除旧路由导入
4. `backend/app/main.py` - 更新应用信息

### 前端
1. `frontend/src/router/index.js` - 删除旧路由
2. `frontend/src/api/vote.js` - 修复 API 路径
3. `frontend/src/stores/system.js` - 添加辩论进度支持
4. `frontend/.env.development` - 添加开发环境配置

### 配置文件
1. `run_local.ps1` - 修复 PowerShell 兼容性问题

## 下一步优化建议

虽然系统现在可以正常运行，但以下优化可以进一步提升代码质量：

### 优先级 P1 (可选)
1. **清理 `admin.py`**: 删除提问系统和学生评分相关的端点
2. **删除旧 schema 文件**: 删除 `score.py` 和 `question.py`
3. **清理 `services/`**: 删除 `calculation.py` 中的旧逻辑

### 优先级 P2 (可选)
1. **添加单元测试**: 为核心功能添加测试
2. **优化数据库**: 添加索引提升查询性能
3. **添加日志**: 完善系统日志记录

## 系统版本

- **版本**: v2.0.0
- **名称**: 辩论赛智能投票系统
- **状态**: ✅ 可正常运行
- **最后更新**: 2026-01-13

---

**注意**: 所有修复已完成，系统可以正常启动和使用！
