import logging
import MetaTrader5 as mt5
from execution import ExecutionEngine

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger("ForceTrade")

    if not mt5.initialize():
        logger.error("Failed to connect to MT5.")
        exit(1)
        
    symbol = "XAUUSD"
    if not mt5.symbol_select(symbol, True):
        mt5.shutdown()
        exit(1)
        
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        mt5.shutdown()
        exit(1)
        
    current_price = tick.ask
    
    # Larger trade config: 0.10 Lot Buy with wider targets
    sl = current_price - 5.0
    tp = current_price + 10.0
    
    logger.info(f"Targeting Aggressive BUY 0.10 lot {symbol} at {current_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
    
    exe = ExecutionEngine(symbol=symbol)
    res = exe.send_order("BUY", 0.10, current_price, sl, tp, comment="Demo_Force_Trade_Recovery")
    
    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info(f"SUCCESS! Trade boldly opened. Ticket ID: {res.order}")
    else:
        logger.error(f"Trade failed. Retcode: {res.retcode if res else 'Unknown'}")
        
    mt5.shutdown()
