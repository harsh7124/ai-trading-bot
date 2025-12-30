class Trade:
    def __init__(self, entry_time, entry_price, direction, lot_size, sl, target, brokerage=0, slippage=0):
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction  # "BUY" or "SELL"
        self.lot_size = lot_size
        self.sl = sl
        self.target = target
        self.risk = abs(entry_price - sl)  # Add risk calculation
        self.brokerage = brokerage  # percentage
        self.slippage = slippage  # percentage
        self.exit_time = None
        self.exit_price = None
        self.pnl = 0
        self.brokerage_cost = 0
        self.slippage_cost = 0

    def apply_slippage_brokerage(self):
        # Apply slippage to entry
        if self.direction == "BUY":
            self.entry_price *= (1 + self.slippage)
        else:
            self.entry_price *= (1 - self.slippage)
        # Brokerage on entry
        self.brokerage_cost += abs(self.entry_price * self.lot_size * self.brokerage)

    def close_trade(self, exit_time, exit_price, reason="target"):
        self.exit_time = exit_time
        # Apply slippage to exit
        if self.direction == "BUY":
            self.exit_price = exit_price * (1 - self.slippage)
        else:
            self.exit_price = exit_price * (1 + self.slippage)
        # Brokerage on exit
        self.brokerage_cost += abs(self.exit_price * self.lot_size * self.brokerage)
        # Calculate PnL
        if self.direction == "BUY":
            self.pnl = (self.exit_price - self.entry_price) * self.lot_size
        else:
            self.pnl = (self.entry_price - self.exit_price) * self.lot_size
        self.pnl -= self.brokerage_cost

    def __str__(self):
        return f"Trade({self.direction}, Entry: {self.entry_price:.2f} at {self.entry_time}, Exit: {self.exit_price:.2f} at {self.exit_time}, PnL: {self.pnl:.2f})"