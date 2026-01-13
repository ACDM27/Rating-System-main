
import json
import asyncio
from fastapi import WebSocket
from typing import Dict, List, Callable, Awaitable


class ConnectionManager:
    """WebSocket 连接管理器 - 支持按班级隔离"""
    
    def __init__(self):
        # 存储所有活跃连接：class_id -> list[WebSocket]
        self.active_connections: dict[int, list[WebSocket]] = {}
        # 存储倒计时任务：class_id -> asyncio.Task
        self.countdown_tasks: dict[int, asyncio.Task] = {}
        # 存储当前倒计时数值：class_id -> int
        self.current_countdowns: dict[int, int] = {}
        # 不指定班级的全局连接（用于大屏等）
        self.global_connections: List[WebSocket] = []
        # 倒计时结束回调：class_id -> callback
        self.countdown_callbacks: dict[int, Callable[[int], Awaitable[None]]] = {}
    
    def get_countdown(self, class_id: int) -> int | None:
        """获取指定班级当前的倒计时值"""
        return self.current_countdowns.get(class_id)
    
    async def connect(self, websocket: WebSocket, class_id: int | None = None):
        """连接 WebSocket"""
        await websocket.accept()
        if class_id is not None:
            if class_id not in self.active_connections:
                self.active_connections[class_id] = []
            self.active_connections[class_id].append(websocket)
        else:
            self.global_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket, class_id: int | None = None):
        """断开 WebSocket 连接"""
        if class_id is not None:
            if class_id in self.active_connections:
                if websocket in self.active_connections[class_id]:
                    self.active_connections[class_id].remove(websocket)
        else:
            if websocket in self.global_connections:
                self.global_connections.remove(websocket)
    
    async def broadcast_state_update(
        self, 
        stage: str, 
        current_team: dict | None, 
        snatch_remaining: int,
        snatch_start_time: int | None = None,
        class_id: int | None = None,
        teacher_avg_score: float | None = None,
        student_avg_score: float | None = None,
        teacher_scoring_completed: bool = False,
        student_scoring_completed: bool = False,
        update_time: int | None = None
    ):
        """广播系统状态更新"""
        message = json.dumps({
            "type": "state_update",
            "data": {
                "stage": stage,
                "current_team": current_team,
                "snatch_slots_remaining": snatch_remaining,
                "snatch_start_time": snatch_start_time,
                "class_id": class_id,
                "teacher_avg_score": teacher_avg_score,
                "student_avg_score": student_avg_score,
                "teacher_scoring_completed": teacher_scoring_completed,
                "student_scoring_completed": student_scoring_completed,
                "update_time": update_time
            }
        })
        
        # 发送到指定班级的连接
        if class_id is not None and class_id in self.active_connections:
            for connection in self.active_connections[class_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass
        
        # 发送到全局连接
        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass
    
    async def broadcast_to_class(self, class_id: int, message: dict):
        """向指定班级广播消息"""
        if class_id not in self.active_connections:
            return
        
        text = json.dumps(message)
        for connection in self.active_connections[class_id]:
            try:
                await connection.send_text(text)
            except Exception:
                pass
        
        # 同时广播到全局连接
        for connection in self.global_connections:
            try:
                await connection.send_text(text)
            except Exception:
                pass

    async def _countdown_task(self, class_id: int):
        """倒计时协程"""
        while True:
            remaining = self.current_countdowns.get(class_id, 0)
            if remaining < 0:
                self._cleanup_countdown(class_id)
                break
            
            # 广播当前倒计时
            await self.broadcast_to_class(class_id, {
                "type": "TIMER_UPDATE",
                "data": {
                    "countdown": remaining
                }
            })
            
            if remaining == 0:
                # 倒计时结束，触发回调
                callback = self.countdown_callbacks.get(class_id)
                self._cleanup_countdown(class_id)
                if callback:
                    try:
                        await callback(class_id)
                    except Exception as e:
                        print(f"倒计时回调执行失败: {e}")
                break
                
            await asyncio.sleep(1)
            self.current_countdowns[class_id] -= 1

    def _cleanup_countdown(self, class_id: int):
        """清理倒计时相关资源"""
        if class_id in self.countdown_tasks:
            del self.countdown_tasks[class_id]
        if class_id in self.current_countdowns:
            del self.current_countdowns[class_id]
        if class_id in self.countdown_callbacks:
            del self.countdown_callbacks[class_id]

    def start_countdown(self, class_id: int, duration: int = 30, on_complete: Callable[[int], Awaitable[None]] | None = None):
        """开始倒计时"""
        # 如果已有任务在运行，先停止
        self.stop_countdown(class_id)
        
        self.current_countdowns[class_id] = duration
        if on_complete:
            self.countdown_callbacks[class_id] = on_complete
        # 创建新的后台任务
        task = asyncio.create_task(self._countdown_task(class_id))
        self.countdown_tasks[class_id] = task

    def stop_countdown(self, class_id: int):
        """停止倒计时"""
        if class_id in self.countdown_tasks:
            task = self.countdown_tasks[class_id]
            task.cancel()
            del self.countdown_tasks[class_id]
        
        if class_id in self.current_countdowns:
            del self.current_countdowns[class_id]
        
        if class_id in self.countdown_callbacks:
            del self.countdown_callbacks[class_id]

    async def broadcast_debate_update(
        self,
        stage: str,
        contest: dict | None,
        class_id: int,
        voting_enabled: dict,
        results_revealed: bool,
        progress: dict,
        update_time: int
    ):
        """广播辩论状态更新"""
        message = json.dumps({
            "type": "debate_update",
            "data": {
                "stage": stage,
                "contest": contest,
                "class_id": class_id,
                "voting_enabled": voting_enabled,
                "results_revealed": results_revealed,
                "progress": progress,
                "update_time": update_time
            }
        })
        
        # 发送到指定班级的连接
        if class_id in self.active_connections:
            for connection in self.active_connections[class_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass
        
        # 发送到全局连接（大屏等）
        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

    async def broadcast_vote_progress(self, class_id: int, total_votes: int, contest_id: int):
        """广播投票进度更新（不显示具体分布）"""
        message = json.dumps({
            "type": "vote_progress",
            "data": {
                "total_votes": total_votes,
                "contest_id": contest_id,
                "class_id": class_id
            }
        })
        
        # 只发送到全局连接（大屏显示）
        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass

    async def broadcast_results_reveal(self, class_id: int, results: dict):
        """广播结果揭晓"""
        message = json.dumps({
            "type": "results_reveal",
            "data": {
                "class_id": class_id,
                "results": results
            }
        })
        
        # 广播到所有连接
        if class_id in self.active_connections:
            for connection in self.active_connections[class_id]:
                try:
                    await connection.send_text(message)
                except Exception:
                    pass
        
        for connection in self.global_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


# 模块级别的 manager 实例
manager = ConnectionManager()