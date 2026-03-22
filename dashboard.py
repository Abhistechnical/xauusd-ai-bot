import streamlit as st
import pandas as pd
import MetaTrader5 as mt5
from data import DataPipeline
from features import FeatureEngineer

# Setup page
st.set_page_config(page_title="XAUUSD AI Trading Bot", layout="wide")
st.title("📈 XAUUSD AI Trading System Dashboard")

@st.cache_data(ttl=60)
def load_data():
    dp = DataPipeline("XAUUSD", mt5.TIMEFRAME_M15)
    if dp.connect():
        df = dp.fetch_historical_data(500)
        dp.disconnect()
        if df is not None:
            fe = FeatureEngineer(df)
            df_feat = fe.generate_all(training=False)
            return df_feat
    return None

df = load_data()

if df is not None:
    st.subheader("Live Market Data & Features")
    st.dataframe(df.tail(10))
    
    st.subheader("Price Action (Close + 50/200 EMA)")
    chart_data = df[['close', 'ema_50', 'ema_200']]
    st.line_chart(chart_data)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"{df['close'].iloc[-1]:.2f}")
    with col2:
        st.metric("RSI (14)", f"{df['rsi_14'].iloc[-1]:.2f}")
    with col3:
        st.metric("ATR (14)", f"{df['atr_14'].iloc[-1]:.2f}")
    with col4:
        trend = "Bullish" if df['ema_50'].iloc[-1] > df['ema_200'].iloc[-1] else "Bearish"
        st.metric("Trend", trend)
        
    st.info("Start `main.py` back-end process to run the active AI loop. This web dashboard is for realtime visualization of the engineered DataFrames.")
else:
    st.error("Failed to connect to MT5 or fetch data. Please ensure MetaTrader 5 is running and logged into a demo/live account.")
