from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db
from app.models.models import Trade, Portfolio, BotActivity

router = APIRouter()

class TradeRequest(BaseModel):
    symbol: str
    side: str
    quantity: float
    entry_price: float

@router.get("/trades")
def get_trades(db: Session = Depends(get_db)):
    trades = db.query(Trade).filter(
        Trade.user_id == 1
    ).order_by(Trade.created_at.desc()).all()
    
    return [
        {
            "id": t.id,
            "symbol": t.symbol,
            "side": t.side,
            "quantity": t.quantity,
            "entry_price": t.entry_price,
            "current_price": t.current_price,
            "pnl": round(t.pnl, 2),
            "status": t.status,
            "created_at": str(t.created_at)
        }
        for t in trades
    ]

@router.post("/trades")
def place_trade(req: TradeRequest, db: Session = Depends(get_db)):
    trade = Trade(
        user_id=1,
        symbol=req.symbol,
        side=req.side,
        quantity=req.quantity,
        entry_price=req.entry_price,
        current_price=req.entry_price,
        pnl=0.0,
        status="OPEN"
    )
    db.add(trade)

    activity = BotActivity(
        user_id=1,
        message=f"{req.side} signal executed — {req.symbol} — qty: {req.quantity}",
        activity_type=req.side,
        symbol=req.symbol
    )
    db.add(activity)
    db.commit()
    db.refresh(trade)

    return {"message": "Trade placed successfully", "trade_id": trade.id}

@router.put("/trades/{trade_id}/close")
def close_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(
        Trade.id == trade_id,
        Trade.user_id == 1
    ).first()
    
    if not trade:
        return {"error": "Trade not found"}
    
    trade.status = "CLOSED"
    db.commit()
    return {"message": "Trade closed successfully"}