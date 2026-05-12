from fastapi import APIRouter
from app.services.market_service import get_all_prices

router = APIRouter()

@router.get("/prices")
def get_prices():
    return get_all_prices()