import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, risk_per_trade=0.01, max_daily_loss=0.03, atr_multiplier_sl=2.0, atr_multiplier_tp=4.0):
        self.risk_per_trade = risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.atr_multiplier_sl = atr_multiplier_sl  # Kept for compatibility with main.py
        self.atr_multiplier_tp = atr_multiplier_tp
        
        # Hardcoded constraints imposed by user
        self.fixed_lot_size = 0.10
        self.fixed_sl_dist = 10.0
        self.fixed_tp_dist = 20.0
        
        # Track daily metrics
        self.daily_start_balance = None
        
    def calculate_position_size(self, balance, stop_loss_pips=None, tick_value=1.0):
        """
        Calculates the lot size.
        Using the fixed static lot size of 0.10.
        """
        return self.fixed_lot_size
        
    def calculate_sl_tp(self, current_price, atr_value=None, signal_type=None):
        """
        Calculates exact absolute price levels for SL and TP based on fixed distances.
        SL = $10.00
        TP = $20.00
        """
        if signal_type == "BUY":
            sl_price = current_price - self.fixed_sl_dist
            tp_price = current_price + self.fixed_tp_dist
        elif signal_type == "SELL":
            sl_price = current_price + self.fixed_sl_dist
            tp_price = current_price - self.fixed_tp_dist
        else:
            return 0.0, 0.0
            
        return round(sl_price, 2), round(tp_price, 2)
        
    def check_daily_loss_limit(self, current_balance):
        if self.daily_start_balance is None:
            self.daily_start_balance = current_balance
            
        if self.daily_start_balance <= 0.0:
            return False
            
        loss_pct = (self.daily_start_balance - current_balance) / self.daily_start_balance
        
        if loss_pct >= self.max_daily_loss:
            logger.warning(f"MAX DAILY LOSS LIMIT REACHED ({loss_pct:.2%}). Halting trading.")
            return True
        return False
        
    def reset_daily_tracking(self, current_balance):
        self.daily_start_balance = current_balance
        logger.info(f"Daily Risk Tracker reset. Starting Balance: {self.daily_start_balance}")
