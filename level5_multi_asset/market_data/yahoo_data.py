import yfinance as yf
import pandas as pd

def fetch_yahoo_data(symbol, interval="1d", period=None):
    try:
        ticker = f"{symbol}.NS" if not symbol.startswith("^") else symbol
        data = yf.download(
            ticker,
            start="2024-01-01",
            end="2024-12-31",
            interval=interval,
            progress=False
        )
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)
        return data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()  # Return empty DataFrame on error
