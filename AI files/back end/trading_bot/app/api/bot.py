from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import BotActivity
from app.services.trading_loop import start_bot, stop_bot, bot_running

router = APIRouter()

@router.get("/activity")
def get_activity(db: Session = Depends(get_db)):
    activities = db.query(BotActivity).filter(
        BotActivity.user_id == 1
    ).order_by(BotActivity.created_at.desc()).limit(20).all()
    
    return [
        {
            "id": a.id,
            "message": a.message,
            "activity_type": a.activity_type,
            "symbol": a.symbol,
            "created_at": str(a.created_at)
        }
        for a in activities
    ]
@router.get("/status")
def get_status():
    return {"running": bot_running}


@router.get("/start")
@router.post("/start")
async def start_trading():
    result = start_bot()
    if result:
        return {"message": "Bot started successfully! 🚀"}
    return {"message": "Bot is already running!"}

@router.get("/stop")
@router.post("/stop")
def stop_trading():
    stop_bot()
    return {"message": "Bot stopped! 🛑"}