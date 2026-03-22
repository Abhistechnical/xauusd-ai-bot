import time
import schedule
import logging
from datetime import datetime

# Local Modules
from data import DataPipeline
from features import FeatureEngineer
from model import AIEngine
from signal_engine import SignalEngine
from risk import RiskManager
from execution import ExecutionEngine
from news import NewsFilter
from alerts import TelegramAlerts

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("MainBot")

# Instantiate Modules
dp = DataPipeline(symbol="XAUUSD", timeframe=15) # Assume MT5 TIMEFRAME_M15 constant is 15
model = AIEngine("model.joblib")
sig_engine = SignalEngine(confidence_threshold=0.60)
risk_mgr = RiskManager(risk_per_trade=0.01)
execution = ExecutionEngine(symbol="XAUUSD")
news = NewsFilter()
alerts = TelegramAlerts()

# Internal State tracker
is_trading = True
trades_today = 0
daily_pnl = 0.0

def run_trading_cycle():
    global trades_today, daily_pnl
    
    if not is_trading:
        return
        
    logger.info("--- Starting Trading Cycle ---")
    
    # 1. Update News and check Pause Window
    news.update_calendar()
    if not news.is_trading_allowed():
        logger.warning("Trading Paused: High Impact Events active.")
        return
        
    # 2. Extract MT5 live data
    if not dp.connect():
        logger.error("Failed to connect to MT5. Retrying next cycle.")
        return
        
    import MetaTrader5 as mt5
    
    # 3. Retrieve Account Risk Info
    account_info = mt5.account_info()
    if account_info is None:
        logger.error("Failed to fetch MT5 account info")
        dp.disconnect()
        return
        
    balance = account_info.balance
    
    if risk_mgr.check_daily_loss_limit(balance):
        alerts.send_message("🚨 *Trading Halted*: Max Daily Loss Limit Reached.")
        dp.disconnect()
        return
        
    # 4. Fetch 200 bars for EMA 200 calculation
    df_raw = dp.fetch_historical_data(250, tf=mt5.TIMEFRAME_M15)
    
    if df_raw is not None and not df_raw.empty:
        # 5. Build ML Features
        fe = FeatureEngineer(df_raw)
        df_features = fe.generate_all(training=False)
        
        # 6. Predict utilizing Pre-trained Model
        if model.load():
            ai_pred, proba = model.predict(df_features)
            
            # 7. Generate actionable market signals using Rules + AI Output
            final_signal = sig_engine.generate_signal(df_features, ai_pred, proba)
            logger.info(f"Generated Signal: {final_signal} | AI Probability: {proba:.2f}")
            
            # 8. Execute Trade on MT5
            if final_signal in ["BUY", "SELL"]:
                current_price = df_features['close'].iloc[-1]
                atr = df_features['atr_14'].iloc[-1]
                
                # Assume 1 pip = 0.01 points standard for XAUUSD (broker specific)
                sl_pips = (atr * risk_mgr.atr_multiplier_sl) / 0.01 
                lot_size = risk_mgr.calculate_position_size(balance, sl_pips, tick_value=1.0)
                
                sl_price, tp_price = risk_mgr.calculate_sl_tp(current_price, atr, final_signal)
                
                logger.info(f"Target Execution: {final_signal} | Lot: {lot_size} | Entry: {current_price} | SL: {sl_price} | TP: {tp_price}")
                
                res = execution.send_order(final_signal, lot_size, current_price, sl_price, tp_price)
                if res and res.retcode == mt5.TRADE_RETCODE_DONE:
                    trades_today += 1
                    alerts.send_trade_execution(final_signal, current_price, sl_price, tp_price, lot_size)
        else:
            logger.warning("AI Model not found (`model.joblib`). Skipping prediction. Please run `model.train()` offline first.")
            
    dp.disconnect()
    logger.info("--- Cycle Complete ---")

def daily_reset():
    global trades_today, daily_pnl
    logger.info("Executing Midnight Daily System Reset.")
    trades_today = 0
    daily_pnl = 0.0
    
    if dp.connect():
        import MetaTrader5 as mt5
        acc = mt5.account_info()
        if acc:
            risk_mgr.reset_daily_tracking(acc.balance)
            # Sends Telegram EOD summary automatically
            alerts.send_daily_summary(acc.balance, daily_pnl, trades_today)
        dp.disconnect()

def main():
    logger.info("XAUUSD fully-automated AI Bot initializing...")
    alerts.send_message("🚀 *XAUUSD AI Trading Bot instance started.*")
    
    # Establish initial day boundary sync
    daily_reset()
    
    # Schedule the core cycle every 15 minutes, aligning with the M15 timeframe targets.
    schedule.every(15).minutes.do(run_trading_cycle)
    
    # Reset daily
    schedule.every().day.at("00:00").do(daily_reset)
    
    logger.info("Starting schedule evaluation loop. (Ctrl+C to stop)")
    run_trading_cycle() # Run once immediately on boot
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received, shutting down gracefully...")
            break

if __name__ == "__main__":
    main()
