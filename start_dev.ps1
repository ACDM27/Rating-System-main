# 辩论赛投票系统 - 本地启动脚本
# 使用方法: 右键点击 -> 使用PowerShell运行

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  辩论赛投票系统 - 本地开发环境启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查是否在项目根目录
if (-not (Test-Path "backend") -or -not (Test-Path "frontend")) {
    Write-Host "错误: 请在项目根目录下运行此脚本!" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit
}

# 1. 启动后端
Write-Host "[1/2] 启动后端服务..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; Write-Host '后端服务启动中...' -ForegroundColor Yellow; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

# 等待后端启动
Start-Sleep -Seconds 3

# 2. 启动前端
Write-Host "[2/2] 启动前端服务..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; Write-Host '前端服务启动中...' -ForegroundColor Yellow; npm run dev"

# 等待前端启动
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  服务启动完成!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "后端地址: " -NoNewline
Write-Host "http://localhost:8000" -ForegroundColor Cyan
Write-Host "前端地址: " -NoNewline
Write-Host "http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "管理员账号: admin" -ForegroundColor Yellow
Write-Host "管理员密码: admin123" -ForegroundColor Yellow
Write-Host ""
Write-Host "提示: 两个PowerShell窗口已打开" -ForegroundColor Gray
Write-Host "      关闭窗口即可停止服务" -ForegroundColor Gray
Write-Host ""

# 自动打开浏览器
Start-Sleep -Seconds 3
Write-Host "正在打开浏览器..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Read-Host "按回车键关闭此窗口"
