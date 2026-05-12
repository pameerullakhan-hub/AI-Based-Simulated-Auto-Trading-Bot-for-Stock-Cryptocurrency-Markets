from fastapi import APIRouter
from app.services.signal_fusion import fuse_signals, fuse_all_signals

router = APIRouter()

@router.get("/predictions")
def get_all_predictions():
    return fuse_all_signals()

@router.get("/predictions/{symbol}")
def get_prediction(symbol: str, is_crypto: bool = False):
    return fuse_signals(symbol, is_crypto) 
