import logging
import MetaTrader5 as mt5

from data import DataPipeline
from features import FeatureEngineer
from model import AIEngine
from risk import RiskManager
from execution import ExecutionEngine

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("InstantStrategy")

def run_instant_analysis():
    logger.info("Initializing Instant AI Analysis & Execution...")
    
    dp = DataPipeline("XAUUSD", mt5.TIMEFRAME_M15)
    if not dp.connect():
        logger.error("Failed to connect to MT5.")
        return
        
    df_raw = dp.fetch_historical_data(250, tf=mt5.TIMEFRAME_M15)
    if df_raw is None or df_raw.empty:
        logger.error("Failed to fetch historical data.")
        dp.disconnect()
        return

    logger.info("Generating Machine Learning Features & Tech Indicators...")
    fe = FeatureEngineer(df_raw)
    df_features = fe.generate_all(training=False)
    
    logger.info("Evaluating AI RandomForest Engine...")
    model = AIEngine("model.joblib")
    if not model.load():
        logger.error("AI Model not found.")
        dp.disconnect()
        return
        
    ai_pred, proba = model.predict(df_features)
    logger.info(f"AI Matrix Class Prediction: {ai_pred} | Probability: {proba*100:.2f}%")
    
    direction = "BUY" if ai_pred == 1 else "SELL" if ai_pred == -1 else None
    
    if direction is None:
        ema_50 = df_features['ema_50'].iloc[-1]
        ema_200 = df_features['ema_200'].iloc[-1]
        direction = "BUY" if ema_50 > ema_200 else "SELL"
        logger.warning(f"AI Matrix predicts HOLD (0). Falling back to pure optimal EMA trend: {direction}")
    
    logger.info(f"Strategy strictly decides to {direction}!")
    
    risk_mgr = RiskManager()
    current_price = df_features['close'].iloc[-1]
    
    lot_size = risk_mgr.fixed_lot_size
    sl, tp = risk_mgr.calculate_sl_tp(current_price, signal_type=direction)
    
    logger.info(f"Executing {direction} | Lot: {lot_size} | Entry: {current_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
    
    exe = ExecutionEngine(symbol="XAUUSD")
    res = exe.send_order(direction, lot_size, current_price, sl, tp, comment="Instant_UI_Strategy")
    
    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info(f"SUCCESS! Strategy Order deployed. Ticket ID: {res.order}")
    else:
        logger.error(f"Execution failed. MT5 Retcode: {res.retcode if res else 'Unknown'}")
        
    dp.disconnect()

if __name__ == "__main__":
    run_instant_analysis()
