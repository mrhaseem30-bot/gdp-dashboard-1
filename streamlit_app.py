import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib

# ... (upar wala code same rahega - title, coin selector etc.)

# ==================== IMPROVED MULTI-TF LIQUIDITY FUNCTION ====================
def find_swing_highs_lows(df, window=5, min_distance=3):
    """Swing Highs & Lows detect karega"""
    highs = []
    lows = []
    for i in range(window, len(df) - window):
        if df['High'].iloc[i] == df['High'].iloc[i-window:i+window+1].max():
            highs.append((df.index[i], df['High'].iloc[i]))
        if df['Low'].iloc[i] == df['Low'].iloc[i-window:i+window+1].min():
            lows.append((df.index[i], df['Low'].iloc[i]))
    return highs, lows

def get_liquidity_zones_multi(df, lookback_periods=[20, 60, 252]):
    """Multiple liquidity zones with different lookbacks"""
    zones = {"demand": [], "supply": []}
    
    for period in lookback_periods:
        if len(df) < period:
            continue
        recent = df.tail(period)
        
        highs, lows = find_swing_highs_lows(recent, window=5)
        
        # Top Supply Zones (recent significant highs)
        if highs:
            supply_levels = sorted([h[1] for h in highs[-4:]], reverse=True)  # last 4 swings
            zones["supply"].extend(supply_levels)
        
        # Bottom Demand Zones (recent significant lows)
        if lows:
            demand_levels = sorted([l[1] for l in lows[-4:]])
            zones["demand"].extend(demand_levels)
    
    # Unique + rounded
    zones["demand"] = sorted(list(set([round(x, 4) for x in zones["demand"]])))
    zones["supply"] = sorted(list(set([round(x, 4) for x in zones["supply"]])))
    
    return zones

# ====================== MAIN DATA FETCH ======================
@st.cache_data(ttl=60)
def get_data(ticker):
    df15 = yf.download(ticker, period="5d", interval="15m")
    df1h = yf.download(ticker, period="30d", interval="1h")
    df4h = yf.download(ticker, period="90d", interval="4h")
    df1d = yf.download(ticker, period="1y", interval="1d")   # 1 year daily
    return df15, df1h, df4h, df1d

# ... data loading aur cleaning same rahega ...

# ==================== LIQUIDITY CALCULATION ====================
live_price = float(df15['Close'].iloc[-1])

# Multi Timeframe Liquidity
liquidity_1h = get_liquidity_zones_multi(df1h, [20, 60])      # \~1 week + 1 month
liquidity_4h = get_liquidity_zones_multi(df4h, [30, 90])
liquidity_daily = get_liquidity_zones_multi(df1d, [5, 20, 120])  # 1w, 1m, \~6 months

# Combine all
all_demand = sorted(list(set(liquidity_1h["demand"] + liquidity_4h["demand"] + liquidity_daily["demand"])))
all_supply = sorted(list(set(liquidity_1h["supply"] + liquidity_4h["supply"] + liquidity_daily["supply"])))

# Current price position
near_demand = [z for z in all_demand if abs(z - live_price)/live_price < 0.015]  # 1.5% ke andar
near_supply = [z for z in all_supply if abs(z - live_price)/live_price < 0.015]

# ====================== UI DISPLAY ======================
st.subheader("🔍 Multi-Timeframe Liquidity Zones")

col1, col2 = st.columns(2)

with col1:
    st.success("**Demand Zones (Lower Liquidity)**")
    for zone in all_demand[-6:]:   # last 6 zones
        dist = ((live_price - zone) / zone) * 100
        st.write(f"**${zone:,.4f}** → {dist:+.2f}% below price")

with col2:
    st.error("**Supply Zones (Upper Liquidity)**")
    for zone in all_supply[-6:]:
        dist = ((zone - live_price) / live_price) * 100
        st.write(f"**${zone:,.4f}** → {dist:+.2f}% above price")

# Current Position
if near_demand:
    st.success(f"**Price Near Demand Liquidity:** ${near_demand[0]:,.4f}")
elif near_supply:
    st.error(f"**Price Near Supply Liquidity:** ${near_supply[0]:,.4f}")
else:
    st.info("Price currently between major liquidity zones")

# Signal Logic (Improved)
if rsi1h < 30 and near_demand:
    signal = "🟢 STRONG BUY (Liquidity Grab)"
    color = "lime"
elif rsi1h > 70 and near_supply:
    signal = "🔴 STRONG SELL (Liquidity Sweep)"
    color = "red"
else:
    signal = "⭕ NEUTRAL"
    color = "orange"

st.markdown(f"<h2 style='color:{color}; text-align:center;'>{signal}</h2>", unsafe_allow_html=True)
