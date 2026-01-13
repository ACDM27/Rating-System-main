from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.vote import router as vote_router
from app.routers.judge_score import router as judge_score_router

__all__ = ["auth_router", "admin_router", "vote_router", "judge_score_router"]
