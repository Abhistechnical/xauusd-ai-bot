import pandas as pd
import numpy as np
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, initial_balance=10000.0, risk_per_trade=0.01):
        self.initial_balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.balance = initial_balance
        self.equity_curve = []
        self.trades = []
        
    def run(self, df: pd.DataFrame, signals: pd.Series):
        """
        Runs a bar-by-bar backtest using standard SL and TP rules.
        signals: Series with 1 (Buy), -1 (Sell), 0 (Hold).
        Assumes dataframe has 'open', 'high', 'low', 'close', 'atr_14'.
        """
        self.balance = self.initial_balance
        self.equity_curve = [self.balance]
        self.trades = []
        
        in_position = False
        entry_price = 0.0
        sl_price = 0.0
        tp_price = 0.0
        position_type = 0 # 1 for Long, -1 for Short
        
        # We start loop from index 1.
        for i in range(1, len(df)):
            current_bar = df.iloc[i]
            prev_signal = signals.iloc[i-1] # Signal generated at close of prev bar
            
            # Check if active position hits SL or TP
            if in_position:
                low, high = current_bar['low'], current_bar['high']
                closed = False
                pnl = 0.0
                
                if position_type == 1:
                    if low <= sl_price:
                        pnl = - (self.balance * self.risk_per_trade)
                        closed = True
                    elif high >= tp_price:
                        pnl = (self.balance * self.risk_per_trade) * 2.0 # 1:2 RR
                        closed = True
                elif position_type == -1:
                    if high >= sl_price:
                        pnl = - (self.balance * self.risk_per_trade)
                        closed = True
                    elif low <= tp_price:
                        pnl = (self.balance * self.risk_per_trade) * 2.0 # 1:2 RR
                        closed = True
                        
                if closed:
                    self.balance += pnl
                    self.trades.append({'time': df.index[i], 'type': position_type, 'pnl': pnl})
                    in_position = False
            
            # Open new positions if not in position
            if not in_position and prev_signal != 0:
                in_position = True
                position_type = prev_signal
                entry_price = current_bar['open'] # Enter at open of current bar
                
                # Assume ATR from previous bar for SL/TP calc
                atr = df.iloc[i-1].get('atr_14', 2.0)
                if pd.isna(atr) or atr == 0:
                    atr = 2.0
                    
                sl_dist = atr * 2.0
                tp_dist = atr * 4.0
                
                if position_type == 1:
                    sl_price = entry_price - sl_dist
                    tp_price = entry_price + tp_dist
                else:
                    sl_price = entry_price + sl_dist
                    tp_price = entry_price - tp_dist
                    
            self.equity_curve.append(self.balance)
            
        return self.get_metrics()
        
    def get_metrics(self) -> Dict[str, Any]:
        total_trades = len(self.trades)
        
        if total_trades == 0:
            return {"total_trades": 0, "net_profit": 0, "win_rate": 0, "max_drawdown": 0, "final_balance": self.initial_balance}
            
        trades_df = pd.DataFrame(self.trades)
        wins = len(trades_df[trades_df['pnl'] > 0])
        win_rate = wins / total_trades
        net_profit = self.balance - self.initial_balance
        
        # Max Drawdown
        equity_series = pd.Series(self.equity_curve)
        peak = equity_series.expanding(min_periods=1).max()
        drawdown = (equity_series - peak) / peak
        max_drawdown = drawdown.min()
        
        return {
            "total_trades": total_trades,
            "net_profit": net_profit,
            "win_rate": win_rate,
            "max_drawdown": abs(max_drawdown),
            "final_balance": self.balance
        }
