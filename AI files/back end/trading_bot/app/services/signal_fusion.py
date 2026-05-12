from app.services.kama import get_kama_signal
from app.services.finbert import get_market_sentiment

TAU = 0.1  # Sentiment threshold from the paper

def fuse_signals(symbol: str, is_crypto: bool = False):
    # Get KAMA signal
    kama_data = get_kama_signal(symbol, is_crypto)
    kama_signal = kama_data["latest_signal"]
    
    # Get FinBERT sentiment
    query = symbol.replace("USDT", "").replace("USD", "")
    sentiment_data = get_market_sentiment(query)
    msi = sentiment_data["msi"]
    
    # Signal Fusion Logic (Equation 7 from the paper)
    if kama_signal == "BUY" and msi >= TAU:
        decision = "BUY"
        reason = f"KAMA bullish + positive sentiment (MSI: {msi:.3f})"
        confidence = round(((msi + 1) / 2) * 100, 1)
    elif kama_signal == "SELL" or msi < -TAU:
        decision = "SELL"
        reason = f"KAMA bearish or negative sentiment (MSI: {msi:.3f})"
        confidence = round(((1 - msi) / 2) * 100, 1)
    else:
        decision = "HOLD"
        reason = f"Insufficient signal strength (MSI: {msi:.3f})"
        confidence = round(50 - abs(msi) * 50, 1)

    return {
        "symbol": symbol,
        "decision": decision,
        "confidence": confidence,
        "reason": reason,
        "kama_signal": kama_signal,
        "kama_price": kama_data["latest_price"],
        "kama_value": kama_data["latest_kama"],
        "msi": msi,
        "sentiment_signal": sentiment_data["signal"],
        "headlines": sentiment_data["headlines"][:5]
    }

def fuse_all_signals():
    assets = [
        {"symbol": "RELIANCE", "is_crypto": False},
        {"symbol": "TCS", "is_crypto": False},
        {"symbol": "INFY", "is_crypto": False},
        {"symbol": "HDFCBANK", "is_crypto": False},
        {"symbol": "BTCUSDT", "is_crypto": True},
        {"symbol": "ETHUSDT", "is_crypto": True},
    ]
    
    results = []
    for asset in assets:
        try:
            result = fuse_signals(asset["symbol"], asset["is_crypto"])
            results.append(result)
        except Exception as e:
            print(f"Fusion error for {asset['symbol']}: {e}")
    
    return results 
