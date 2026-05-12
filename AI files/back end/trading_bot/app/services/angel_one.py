import pyotp
import requests
import json
from app.core.config import (
    ANGEL_ONE_API_KEY,
    ANGEL_ONE_CLIENT_ID,
    ANGEL_ONE_PASSWORD,
    ANGEL_ONE_TOTP
)

BASE_URL = "https://apiconnect.angelbroking.com"
auth_token = None
refresh_token = None

def get_totp():
    totp = pyotp.TOTP(ANGEL_ONE_TOTP)
    return totp.now()

def connect_angel_one():
    global auth_token, refresh_token
    try:
        totp = get_totp()
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "127.0.0.1",
            "X-MACAddress": "00:00:00:00:00:00",
            "X-PrivateKey": ANGEL_ONE_API_KEY
        }
        payload = {
            "clientcode": ANGEL_ONE_CLIENT_ID,
            "password": ANGEL_ONE_PASSWORD,
            "totp": totp
        }
        res = requests.post(
            f"{BASE_URL}/rest/auth/angelbroking/user/v1/loginByPassword",
            headers=headers,
            json=payload,
            timeout=10
        )
        data = res.json()
        if data.get("status"):
            auth_token = data["data"]["jwtToken"]
            refresh_token = data["data"]["refreshToken"]
            print(f"✅ Angel One connected! Client: {ANGEL_ONE_CLIENT_ID}")
            return True
        else:
            print(f"❌ Angel One login failed: {data}")
            return False
    except Exception as e:
        print(f"❌ Angel One connection error: {e}")
        return False

def get_headers():
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
        "X-ClientLocalIP": "127.0.0.1",
        "X-ClientPublicIP": "127.0.0.1",
        "X-MACAddress": "00:00:00:00:00:00",
        "X-PrivateKey": ANGEL_ONE_API_KEY,
        "Authorization": f"Bearer {auth_token}"
    }

def get_stock_price(symbol: str):
    try:
        if not auth_token:
            connect_angel_one()
        token_map = {
            "RELIANCE": "2885",
            "TCS": "11536",
            "INFY": "1594",
            "HDFCBANK": "1333",
        }
        token = token_map.get(symbol)
        if not token:
            return None
        payload = {
            "exchange": "NSE",
            "tradingsymbol": symbol + "-EQ",
            "symboltoken": token
        }
        res = requests.post(
            f"{BASE_URL}/rest/secure/angelbroking/market/v1/getLTPData",
            headers=get_headers(),
            json=payload,
            timeout=10
        )
        data = res.json()
        if data.get("status"):
            return data["data"]["ltp"]
        return None
    except Exception as e:
        print(f"Angel One price error: {e}")
        return None

def place_paper_order(symbol: str, side: str, quantity: int):
    try:
        if not auth_token:
            connect_angel_one()
        token_map = {
            "RELIANCE": "2885",
            "TCS": "11536",
            "INFY": "1594",
            "HDFCBANK": "1333",
        }
        token = token_map.get(symbol)
        if not token:
            return None
        price = get_stock_price(symbol)
        payload = {
            "variety": "NORMAL",
            "tradingsymbol": symbol + "-EQ",
            "symboltoken": token,
            "transactiontype": side,
            "exchange": "NSE",
            "ordertype": "MARKET",
            "producttype": "INTRADAY",
            "duration": "DAY",
            "quantity": str(quantity),
            "price": "0",
            "squareoff": "0",
            "stoploss": "0"
        }
        res = requests.post(
            f"{BASE_URL}/rest/secure/angelbroking/order/v1/placeOrder",
            headers=get_headers(),
            json=payload,
            timeout=10
        )
        data = res.json()
        if data.get("status"):
            print(f"✅ Angel One order: {side} {quantity} {symbol} @ ₹{price}")
            return {
                "order_id": data["data"]["orderid"],
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "price": price
            }
        else:
            print(f"❌ Order failed: {data}")
            return None
    except Exception as e:
        print(f"❌ Angel One order error: {e}")
        return None