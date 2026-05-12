from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.core.database import get_db

router = APIRouter()

# In-memory store for now (persists while server is running)
selected_assets = {
    "stocks": ["RELIANCE", "TCS", "INFY", "HDFCBANK"],
    "crypto": ["BTCUSDT", "ETHUSDT"]
}

class AssetsRequest(BaseModel):
    assets: List[str]

@router.get("/assets")
def get_assets():
    return selected_assets

@router.post("/assets")
def update_assets(req: AssetsRequest):
    global selected_assets
    
    stocks = []
    crypto = []
    
    for asset in req.assets:
        if asset in ["BTC-USD", "ETH-USD"]:
            # Convert to ccxt format
            crypto.append(asset.replace("-USD", "USDT"))
        else:
            stocks.append(asset)
    
    selected_assets["stocks"] = stocks
    selected_assets["crypto"] = crypto
    
    return {
        "message": "Assets updated successfully",
        "selected": selected_assets
    } 
