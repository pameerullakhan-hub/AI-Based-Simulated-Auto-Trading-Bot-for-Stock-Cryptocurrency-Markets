from fastapi import APIRouter
from app.services.kama import get_kama_signal

router = APIRouter()

@router.get("/kama/{symbol}")
def kama_signal(symbol: str, is_crypto: bool = False):
    return get_kama_signal(symbol, is_crypto) 
