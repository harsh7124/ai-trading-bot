getting ths error.Fix this
# AI Trading Bot

An automated multi-asset trading bot using daily gap-based Opening Range Breakout (ORB) strategy with trend and momentum filters. Supports backtesting on historical data and live trading via Kite/Zerodha API.

## Features
- **Strategy**: Daily ORB with previous day's high/low, EMA trend, RSI momentum, volume, and gap filters.
- **Backtesting**: Test on 2020-2024 data with ~65% win rate.
- **Live Trading**: Execute trades in real-time using Kite API.
- **Risk Management**: 0.25% risk per trade, ATR-based targets, max hold 10 days.

## Setup

1. Clone the repo: `git clone <repo-url>`
2. Create virtual environment: `python -m venv .venv`
3. Activate: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`

## Backtesting

Run: `python -m level5_multi_asset.main`

## Live Trading

1. Update `level5_multi_asset/live_trading.py` with your Kite API credentials.
2. Run: `python level5_multi_asset/live_trading.py`

## Requirements

- Python 3.8+
- Kite API for live trading
- yfinance for data

## Disclaimer

This is for educational purposes. Trading involves risk; use at your own discretion.