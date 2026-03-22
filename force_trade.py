import sys
import logging
import MetaTrader5 as mt5
from execution import ExecutionEngine

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
    logger = logging.getLogger("ForceTrade")
    
    # Defaults to BUY if no argument is provided
    trade_type = "BUY"
    if len(sys.argv) > 1:
        trade_type = sys.argv[1].upper()
        if trade_type not in ["BUY", "SELL"]:
            logger.error("Usage: python force_trade.py [BUY|SELL]")
            exit(1)

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
        
    current_price = tick.ask if trade_type == "BUY" else tick.bid
    
    # Configure user requested fixed parameters
    lot_size = 0.10
    sl_dist = 10.0
    tp_dist = 20.0
    
    if trade_type == "BUY":
        sl = current_price - sl_dist
        tp = current_price + tp_dist
    else:
        sl = current_price + sl_dist
        tp = current_price - tp_dist
    
    logger.info(f"Targeting {trade_type} {lot_size} lot {symbol} at {current_price:.2f} | SL: {sl:.2f} | TP: {tp:.2f}")
    
    exe = ExecutionEngine(symbol=symbol)
    res = exe.send_order(trade_type, lot_size, current_price, sl, tp, comment="Manual_Force_Trade")
    
    if res and res.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info(f"SUCCESS! Trade opened safely. Ticket ID: {res.order}")
    else:
        logger.error(f"Trade failed. Retcode: {res.retcode if res else 'Unknown'}")
        
    mt5.shutdown()
