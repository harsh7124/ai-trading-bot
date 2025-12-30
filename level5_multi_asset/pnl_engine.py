from .trade import Trade

class PnLEngine:
    def __init__(self, initial_capital=200000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.total_pnl = 0

    def add_trade(self, trade):
        self.trades.append(trade)
        self.total_pnl += trade.pnl
        self.current_capital += trade.pnl

    def get_total_pnl(self):
        return self.total_pnl

    def get_current_capital(self):
        return self.current_capital

    def get_trade_summary(self):
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(self.trades) if self.trades else 0,
            "total_pnl": self.total_pnl,
            "max_drawdown": min([self.current_capital - self.initial_capital for _ in self.trades] or [0])  # simplified
        }