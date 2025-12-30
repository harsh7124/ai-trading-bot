from .trade import Trade
from .pnl_engine import PnLEngine
import pandas_ta as ta

def calculate_lot_size(instrument, capital, risk_pct=0.005, entry_price=0, sl=0):
    """Calculate dynamic lot size based on risk"""
    if entry_price > 0 and sl > 0:
        risk_per_unit = abs(entry_price - sl)
        max_risk = capital * risk_pct
        if risk_per_unit > 0:
            calculated_lot = max_risk / risk_per_unit
            return max(1, int(calculated_lot))  # At least 1
    return instrument["lot_size"]

def backtest_orb(data, instrument, skip_time="09:30", paper_trading=True):
    pnl_engine = PnLEngine()
    in_trade = False
    current_trade = None

    lot_size = calculate_lot_size(instrument, pnl_engine.current_capital, risk_pct=0.0025)

    # Calculate indicators
    atr = ta.atr(data['High'], data['Low'], data['Close'], length=14)
    ema = ta.ema(data['Close'], length=20)
    rsi = ta.rsi(data['Close'], length=14)
    macd, macdsignal, macdhist = ta.macd(data['Close'])
    atr_threshold = data['Close'].mean() * 0.001  # 0.1% of average price
    avg_volume = data['Volume'].mean()
    max_hold_days = 10

    for time, row in data.iterrows():
        if time.strftime("%H:%M") <= skip_time:
            continue

        close_price = row["Close"]
        volume = row["Volume"]

        prev_high = data['High'].shift(1).loc[time] if time != data.index[0] else None
        prev_low = data['Low'].shift(1).loc[time] if time != data.index[0] else None

        if not in_trade and prev_high is not None and prev_low is not None:
            current_atr = atr.loc[time] if time in atr.index else 0.01  # default small
            current_ema = ema.loc[time] if time in ema.index else close_price
            current_rsi = rsi.loc[time] if time in rsi.index else 50
            volume_ok = volume > 1.5 * avg_volume
            if close_price > prev_high and volume_ok and close_price > current_ema and current_rsi > 50 and abs(close_price - prev_high) / close_price > 0.005:
                entry = close_price
                current_atr = atr.loc[time] if time in atr.index else 0.01
                sl = entry * 0.995
                target = entry + 0.5 * current_atr  # ATR-based target
                current_trade = Trade(time, entry, "BUY", lot_size, sl, target)
                current_trade.apply_slippage_brokerage()
                in_trade = True
            elif close_price < prev_low and volume_ok and close_price < current_ema and current_rsi < 50 and abs(close_price - prev_low) / close_price > 0.005:
                entry = close_price
                current_atr = atr.loc[time] if time in atr.index else 0.01
                sl = entry * 1.005
                target = entry - 0.5 * current_atr  # ATR-based target
                current_trade = Trade(time, entry, "SELL", lot_size, sl, target)
                current_trade.apply_slippage_brokerage()
                in_trade = True

        if in_trade:
            # Trailing stop to lock profits
            if current_trade.direction == "BUY":
                profit = close_price - current_trade.entry_price
                if profit >= 0.5 * current_trade.risk:
                    current_trade.sl = max(current_trade.sl, current_trade.entry_price)
                # No SL exit, only target or end
                if row["High"] >= current_trade.target:
                    current_trade.close_trade(time, current_trade.target, "target")
                    pnl_engine.add_trade(current_trade)
                    in_trade = False
            elif current_trade.direction == "SELL":
                profit = current_trade.entry_price - close_price
                if profit >= 0.5 * current_trade.risk:
                    current_trade.sl = min(current_trade.sl, current_trade.entry_price)
                # No SL exit, only target or end
                if row["Low"] <= current_trade.target:
                    current_trade.close_trade(time, current_trade.target, "target")
                    pnl_engine.add_trade(current_trade)
                    in_trade = False

        if in_trade and (time - current_trade.entry_time).days > max_hold_days:
            current_trade.close_trade(time, close_price, "max_hold")
            pnl_engine.add_trade(current_trade)
            in_trade = False

    # If still in trade at end, close at last price
    if in_trade:
        current_trade.close_trade(data.index[-1], data.iloc[-1]["Close"], "end")
        pnl_engine.add_trade(current_trade)

    return pnl_engine
