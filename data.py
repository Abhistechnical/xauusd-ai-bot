import MetaTrader5 as mt5
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, symbol="XAUUSD", timeframe=mt5.TIMEFRAME_M15):
        self.symbol = symbol
        self.timeframe = timeframe

    def connect(self):
        """Connects to the MetaTrader 5 terminal."""
        if not mt5.initialize():
            logger.error(f"initialize() failed, error code = {mt5.last_error()}")
            return False
            
        # Check if symbol is available
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            logger.error(f"{self.symbol} not found.")
            mt5.shutdown()
            return False
            
        # If the symbol is unavailable in MarketWatch, add it
        if not symbol_info.visible:
            logger.info(f"{self.symbol} is not visible, trying to switch on")
            if not mt5.symbol_select(self.symbol, True):
                logger.error(f"symbol_select({self.symbol}) failed")
                mt5.shutdown()
                return False
                
        logger.info(f"Successfully connected to MT5 and selected {self.symbol}")
        return True

    def fetch_historical_data(self, num_bars=10000, tf=None):
        """Fetches historical data for the given symbol and timeframe."""
        if tf is None:
            tf = self.timeframe
            
        rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, num_bars)
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to fetch historical data for {self.symbol}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df

    def fetch_latest_data(self, tf=None):
        """Fetches the most recent closed candle. Used for live streaming updates."""
        if tf is None:
            tf = self.timeframe
            
        # Fetch the last 2 bars, 0 is current unclosed, 1 is the last closed
        rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, 2)
        if rates is None or len(rates) < 2:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        # Return the last closed candle which is at index 0 because copy_rates_from_pos returns oldest first
        return df.iloc[:-1]

    def disconnect(self):
        """Disconnects from MT5 terminal."""
        mt5.shutdown()
        logger.info("Disconnected from MT5")
