import numpy as np
import pandas as pd
import yfinance as yf
import ccxt

def fetch_stock_data(symbol: str, period: str = "6mo", interval: str = "1d"):
    ticker = yf.Ticker(f"{symbol}.NS")
    df = ticker.history(period=period, interval=interval)
    df.dropna(inplace=True)
    return df

def fetch_crypto_data(symbol: str, timeframe: str = "1d", limit: int = 180):
    # Use real Binance public API for historical data (no auth needed)
    exchange = ccxt.binance({
        'enableRateLimit': True,
    })
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    return df

def compute_kama(close: pd.Series, n: int = 10, fast: int = 2, slow: int = 30):
    f = 2 / (fast + 1)
    s = 2 / (slow + 1)
    
    kama = np.zeros(len(close))
    kama[n] = close.iloc[n]
    
    for i in range(n + 1, len(close)):
        direction = abs(close.iloc[i] - close.iloc[i - n])
        volatility = sum(abs(close.iloc[j] - close.iloc[j - 1]) for j in range(i - n + 1, i + 1))
        
        er = direction / volatility if volatility != 0 else 0
        alpha = (er * (f - s) + s) ** 2
        kama[i] = kama[i - 1] + alpha * (close.iloc[i] - kama[i - 1])
    
    return pd.Series(kama, index=close.index)

def generate_signals(df: pd.DataFrame):
    close = df['Close'] if 'Close' in df.columns else df['close']
    kama = compute_kama(close)
    
    signals = []
    for i in range(1, len(close)):
        kama_slope = kama.iloc[i] - kama.iloc[i - 1]
        price = close.iloc[i]
        kama_val = kama.iloc[i]

        if kama_val == 0:
            signal = "HOLD"
        elif price > kama_val and kama_slope > 0:
            signal = "BUY"
        elif price < kama_val and kama_slope < 0:
            signal = "SELL"
        else:
            signal = "HOLD"

        signals.append({
            "date": str(close.index[i].date() if hasattr(close.index[i], 'date') else close.index[i]),
            "price": round(float(price), 2),
            "kama": round(float(kama_val), 2),
            "signal": signal
        })
    
    return signals

def get_kama_signal(symbol: str, is_crypto: bool = False):
    try:
        if is_crypto:
            # Convert BTCUSDT → BTC/USDT for ccxt
            if "/" not in symbol:
                symbol_ccxt = symbol[:-4] + "/" + symbol[-4:]  # BTCUSDT → BTC/USDT
            else:
                symbol_ccxt = symbol
            df = fetch_crypto_data(symbol_ccxt)
        else:
            df = fetch_stock_data(symbol)
        
        signals = generate_signals(df)
        latest = signals[-1] if signals else {"signal": "HOLD", "price": 0, "kama": 0}
        
        return {
            "symbol": symbol,
            "latest_signal": latest["signal"],
            "latest_price": latest["price"],
            "latest_kama": latest["kama"],
            "history": signals[-30:]
        }
    except Exception as e:
        print(f"KAMA error for {symbol}: {e}")
        return {
            "symbol": symbol,
            "latest_signal": "HOLD",
            "latest_price": 0,
            "latest_kama": 0,
            "history": []
        }