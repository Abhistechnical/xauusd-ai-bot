import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, risk_per_trade=0.01, max_daily_loss=0.03, atr_multiplier_sl=2.0, atr_multiplier_tp=4.0):
        self.risk_per_trade = risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.atr_multiplier_sl = atr_multiplier_sl
        self.atr_multiplier_tp = atr_multiplier_tp
        
        # Track daily metrics
        self.daily_start_balance = None
        
    def calculate_position_size(self, balance, stop_loss_pips, tick_value=1.0):
        """
        Calculates the lot size based on balance and stop loss distance.
        XAUUSD pips are often 0.1 or 0.01 depending on broker.
        We assume standard lot size modeling using standard tick mapping.
        """
        if stop_loss_pips <= 0:
            return 0.01
            
        risk_amount = balance * self.risk_per_trade
        
        # Basic formula, lot size = risk / (points * tick_value_per_point).
        # We assume for Gold typical standard logic, but returning nominal bounds
        lot_size = risk_amount / (stop_loss_pips * tick_value)
        
        # Clamp to reasonable values for Gold depending on broker (Standard bounds: 0.01 min, let's say 10 max safely)
        return round(max(0.01, min(lot_size, 10.0)), 2)
        
    def calculate_sl_tp(self, current_price, atr_value, signal_type):
        """Calculates exact absolute price levels for SL and TP based on ATR."""
        if atr_value is None or atr_value == 0:
            atr_value = 2.0 # Fallback for XAUUSD avg volatility
            
        sl_dist = atr_value * self.atr_multiplier_sl
        tp_dist = atr_value * self.atr_multiplier_tp
        
        if signal_type == "BUY":
            sl_price = current_price - sl_dist
            tp_price = current_price + tp_dist
        elif signal_type == "SELL":
            sl_price = current_price + sl_dist
            tp_price = current_price - tp_dist
        else:
            return 0.0, 0.0
            
        return round(sl_price, 2), round(tp_price, 2)
        
    def check_daily_loss_limit(self, current_balance):
        """Checks if the daily loss limit has been hit."""
        if self.daily_start_balance is None:
            self.daily_start_balance = current_balance
            
        if self.daily_start_balance <= 0.0:
            return False # Avoid div by zero
            
        loss_pct = (self.daily_start_balance - current_balance) / self.daily_start_balance
        
        if loss_pct >= self.max_daily_loss:
            logger.warning(f"MAX DAILY LOSS LIMIT REACHED ({loss_pct:.2%}). Halting trading.")
            return True
        return False
        
    def reset_daily_tracking(self, current_balance):
        """Resets the beginning balance, usually called at 00:00 server time."""
        self.daily_start_balance = current_balance
        logger.info(f"Daily Risk Tracker reset. Starting Balance: {self.daily_start_balance}")
