# 定义变量
COMPOSE_FILE = docker-compose.yaml

# 读取 .env 文件中的版本变量
-include .env
export

# 获取版本号的函数，如果 .env 中没有设置则使用默认值
BACKEND_VERSION ?= latest
FRONTEND_VERSION ?= latest

# 默认目标
.PHONY: all
all: build

# 构建所有镜像
.PHONY: build
build:
	@echo "构建所有镜像..."
	@echo "后端版本: $(BACKEND_VERSION)"
	@echo "前端版本: $(FRONTEND_VERSION)"
	@echo "构建后端镜像: rating_system_backend:$(BACKEND_VERSION)"
	docker build -t rating_system_backend:$(BACKEND_VERSION) ./backend
	@echo "构建前端镜像: rating_system_frontend:$(FRONTEND_VERSION)"
	docker build -t rating_system_frontend:$(FRONTEND_VERSION) ./frontend

# 构建后端镜像
.PHONY: build-backend
build-backend:
	@echo "构建后端镜像: rating_system_backend:$(BACKEND_VERSION)"
	docker build -t rating_system_backend:$(BACKEND_VERSION) ./backend

# 构建前端镜像
.PHONY: build-frontend
build-frontend:
	@echo "构建前端镜像: rating_system_frontend:$(FRONTEND_VERSION)"
	docker build -t rating_system_frontend:$(FRONTEND_VERSION) ./frontend

# 启动所有服务
.PHONY: up
up:
	@echo "启动所有服务..."
	@echo "使用后端版本: $(BACKEND_VERSION)"
	@echo "使用前端版本: $(FRONTEND_VERSION)"
	docker compose -f $(COMPOSE_FILE) up -d

# 停止所有服务
.PHONY: down
down:
	@echo "停止所有服务..."
	docker compose -f $(COMPOSE_FILE) down

# 重启所有服务
.PHONY: restart
restart: down up

# 查看服务状态
.PHONY: ps
ps:
	docker compose -f $(COMPOSE_FILE) ps

# 查看日志
.PHONY: logs
logs:
	docker compose -f $(COMPOSE_FILE) logs -f

# 查看后端日志
.PHONY: logs-backend
logs-backend:
	docker compose -f $(COMPOSE_FILE) logs -f backend

# 查看前端日志
.PHONY: logs-frontend
logs-frontend:
	docker compose -f $(COMPOSE_FILE) logs -f frontend

# 查看worker日志
.PHONY: logs-worker
logs-worker:
	docker compose -f $(COMPOSE_FILE) logs -f worker

# 进入后端容器
.PHONY: exec-backend
exec-backend:
	docker compose -f $(COMPOSE_FILE) exec backend bash

# 进入前端容器
.PHONY: exec-frontend
exec-frontend:
	docker compose -f $(COMPOSE_FILE) exec frontend sh

# 删除项目相关的镜像
.PHONY: clean-images
clean-images:
	@echo "删除项目镜像..."
	@echo "删除后端镜像: rating_system_backend:$(BACKEND_VERSION)"
	docker rmi rating_system_backend:$(BACKEND_VERSION) || true
	@echo "删除前端镜像: rating_system_frontend:$(FRONTEND_VERSION)"
	docker rmi rating_system_frontend:$(FRONTEND_VERSION) || true

# 完全重建（清理后重新构建）
.PHONY: rebuild
rebuild: clean-images build

# 部署（构建并启动）
.PHONY: deploy
deploy: build up

# 显示版本信息
.PHONY: version
version:
	@echo "当前版本配置："
	@echo "  后端版本: $(BACKEND_VERSION)"
	@echo "  前端版本: $(FRONTEND_VERSION)"

# 显示帮助信息
.PHONY: help
help:
	@echo "可用的命令："
	@echo "  build          - 构建所有镜像（使用 .env 中的版本）"
	@echo "  build-backend  - 构建后端镜像（使用 .env 中的版本）"
	@echo "  build-frontend - 构建前端镜像（使用 .env 中的版本）"
	@echo "  up             - 启动所有服务"
	@echo "  down           - 停止所有服务"
	@echo "  restart        - 重启所有服务"
	@echo "  ps             - 查看服务状态"
	@echo "  logs           - 查看所有服务日志"
	@echo "  logs-backend   - 查看后端日志"
	@echo "  logs-frontend  - 查看前端日志"
	@echo "  logs-worker    - 查看worker日志"
	@echo "  exec-backend   - 进入后端容器"
	@echo "  exec-frontend  - 进入前端容器"
	@echo "  clean-images   - 删除项目镜像（使用 .env 中的版本）"
	@echo "  rebuild        - 完全重建镜像"
	@echo "  deploy         - 部署（构建并启动）"
	@echo "  version        - 显示当前版本配置"
	@echo "  help           - 显示此帮助信息"
