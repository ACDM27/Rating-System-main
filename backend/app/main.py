import subprocess
import json
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth_router, admin_router, vote_router, judge_score_router
from app.routers.vote_records import router as vote_records_router
from app.websocket import manager


def run_migrations():
    """运行数据库迁移"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Database migrations completed successfully")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Migration failed: {e.stderr}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时运行数据库迁移
    run_migrations()
    yield


app = FastAPI(
    title="辩论赛智能投票系统",
    description="支持评委打分、观众投票、大屏展示的辩论赛全流程管理系统",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(vote_router)
app.include_router(judge_score_router)
app.include_router(vote_records_router)


@app.get("/")
async def root():
    return {"message": "辩论赛智能投票系统 API", "version": "2.0.0"}



@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, class_id: int | None = Query(None)):
    """WebSocket 连接端点，支持按班级隔离"""
    await manager.connect(websocket, class_id)
    try:
        while True:
            # 使用 receive_text 避免 JSON 解析错误导致连接断开
            text = await websocket.receive_text()
            
            # 处理 ping 消息
            if text == "ping":
                await websocket.send_text("pong")
                continue
            
            try:
                data = json.loads(text)
                # 处理客户端消息
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("action") == "SNATCH":
                    # 提问逻辑通过 HTTP API 处理，这里仅保持连接
                    pass
            except json.JSONDecodeError:
                # 忽略无法解析的消息
                pass
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(websocket, class_id)

