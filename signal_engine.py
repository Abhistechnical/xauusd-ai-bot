import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SignalEngine:
    def __init__(self, confidence_threshold=0.55):
        self.confidence_threshold = confidence_threshold
        
    def generate_signal(self, current_data: pd.DataFrame, ai_prediction: float, ai_proba: float):
        """
        Combines AI prediction with rule-based confirmations.
        ai_prediction: 1 (Buy), -1 (Sell), 0 (Hold)
        Returns: "BUY", "SELL", or "HOLD"
        """
        if current_data is None or current_data.empty:
            return "HOLD"
            
        # Get latest data row
        latest = current_data.iloc[-1]
        
        # Rule 1: Confidence Threshold
        if ai_proba < self.confidence_threshold:
            logger.info(f"Signal HOLD: AI Probability {ai_proba:.2f} is below threshold {self.confidence_threshold}")
            return "HOLD"
            
        # Rule 2: Trend Alignment (EMA 50 vs EMA 200)
        # Professional traders usually only buy when EMAs align bullish, sell when bearish
        ema_50 = latest.get('ema_50', 0)
        ema_200 = latest.get('ema_200', 0)
        
        if ai_prediction == 1:
            if ema_50 > ema_200:
                return "BUY"
            else:
                logger.info("Signal HOLD: AI signals BUY, but counter-trend (EMA50 <= EMA200)")
                return "HOLD"
                
        elif ai_prediction == -1:
            if ema_50 < ema_200:
                return "SELL"
            else:
                logger.info("Signal HOLD: AI signals SELL, but counter-trend (EMA50 >= EMA200)")
                return "HOLD"
                
        return "HOLD"
