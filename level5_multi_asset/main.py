from .market_data import fetch_data
from .backtest_engine import backtest_orb
from .instruments import INSTRUMENTS


results = {}

for name, info in INSTRUMENTS.items():
    print(f"\nBacktesting {name}")

    data = fetch_data(info)
    
    if data.empty:
        print(f"No data fetched for {name}")
        continue

    skip_time = "-1:00"
    pnl_engine = backtest_orb(
        data,
        info,
        skip_time
    )

    results[name] = pnl_engine.get_total_pnl()
    print(f"PnL: {pnl_engine.get_total_pnl():.2f}")
    print(f"Trades: {len(pnl_engine.trades)}")
    for trade in pnl_engine.trades:
        print(f"  {trade}")

total_pnl = sum(results.values())
print(f"Total PnL: {total_pnl:.2f}")

print("\nFinal Results:", results)
