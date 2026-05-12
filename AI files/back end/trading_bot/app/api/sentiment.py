from fastapi import APIRouter
from app.services.finbert import get_market_sentiment

router = APIRouter()

@router.get("/sentiment/{symbol}")
def sentiment(symbol: str):
    return get_market_sentiment(symbol)

@router.get("/sentiment")
def overall_sentiment():
    symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK", "Bitcoin", "Ethereum"]
    all_headlines = []
    total_msi = 0

    for s in symbols:
        data = get_market_sentiment(s)
        total_msi += data["msi"]
        all_headlines.extend(data["headlines"])

    avg_msi = round((total_msi / len(symbols)) * 100, 1)

    return {
        "overall_sentiment": avg_msi,
        "headlines": all_headlines[:10]  # frontend expects this array
    }