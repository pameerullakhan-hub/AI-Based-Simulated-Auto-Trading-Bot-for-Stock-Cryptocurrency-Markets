import requests
import yfinance as yf

INDIAN_STOCKS = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS"]

def get_crypto_prices():
    results = []
    symbols = [("BTC/USDT", "BTC-USD"), ("ETH/USDT", "ETH-USD")]
    for pair, display in symbols:
        try:
            url = f"https://testnet.binance.vision/api/v3/ticker/24hr?symbol={pair.replace('/', '')}"
            r = requests.get(url, timeout=5)
            data = r.json()
            price = round(float(data['lastPrice']), 2)
            change_pct = round(float(data['priceChangePercent']), 2)
            results.append({
                "symbol": display,
                "price": price,
                "change_pct": change_pct
            })
        except Exception as e:
            print(f"Crypto error {pair}: {e}")
            results.append({
                "symbol": display,
                "price": 0.0,
                "change_pct": 0.0
            })
    return results

def get_indian_stock_prices():
    results = []
    for symbol in INDIAN_STOCKS:
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.fast_info
            price = round(data.last_price, 2)
            prev = round(data.previous_close, 2)
            change_pct = round(((price - prev) / prev) * 100, 2)
            results.append({
                "symbol": symbol.replace(".NS", ""),
                "price": price,
                "change_pct": change_pct
            })
        except Exception as e:
            print(f"Stock error {symbol}: {e}")
            results.append({
                "symbol": symbol.replace(".NS", ""),
                "price": 0.0,
                "change_pct": 0.0
            })
    return results

def get_all_prices():
    crypto = get_crypto_prices()
    stocks = get_indian_stock_prices()
    return crypto + stocks