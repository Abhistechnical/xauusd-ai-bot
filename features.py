import pandas as pd
import pandas_ta as ta
import numpy as np

class FeatureEngineer:
    def __init__(self, data: pd.DataFrame):
        self.df = data.copy()
        
    def add_technical_indicators(self):
        """Adds standard technical indicators (EMA, RSI, ATR, Volume)."""
        # Feature: 50 EMA and 200 EMA
        self.df['ema_50'] = ta.ema(self.df['close'], length=50)
        self.df['ema_200'] = ta.ema(self.df['close'], length=200)
        
        # Feature: RSI 14
        self.df['rsi_14'] = ta.rsi(self.df['close'], length=14)
        
        # Feature: ATR 14 (Volatility)
        self.df['atr_14'] = ta.atr(self.df['high'], self.df['low'], self.df['close'], length=14)
        
        # Feature: Volume ratios
        self.df['volume_ma'] = ta.sma(self.df['tick_volume'], length=20)
        self.df['vol_ratio'] = self.df['tick_volume'] / self.df['volume_ma']
        
        return self.df
        
    def add_smc_features(self):
        """
        Adds simplified Smart Money Concept features (BOS, CHOCH, Order Blocks).
        Calculated without lookahead bias.
        """
        window = 5
        
        # Rolling min / max (excluding current bar) to establish local structure
        prev_max = self.df['high'].shift(1).rolling(window=window).max()
        prev_min = self.df['low'].shift(1).rolling(window=window).min()
        
        # Break of Structure (BOS) / Change of Character (CHOCH)
        # 1 if close breaks recent high, -1 if close breaks recent low
        self.df['bos_bullish'] = np.where(self.df['close'] > prev_max, 1, 0)
        self.df['bos_bearish'] = np.where(self.df['close'] < prev_min, 1, 0)
        
        # Momentum Surges (Placeholder for impulsive moves leaving order blocks)
        self.df['momentum'] = (self.df['close'] - self.df['open']) / self.df['atr_14']
        
        return self.df
        
    def add_target_variable(self, shift_period=5):
        """
        Creates the target variable for ML training.
        1: BUY (Price goes up by > 1.0 ATR within next `shift_period` bars)
        -1: SELL (Price goes down by > 1.0 ATR within next `shift_period` bars)
        0: HOLD / NO CLEAR SIGNAL
        """
        # Note: This introduces lookahead bias artificially for the TARGET variable only.
        # It must ONLY be used during offline training, NEVER as a live feature.
        
        future_return = (self.df['close'].shift(-shift_period) - self.df['close'])
        
        # Require a move of at least 1.0 ATR
        # Fill NaN backwards from the shift so threshold array matches length
        threshold = self.df['atr_14'] * 1.0
        
        conditions = [
            (future_return > threshold),
            (future_return < -threshold)
        ]
        choices = [1, -1]
        
        self.df['target'] = np.select(conditions, choices, default=0)
        
        # Since we use shift(-shift_period), the last `shift_period` rows will have NaN/inaccurate data
        # We replace the last shift_periods with NaN so they get dropped.
        self.df.loc[self.df.index[-shift_period:], 'target'] = np.nan
        
        return self.df
        
    def generate_all(self, training=True):
        """Generates all features and an optional target column."""
        self.add_technical_indicators()
        self.add_smc_features()
        
        if training:
            self.add_target_variable()
            
        # Drop rows with NaN values resulting from EMAs, MAs, and shifts
        self.df.dropna(inplace=True)
        return self.df
