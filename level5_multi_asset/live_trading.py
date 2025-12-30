from kiteconnect import KiteConnect
import pandas as pd
import time
from datetime import datetime, timedelta
import logging
import talib  # For technical indicators (install via pip if needed)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Kite credentials (replace with your own)
API_KEY = "your_api_key"
API_SECRET = "your_api_secret"
ACCESS_TOKEN = "your_access_token"  # Get this after login

kite = KiteConnect(api_key=API_KEY)
kite.set_access_token(ACCESS_TOKEN)

# Load instruments once at startup
instruments_df = pd.DataFrame(kite.instruments())
token_map = {}
for _, row in instruments_df.iterrows():
    key = f"{row['exchange']}:{row['tradingsymbol']}"
    token_map[key] = row['instrument_token']

# Instruments (updated for current Nifty expiry; adjust as needed)
INSTRUMENTS = {
    "RELIANCE": {"symbol": "RELIANCE", "exchange": "NSE", "type": "STOCK", "lot_size": 1, "strategy": "ORB_TREND"},
    "TCS": {"symbol": "TCS", "exchange": "NSE", "type": "STOCK", "lot_size": 1, "strategy": "ORB_TREND"},
    "NIFTY": {"symbol": "NIFTY25JANFUT", "exchange": "NFO", "type": "FUTURES", "lot_size": 50, "strategy": "ORB_MOMENTUM"},  # Update expiry as needed
    # Add more with strategies
}

# Capital and risk
CAPITAL = 200000
RISK_PCT = 0.0025

# Opening range times (IST)
OR_START = "09:15"
OR_END = "09:45"

# Store positions
positions = {}

def fetch_data(symbol, exchange, interval="day", days=30):
    key = f"{exchange}:{symbol}"
    token = token_map.get(key)
    if not token:
        logging.error(f"Instrument token not found for {key}")
        return pd.DataFrame()
    from_date = datetime.now() - timedelta(days=days)
    to_date = datetime.now()
    data = kite.historical_data(
        instrument_token=token,
        from_date=from_date,
        to_date=to_date,
        interval=interval
    )
    df = pd.DataFrame(data)
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        # Add indicators
        df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
    return df

def calculate_or_levels(data):
    or_start_time = pd.to_datetime(OR_START).time()
    or_end_time = pd.to_datetime(OR_END).time()
    or_data = data[(data['date'].dt.time >= or_start_time) & (data['date'].dt.time <= or_end_time)]
    if or_data.empty:
        return None, None
    or_high = or_data['high'].max()
    or_low = or_data['low'].min()
    return or_high, or_low

def check_signal(data, instrument):
    if data.empty or len(data) < 20:
        return None
    # Get previous day's high/low
    prev_high = data['high'].iloc[-2] if len(data) > 1 else None
    prev_low = data['low'].iloc[-2] if len(data) > 1 else None
    if prev_high is None or prev_low is None:
        return None
    current_price = data['close'].iloc[-1]
    ema = data['ema_20'].iloc[-1]
    rsi = data['rsi'].iloc[-1]
    atr = data['atr'].iloc[-1]
    volume = data['volume'].iloc[-1]
    avg_volume = data['volume'].mean()
    
    # Filters
    volume_ok = volume > 1.5 * avg_volume
    gap_buy = abs(current_price - prev_high) / current_price > 0.005
    gap_sell = abs(current_price - prev_low) / current_price > 0.005
    
    if current_price > prev_high and volume_ok and current_price > ema and rsi > 50 and gap_buy:
        return "BUY"
    elif current_price < prev_low and volume_ok and current_price < ema and rsi < 50 and gap_sell:
        return "SELL"
    return None

def place_order(symbol, exchange, direction, quantity, price, sl, target):
    try:
        # Place entry order
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange,
            tradingsymbol=symbol,
            transaction_type=direction,
            order_type=kite.ORDER_TYPE_LIMIT,
            quantity=quantity,
            price=price,
            product=kite.PRODUCT_MIS,
            trigger_price=0
        )
        # Place SL order (tighter: use ATR-based)
        kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange,
            tradingsymbol=symbol,
            transaction_type="SELL" if direction == "BUY" else "BUY",
            order_type=kite.ORDER_TYPE_SL,
            quantity=quantity,
            price=sl,
            trigger_price=sl,
            product=kite.PRODUCT_MIS
        )
        # Place target order (limit order for profit exit)
        kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange,
            tradingsymbol=symbol,
            transaction_type="SELL" if direction == "BUY" else "BUY",
            order_type=kite.ORDER_TYPE_LIMIT,
            quantity=quantity,
            price=target,
            product=kite.PRODUCT_MIS
        )
        logging.info(f"Orders placed: {direction} {quantity} {symbol} at {price}, SL: {sl}, Target: {target}")
        return order_id
    except Exception as e:
        logging.error(f"Order failed: {e}")

def run_live_trading():
    while True:
        for name, info in INSTRUMENTS.items():
            try:
                data = fetch_data(info["symbol"], info["exchange"])
                if data.empty:
                    continue
                # or_high, or_low = calculate_or_levels(data)
                signal = check_signal(data, info)
                if signal and name not in positions:
                    current_price = data['close'].iloc[-1]
                    atr = data['atr'].iloc[-1]
                    # No SL, wide SL for safety
                    sl = current_price * 0.9 if signal == "BUY" else current_price * 1.1
                    risk = abs(current_price - sl)
                    max_risk = CAPITAL * RISK_PCT
                    quantity = max(1, int(max_risk / risk))
                    target = current_price + (0.5 * atr) if signal == "BUY" else current_price - (0.5 * atr)
                    place_order(info["symbol"], info["exchange"], signal, quantity, current_price, sl, target)
                    positions[name] = {"direction": signal, "quantity": quantity}
            except Exception as e:
                logging.error(f"Error for {name}: {e}")
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    run_live_trading()