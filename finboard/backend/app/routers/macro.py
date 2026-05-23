"""宏观经济 API（Phase 4 占位）"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/indicators")
async def get_macro_indicators():
    return {"message": "Phase 4: macro module coming soon", "data": []}
