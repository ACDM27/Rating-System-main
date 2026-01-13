# 辩论赛智能投票系统 v2.0

## 系统简介

本系统是一个基于 B/S 架构的辩论赛全流程数字化管理系统，实现从选手管理、评委打分、观众投票到大屏实时揭晓的完整闭环。

## 核心功能

### 1. 管理后台 (PC端)
- **流程控制**: 开启/关闭赛前投票、赛后投票、评委打分
- **比赛管理**: 创建辩论比赛，设置辩题和正反方队伍
- **账号管理**: 批量导入观众账号，管理评委账号
- **结果揭晓**: 一键揭晓投票和评分结果

### 2. 评委端 (移动端)
- **多维度打分**: 6个评分维度，总分100分
  - 语言表达 (20分)
  - 逻辑推理 (20分)
  - 辩驳能力 (20分)
  - 临场反应 (15分)
  - 整体意识 (15分)
  - 综合印象 (10分)
- **移动优化**: 响应式设计，适配手机屏幕

### 3. 观众端 (移动端)
- **双次投票**: 赛前和赛后各一次投票机会
- **跑票制**: 通过赛前赛后票数变化判断胜负
- **极简设计**: 大按钮、防误触

### 4. 大屏展示端 (PC投屏)
- **盲投模式**: 投票过程中只显示人数，不显示具体票数
- **动态揭晓**: 柱状图动画展示最终结果
- **实时更新**: WebSocket 实时推送投票进度

## 技术栈

### 后端
- **框架**: FastAPI
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **ORM**: SQLAlchemy (异步)
- **认证**: JWT
- **实时通信**: WebSocket

### 前端
- **框架**: Vue 3 + Vite
- **UI组件**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios

## 快速开始

### 环境要求
- Python 3.10+
- Node.js 16+
- npm 或 pnpm

### 启动步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd Rating-System-main
   ```

2. **启动服务** (Windows)
   ```powershell
   .\run_local.ps1
   ```

3. **访问系统**
   - 前端: http://localhost:3000
   - 后端 API 文档: http://localhost:8000/docs
   - 管理后台: http://localhost:3000/admin/login
   - 评委/观众登录: http://localhost:3000/login
   - 大屏展示: http://localhost:3000/screen

### 默认账号
- **管理员**: 
  - 用户名: `admin`
  - 密码: `123456`

## 用户角色

| 角色 | 登录入口 | 主要功能 |
|------|---------|---------|
| 管理员 | `/admin/login` | 流程控制、比赛管理、账号管理 |
| 评委 | `/login` | 多维度打分 |
| 观众 | `/login` | 赛前/赛后投票 |
| 大屏 | `/screen` | 展示投票进度和结果 |

## 核心算法

### 个人评分算法
用于评选"优秀辩手"：
```
选手最终得分 = Σ(评委总分) / 评委人数
```
- 精度: 保留两位小数
- 同分排名: 按逻辑推理 → 辩驳能力维度排序

### 团队胜负算法
采用"跑票制"逻辑：
```
跑票值 = 赛后得票数 - 赛前得票数
```
- 跑票值大者获胜
- 正向增长越多越好，负向流失越少越好

## 项目结构

```
Rating-System-main/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── models/         # 数据模型
│   │   ├── routers/        # API 路由
│   │   ├── services/       # 业务逻辑
│   │   ├── schemas/        # Pydantic 模型
│   │   └── main.py         # 应用入口
│   ├── alembic/            # 数据库迁移
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/          # 页面组件
│   │   │   ├── admin/      # 管理后台
│   │   │   ├── judge/      # 评委端
│   │   │   ├── audience/   # 观众端
│   │   │   └── screen/     # 大屏端
│   │   ├── api/            # API 调用
│   │   ├── stores/         # 状态管理
│   │   └── router/         # 路由配置
│   └── package.json        # Node 依赖
└── run_local.ps1           # 启动脚本
```

## 开发指南

### 后端开发
```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端开发
```bash
cd frontend
npm install
npm run dev
```

### 数据库迁移
```bash
cd backend
alembic revision --autogenerate -m "migration message"
alembic upgrade head
```

## 常见问题

### Q: 前端看不到更新？
A: 强制刷新浏览器 (Ctrl+Shift+R) 清除缓存

### Q: 后端启动失败？
A: 检查 Python 版本 (需要 3.10+) 和依赖是否安装完整

### Q: 观众投票页面看不到？
A: 确保使用观众账号登录，且管理员已开启投票通道

## 更新日志

### v2.0.0 (2026-01-13)
- ✨ 全新的辩论赛投票系统
- 🗑️ 移除旧的AI课程答辩评分系统
- 🎨 优化移动端响应式设计
- 🐛 修复 API 路径不匹配问题
- 🔧 添加开发环境配置文件

## 许可证

MIT License

## 联系方式

如有问题，请提交 Issue 或联系开发团队。
