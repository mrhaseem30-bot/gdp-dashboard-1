import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib
from datetime import datetime

st.set_page_config(page_title="H32 Liquidity Bot", layout="wide", page_icon="📈")

# Custom CSS for Colorful Trading Dashboard Look
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    .metric-label {
        color: #00ff88 !important;
    }
    .stSuccess { background-color: #0a3d1f; }
    .stError { background-color: #3d1f0a; }
    h1, h2, h3 { color: #00ffcc; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ H32 CONTROL PANEL")
    st.markdown("---")
    
    coins = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD"
    }
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    ticker = coins[selected_coin]
    
    # Timeframe
    timeframe = st.selectbox("Timeframe", 
        ["15m", "30m", "1h", "2h", "4h", "1d"], index=2)
    
    if st.button("🔄 Force Refresh"):
        st.cache_data.clear()

st.title("📊 H32 RSI + LIQUIDITY BOT")
st.markdown(f"**LIVE** • {selected_coin} • **{timeframe}**")

# ==================== IMPROVED DATA FETCH ====================
@st.cache_data(ttl=15)
def get_data(ticker, tf):
    try:
        interval_map = {
            "15m": ("7d", "15m"),
            "30m": ("14d", "30m"),
            "1h": ("30d", "1h"),
            "2h": ("60d", "2h"),
            "4h": ("90d", "4h"),
            "1d": ("1y", "1d")
        }
        period, interval = interval_map.get(tf, ("30d", "1h"))
        
        df = yf.download(ticker, period=period, interval=interval, progress=False, prepost=False)
        
        if df.empty:
            # Fallback
            df = yf.download(ticker, period="30d", interval="1h", progress=False)
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        return df
    except:
        return pd.DataFrame()

df = get_data(ticker, timeframe)

if df.empty or len(df) < 10:
    st.error("⚠️ Data fetch failed. Retrying with fallback...")
    df = yf.download(ticker, period="30d", interval="1h", progress=False)
    if df.empty:
        st.stop()

live_price = float(df['Close'].iloc[-1])

# ==================== LIQUIDITY ZONES ====================
def get_liquidity_zones(df, live_price):
    # Demand Zones (Buy Liquidity)
    demand = df['Low'].rolling(window=7, center=True).min().dropna().tail(10)
    demand_zones = sorted(list(set([round(x, 2) for x in demand if x > 0])))
    
    # Supply Zones (Sell Liquidity)
    supply = df['High'].rolling(window=7, center=True).max().dropna().tail(10)
    supply_zones = sorted(list(set([round(x, 2) for x in supply if x > 0])))
    
    # Active zones only
    active_demand = [z for z in demand_zones if z <= live_price * 1.08]
    active_supply = [z for z in supply_zones if z >= live_price * 0.92]
    
    return active_demand[-8:], active_supply[-8:]

demand_zones, supply_zones = get_liquidity_zones(df, live_price)

# RSI
rsi = talib.RSI(df['Close'], timeperiod=14).iloc[-1] if len(df) > 14 else 50

# ==================== MAIN UI ====================
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.metric("CURRENT PRICE", f"${live_price:,.2f}", delta=None)
with col2:
    if rsi < 35:
        st.success(f"RSI: {rsi:.1f} → OVERSOLD (BUY)")
    elif rsi > 65:
        st.error(f"RSI: {rsi:.1f} → OVERBOUGHT (SELL)")
    else:
        st.info(f"RSI: {rsi:.1f} → NEUTRAL")

# Liquidity Zones
st.markdown("---")
st.subheader("🔥 ACTIVE LIQUIDITY ZONES")

c1, c2 = st.columns(2)

with c1:
    st.markdown('<h3 style="color:#00ff88;">BUY ZONES (Demand / Support)</h3>', unsafe_allow_html=True)
    for zone in demand_zones:
        dist = ((live_price - zone) / zone) * 100
        if abs(dist) < 3:
            st.markdown(f"**${zone:,.2f}** ← **HOT ENTRY** ({dist:+.1f}%)")
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

with c2:
    st.markdown('<h3 style="color:#ff4444;">SELL ZONES (Supply / Resistance)</h3>', unsafe_allow_html=True)
    for zone in supply_zones:
        dist = ((zone - live_price) / live_price) * 100
        if abs(dist) < 3:
            st.markdown(f"**${zone:,.2f}** ← **HOT RESISTANCE** ({dist:+.1f}%)")
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

# Chart with dark theme
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close'], name="Price"))
fig.update_layout(
    height=700, 
    template="plotly_dark",
    title=f"{selected_coin} - {timeframe} Chart",
    paper_bgcolor='#0e1117',
    plot_bgcolor='#1a1f2e'
)
st.plotly_chart(fig, use_container_width=True)
