import MetaTrader5 as mt5
import logging
import time

logger = logging.getLogger(__name__)

class ExecutionEngine:
    def __init__(self, symbol="XAUUSD", magic_number=1337, deviation=20):
        self.symbol = symbol
        self.magic_number = magic_number
        self.deviation = deviation
        
    def send_order(self, order_type, lot_size, price, sl, tp, comment="AI_Bot"):
        """Sends an order to MT5 with retries."""
        if order_type == "BUY":
            mt5_order_type = mt5.ORDER_TYPE_BUY
        elif order_type == "SELL":
            mt5_order_type = mt5.ORDER_TYPE_SELL
        else:
            logger.error(f"Invalid order type: {order_type}")
            return None
            
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": float(lot_size),
            "type": mt5_order_type,
            "price": float(price),
            "sl": float(sl),
            "tp": float(tp),
            "deviation": self.deviation,
            "magic": self.magic_number,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Retry mechanism for failed connections/requotes
        max_retries = 3
        for attempt in range(max_retries):
            result = mt5.order_send(request)
            if result is None:
                logger.error(f"Order Send completely null. Last error: {mt5.last_error()}")
                return None
                
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order send failed. Retcode: {result.retcode}. Attempt {attempt+1}/{max_retries}")
                time.sleep(1.0)
            else:
                logger.info(f"Order successfully placed! Ticket: {result.order}")
                return result
                
        logger.error("Order completely failed after retries.")
        return None

    def close_all_positions(self):
        """Emergency function to close all open positions for the active symbol."""
        positions = mt5.positions_get(symbol=self.symbol)
        if positions is None or len(positions) == 0:
            return
            
        for pos in positions:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick is None:
                continue
                
            order_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = tick.bid if order_type == mt5.ORDER_TYPE_SELL else tick.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": pos.volume,
                "type": order_type,
                "position": pos.ticket,
                "price": price,
                "deviation": self.deviation,
                "magic": self.magic_number,
                "comment": "Emergency Algo Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            res = mt5.order_send(request)
            if res.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Failed to close position {pos.ticket}. Error: {res.retcode}")
            else:
                logger.info(f"Successfully closed position {pos.ticket}")
