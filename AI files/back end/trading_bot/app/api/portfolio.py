from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.models import Portfolio, Trade

router = APIRouter()

@router.get("/portfolio")
def get_portfolio(db: Session = Depends(get_db)):
    portfolio = db.query(Portfolio).filter(
        Portfolio.user_id == 1
    ).first()
    
    if not portfolio:
        portfolio = Portfolio(
            user_id=1,
            total_value=100000.0,
            equity=0.0,
            daily_pnl=0.0,
            total_pnl=0.0
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    open_trades = db.query(Trade).filter(
        Trade.user_id == 1,
        Trade.status == "OPEN"
    ).all()
    
    equity = sum(t.pnl for t in open_trades)
    
    return {
        "total_value": portfolio.total_value,
        "equity": round(equity, 2),
        "daily_pnl": portfolio.daily_pnl,
        "total_pnl": portfolio.total_pnl
    }