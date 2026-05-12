import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.models import Trade, Portfolio, BotActivity
from app.services.signal_fusion import fuse_signals
from app.api.bot_config import selected_assets
from app.services.angel_one import connect_angel_one, place_paper_order, get_stock_price

# Bot state
bot_running = False
CAPITAL_PER_TRADE = 0.20
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.05

# Connect Angel One on startup
try:
    connect_angel_one()
except Exception as e:
    print(f"Angel One startup connection failed: {e}")

def log_activity(db: Session, message: str, activity_type: str, symbol: str = None):
    activity = BotActivity(
        user_id=1,
        message=message,
        activity_type=activity_type,
        symbol=symbol
    )
    db.add(activity)
    db.commit()

def get_portfolio_value(db: Session):
    portfolio = db.query(Portfolio).filter(Portfolio.user_id == 1).first()
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
    return portfolio

def has_open_trade(db: Session, symbol: str):
    return db.query(Trade).filter(
        Trade.user_id == 1,
        Trade.symbol == symbol,
        Trade.status == "OPEN"
    ).first()

def place_trade(db: Session, symbol: str, side: str, price: float, quantity: float):
    trade = Trade(
        user_id=1,
        symbol=symbol,
        side=side,
        quantity=quantity,
        entry_price=price,
        current_price=price,
        pnl=0.0,
        status="OPEN"
    )
    db.add(trade)
    db.commit()
    log_activity(
        db,
        f"{side} signal executed — {symbol} — qty: {quantity:.4f} @ ₹{price:.2f}",
        side,
        symbol
    )

def close_trade(db: Session, trade: Trade, current_price: float):
    if trade.side == "BUY":
        pnl = (current_price - trade.entry_price) * trade.quantity
    else:
        pnl = (trade.entry_price - current_price) * trade.quantity
    
    trade.pnl = round(pnl, 2)
    trade.current_price = current_price
    trade.status = "CLOSED"
    
    portfolio = get_portfolio_value(db)
    portfolio.total_value += pnl
    portfolio.total_pnl += pnl
    db.commit()
    
    log_activity(
        db,
        f"Trade closed — {trade.symbol} — PnL: ₹{pnl:.2f}",
        "SELL" if trade.side == "BUY" else "BUY",
        trade.symbol
    )

def check_stop_loss_take_profit(db: Session):
    open_trades = db.query(Trade).filter(
        Trade.user_id == 1,
        Trade.status == "OPEN"
    ).all()
    
    for trade in open_trades:
        if trade.entry_price == 0:
            continue
        change_pct = (trade.current_price - trade.entry_price) / trade.entry_price
        if trade.side == "BUY":
            if change_pct <= -STOP_LOSS_PCT:
                log_activity(db, f"Stop loss triggered — {trade.symbol}", "SELL", trade.symbol)
                close_trade(db, trade, trade.current_price)
            elif change_pct >= TAKE_PROFIT_PCT:
                log_activity(db, f"Take profit triggered — {trade.symbol}", "SELL", trade.symbol)
                close_trade(db, trade, trade.current_price)

async def run_trading_loop():
    global bot_running
    bot_running = True
    print("🤖 Auto trading loop started!")
    
    while bot_running:
        db = SessionLocal()
        try:
            portfolio = get_portfolio_value(db)
            capital_per_trade = portfolio.total_value * CAPITAL_PER_TRADE
            
            check_stop_loss_take_profit(db)
            
            all_assets = [
                {"symbol": s, "is_crypto": False}
                for s in selected_assets["stocks"]
            ] + [
                {"symbol": s, "is_crypto": True}
                for s in selected_assets["crypto"]
            ]
            
            for asset in all_assets:
                symbol = asset["symbol"]
                is_crypto = asset["is_crypto"]
                
                try:
                    signal = fuse_signals(symbol, is_crypto)
                    decision = signal["decision"]
                    price = signal["kama_price"]
                    msi = signal["msi"]
                    
                    if price == 0:
                        continue
                    
                    quantity = round(capital_per_trade / price, 4)
                    existing_trade = has_open_trade(db, symbol)
                    
                    if decision == "BUY" and not existing_trade:
                        # Place real Angel One order for stocks
                        if not is_crypto:
                            angel_order = place_paper_order(symbol, "BUY", max(1, int(quantity)))
                            if angel_order:
                                price = angel_order["price"]
                                log_activity(db, f"Angel One BUY executed — {symbol} — qty: {int(quantity)} @ ₹{price}", "BUY", symbol)
                        place_trade(db, symbol, "BUY", price, quantity)
                        print(f"✅ BUY {symbol} @ {price}")
                        
                    elif decision == "SELL" and existing_trade:
                        # Place real Angel One sell for stocks
                        if not is_crypto:
                            angel_order = place_paper_order(symbol, "SELL", max(1, int(existing_trade.quantity)))
                            if angel_order:
                                log_activity(db, f"Angel One SELL executed — {symbol} @ ₹{angel_order['price']}", "SELL", symbol)
                        close_trade(db, existing_trade, price)
                        print(f"🔴 SELL {symbol} @ {price}")
                        
                    else:
                        msg = f"HOLD — insufficient confidence — {symbol}" if decision == "HOLD" else f"SELL signal — no open position — {symbol}"
                        log_activity(db, msg, decision, symbol)
                        print(f"⏸️ {decision} {symbol} — MSI: {msi:.3f}")
                        
                except Exception as e:
                    print(f"Error processing {symbol}: {e}")
                    log_activity(db, f"Signal error — {symbol}: {str(e)[:50]}", "BLOCK", symbol)
            
            print(f"✅ Loop done at {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            print(f"Trading loop error: {e}")
        finally:
            db.close()
        
        await asyncio.sleep(300)
    
    print("🛑 Trading loop stopped!")

def start_bot():
    global bot_running
    if not bot_running:
        asyncio.create_task(run_trading_loop())
        return True
    return False

def stop_bot():
    global bot_running
    bot_running = False
    return True
