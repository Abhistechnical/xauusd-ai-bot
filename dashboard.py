import streamlit as st
import pandas as pd
import MetaTrader5 as mt5
import logging
from data import DataPipeline
from features import FeatureEngineer

# Import our instant strategy runner
from run_strategy_now import run_instant_analysis

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
        
    st.divider()
    st.subheader("🤖 Instant AI Trade Execution")
    st.write("Clicking this button commands the AI to instantly analyze the market and deploy a trade using your strict parameters (0.10 Lot | 10 SL | 20 TP).")
    
    if st.button("⚡ Analyze & Execute Trade NOW", type="primary"):
        with st.spinner("AI Matrix analyzing live data and deploying execution instructions to MT5..."):
            try:
                run_instant_analysis()
                # If it doesn't crash, flash success.
                st.success("✅ Analysis complete! The AI execution command was successfully sent to MT5. Check your MT5 Trade tab to see the active position!")
            except Exception as e:
                st.error(f"Error during AI execution: {e}")
        
    st.divider()
    st.info("Start the `main.py` back-end process in your terminal if you want the bot to run the active AI loop autonomously 24/5.")
else:
    st.error("Failed to connect to MT5 or fetch data. Please ensure MetaTrader 5 is running and logged into a demo/live account.")
