# 辩论赛智能投票系统 - 快速启动指南

## 🚀 一键启动

### Windows 系统
```powershell
.\run_local.ps1
```

这个脚本会自动完成以下操作：
1. ✅ 创建 Python 虚拟环境（如果不存在）
2. ✅ 安装后端依赖
3. ✅ 初始化数据库并创建测试数据
4. ✅ 启动后端服务器 (端口 8000)
5. ✅ 安装前端依赖（如果不存在）
6. ✅ 启动前端开发服务器 (端口 3000)

## 📱 访问系统

启动成功后，会打开两个命令行窗口：
- **辩论赛系统-后端**: 后端 API 服务
- **辩论赛系统-前端**: 前端开发服务器

### 访问地址

| 功能 | 地址 | 说明 |
|------|------|------|
| 🌐 前端应用 | http://localhost:3000 | 主应用入口 |
| 📚 后端 API 文档 | http://localhost:8000/docs | Swagger API 文档 |
| 👨‍💼 管理后台 | http://localhost:3000/admin/login | 管理员登录入口 |
| 👥 评委/观众登录 | http://localhost:3000/login | 评委和观众登录入口 |
| 📺 大屏展示 | http://localhost:3000/screen | 投票结果大屏展示 |

### 默认账号

**管理员账号**：
- 用户名: `admin`
- 密码: `123456`

⚠️ **首次登录后请立即修改密码！**

## 🎯 使用流程

### 1. 管理员操作

1. **登录管理后台**
   - 访问 http://localhost:3000/admin/login
   - 使用默认账号登录

2. **创建辩论比赛**
   - 进入辩论赛管理页面
   - 点击"创建比赛"
   - 填写辩题、正方队伍名称、反方队伍名称

3. **创建观众账号**
   - 批量生成观众账号
   - 或手动创建观众账号

4. **创建评委账号**
   - 创建评委账号
   - 将评委添加到班级

5. **控制比赛流程**
   - 开启赛前投票
   - 开启赛后投票
   - 开启评委打分
   - 揭晓结果

### 2. 评委操作

1. **登录系统**
   - 访问 http://localhost:3000/login
   - 使用评委账号登录

2. **选择班级**
   - 如果评委负责多个班级，需要选择当前班级

3. **为辩手打分**
   - 进入评分页面
   - 为每位辩手的6个维度打分：
     - 语言表达 (20分)
     - 逻辑推理 (20分)
     - 辩驳能力 (20分)
     - 临场反应 (15分)
     - 整体意识 (15分)
     - 综合印象 (10分)
   - 提交评分

### 3. 观众操作

1. **登录系统**
   - 访问 http://localhost:3000/login
   - 使用观众账号登录

2. **投票**
   - 赛前投票：根据第一印象选择支持的队伍
   - 赛后投票：根据辩论表现选择支持的队伍
   - 每个阶段只能投票一次

### 4. 大屏展示

1. **打开大屏**
   - 访问 http://localhost:3000/screen
   - 无需登录

2. **展示内容**
   - 投票进度（盲投模式，只显示人数）
   - 结果揭晓（动画展示票数对比）
   - 辩手排名

## 🛠️ 手动启动（高级）

如果需要单独启动前端或后端：

### 启动后端
```powershell
cd backend
.\venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 启动前端
```powershell
cd frontend
npm run dev
```

## 🔧 常见问题

### Q: 端口被占用怎么办？

**后端端口 8000 被占用**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000
# 结束进程（替换 PID 为实际进程ID）
taskkill /PID <PID> /F
```

**前端端口 3000 被占用**：
- Vite 会自动使用下一个可用端口（如 3001）
- 或在 `frontend/vite.config.js` 中修改端口

### Q: 浏览器显示旧版本？

强制刷新浏览器缓存：
- Windows: `Ctrl + Shift + R` 或 `Ctrl + F5`
- Mac: `Cmd + Shift + R`

### Q: 数据库需要重置？

```powershell
cd backend
# 删除数据库文件
Remove-Item vote.db
# 重新初始化
.\venv\Scripts\python init_db.py --data
```

### Q: 依赖安装失败？

**后端依赖**：
```powershell
cd backend
.\venv\Scripts\python -m pip install --upgrade pip
.\venv\Scripts\python -m pip install -r requirements.txt
```

**前端依赖**：
```powershell
cd frontend
# 清除缓存
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
# 重新安装
npm install
```

## 📊 系统架构

```
辩论赛智能投票系统
├── 前端 (Vue 3 + Vite + Element Plus)
│   ├── 管理后台 - 流程控制、比赛管理
│   ├── 评委端 - 多维度打分
│   ├── 观众端 - 赛前/赛后投票
│   └── 大屏端 - 结果展示
│
└── 后端 (FastAPI + SQLAlchemy + SQLite)
    ├── 认证系统 - JWT 认证
    ├── 投票系统 - 跑票制计算
    ├── 评分系统 - 多维度评分
    └── WebSocket - 实时推送
```

## 🎨 核心功能

### 评委打分算法
```
选手最终得分 = Σ(评委总分) / 评委人数
```
- 精度：保留两位小数
- 同分排名：按逻辑推理 → 辩驳能力维度排序

### 团队胜负算法（跑票制）
```
跑票值 = 赛后得票数 - 赛前得票数
```
- 跑票值大者获胜
- 体现辩论说服力

## 📞 技术支持

如有问题，请查看：
1. 📖 README.md - 完整系统文档
2. 📝 CLEANUP_SUMMARY.md - 系统清理记录
3. 🌐 http://localhost:8000/docs - API 文档

---

**版本**: v2.0.0  
**更新日期**: 2026-01-13  
**系统名称**: 辩论赛智能投票系统
