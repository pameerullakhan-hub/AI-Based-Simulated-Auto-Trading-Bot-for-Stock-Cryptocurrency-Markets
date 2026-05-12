from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine
from app.models import models
from app.api import auth, market, kama, sentiment, predictions, portfolio, trades, bot, bot_config

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Trading Bot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(market.router, prefix="/api/market", tags=["Market"])
app.include_router(kama.router, prefix="/api", tags=["KAMA"])
app.include_router(sentiment.router, prefix="/api", tags=["Sentiment"])
app.include_router(predictions.router, prefix="/api", tags=["Predictions"])
app.include_router(portfolio.router, prefix="/api", tags=["Portfolio"])
app.include_router(trades.router, prefix="/api", tags=["Trades"])
app.include_router(bot.router, prefix="/api/bot", tags=["Bot"])
app.include_router(bot_config.router, prefix="/api/bot", tags=["Bot Config"])

@app.get("/")
def root():
    return {"status": "AI Trading Bot is running "}