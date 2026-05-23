"""AI 资讯 API（Phase 5 占位）"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/latest")
async def get_latest_news():
    return {"message": "Phase 5: AI news module coming soon", "data": []}
