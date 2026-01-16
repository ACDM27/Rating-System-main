# 本地开发和测试指南

## 📋 环境配置说明

本项目使用环境变量来管理不同环境的配置，无需硬编码API地址。

### 配置文件

| 文件 | 环境 | 说明 |
|------|------|------|
| `.env.development` | 开发环境 | `npm run dev` 时使用 |
| `.env.production` | 生产环境 | `npm run build` 时使用 |

### 默认配置

**开发环境** (`.env.development`)
```env
VITE_API_BASE=http://localhost:8000
```

**生产环境** (`.env.production`)
```env
VITE_API_BASE=
```
- 空值表示使用相对路径
- 前端和后端在同一域名下运行

## 🚀 本地开发流程

### 1. 启动后端服务

```bash
# 进入后端目录
cd backend

# 激活虚拟环境（如果使用）
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# 启动后端
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端将运行在: `http://localhost:8000`

### 2. 启动前端开发服务器

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install

# 启动开发服务器
npm run dev
```

前端将运行在: `http://localhost:5173` (Vite默认端口)

### 3. 访问应用

浏览器打开: `http://localhost:5173`

## 🔧 修改代码后的工作流

### 方式一：热重载（推荐）

前端代码修改后会**自动热重载**，无需手动刷新：

1. 修改 `.vue`、`.js` 文件
2. 保存文件
3. 浏览器自动更新 ✨

后端代码修改后会**自动重启**（因为使用了 `--reload`）：

1. 修改 `.py` 文件
2. 保存文件
3. uvicorn 自动重启 ✨

### 方式二：手动刷新

- 前端：按 `F5` 或 `Ctrl+R` 刷新浏览器
- 后端：如果没有自动重启，`Ctrl+C` 停止后重新运行启动命令

## 📦 构建生产版本

### 本地构建测试

```bash
cd frontend

# 构建生产版本
npm run build

# 预览构建结果
npm run preview
```

构建产物在 `frontend/dist` 目录

### 验证生产构建

```bash
# 预览服务器会运行在 http://localhost:4173
npm run preview
```

## 🌐 不同部署场景的配置

### 场景1: 前后端同一服务器（Docker部署）

**生产环境配置** (`.env.production`):
```env
VITE_API_BASE=
```

前端通过相对路径访问后端，Nginx配置代理。

### 场景2: 前后端分离部署

**生产环境配置** (`.env.production`):
```env
VITE_API_BASE=http://your-backend-domain.com
```

或使用HTTPS:
```env
VITE_API_BASE=https://api.your-domain.com
```

### 场景3: 本地开发连接远程后端

**开发环境配置** (`.env.development`):
```env
VITE_API_BASE=http://your-remote-server:8000
```

## 🔍 调试技巧

### 1. 检查API地址

在浏览器控制台输入:
```javascript
console.log(import.meta.env.VITE_API_BASE)
```

### 2. 查看网络请求

- 打开浏览器开发者工具 (F12)
- 切换到 "Network" 标签
- 查看API请求的地址是否正确

### 3. 后端日志

后端终端会显示所有请求:
```
INFO:     127.0.0.1:xxxxx - "GET /api/xxx" 200 OK
```

### 4. 前端日志

在代码中添加调试信息:
```javascript
console.log('API请求:', API_BASE)
console.log('当前场次:', authStore.currentClassId)
```

## 📝 常见问题

### Q: 修改了环境变量，为什么没生效？

**A**: Vite需要重启才能读取环境变量：

1. 停止开发服务器 (`Ctrl+C`)
2. 重新运行 `npm run dev`

### Q: 如何快速切换API地址？

**A**: 直接修改 `.env.development`:

```env
# 本地后端
VITE_API_BASE=http://localhost:8000

# 或远程后端
VITE_API_BASE=http://192.168.1.100:8000
```

保存后重启开发服务器。

### Q: 生产环境如何指定API地址？

**A**: 修改 `.env.production` 或在构建时指定:

```bash
# 方式1: 修改 .env.production
VITE_API_BASE=https://api.example.com

# 方式2: 构建时指定
VITE_API_BASE=https://api.example.com npm run build
```

### Q: CORS错误怎么办？

**A**: 确保后端配置了CORS。在 `backend/app/main.py` 中:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # 添加前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 🎯 推荐工作流

### 日常开发

1. **早上启动**
   ```bash
   # 终端1: 启动后端
   cd backend && python -m uvicorn app.main:app --reload --port 8000
   
   # 终端2: 启动前端
   cd frontend && npm run dev
   ```

2. **开发中**
   - 修改代码 → 自动更新
   - 测试功能
   - Git提交

3. **下班前**
   - 停止服务器 (`Ctrl+C`)
   - Git push

### 测试生产版本

```bash
# 1. 构建
cd frontend && npm run build

# 2. 预览
npm run preview

# 3. 验证功能正常

# 4. 推送到GitHub
git add . && git commit -m "..." && git push
```

### Docker部署

```bash
# 直接使用docker-compose构建和启动
docker-compose up --build
```

## 📱 移动端测试

### 1. 获取本机IP

```bash
# Windows
ipconfig

# 查找 IPv4 地址，例如: 192.168.1.100
```

### 2. 修改开发配置

`.env.development`:
```env
VITE_API_BASE=http://192.168.1.100:8000
```

### 3. 启动服务

```bash
# 后端
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端
npm run dev -- --host
```

### 4. 手机访问

浏览器打开: `http://192.168.1.100:5173`

## 💡 小提示

1. **使用VSCode**：安装Volar插件获得更好的Vue开发体验
2. **快捷键**：`Ctrl+\`` 在VSCode中快速打开终端
3. **多终端**：使用VSCode的分屏终端同时查看前后端日志
4. **Git忽略**：`.env.local` 会被自动忽略，可用于个人配置

## 🔗 相关文档

- [Vite 环境变量文档](https://vitejs.dev/guide/env-and-mode.html)
- [Axios 配置文档](https://axios-http.com/docs/config_defaults)
- [Vue Router 文档](https://router.vuejs.org/)
