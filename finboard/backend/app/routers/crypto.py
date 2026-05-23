"""加密货币 API（Phase 3 占位）"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/tickers")
async def get_crypto_tickers():
    return {"message": "Phase 3: crypto module coming soon", "data": []}
