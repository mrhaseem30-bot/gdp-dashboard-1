import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib
from datetime import datetime

st.set_page_config(page_title="H32 Liquidity Bot", layout="wide")

# Sidebar
with st.sidebar:
    st.title("⚙️ Controls")
    coins = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD",
        "Sui (SUI)": "SUI-USD",
        "Chainlink (LINK)": "LINK-USD"
    }
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    ticker = coins[selected_coin]
    
    refresh_button = st.button("🔄 Manual Refresh Now")
    st.info("Auto-refresh every 15 seconds")

# Auto Refresh
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=15000, limit=None, key="datarefresh")  # 15 seconds
except:
    pass  # agar component nahi hai toh skip

st.title("📊 H32 RSI + Liquidity Bot")
st.subheader("Multi-Timeframe Liquidity Zones + RSI")

# ==================== DATA FETCH (Improved) ====================
@st.cache_data(ttl=30)
def get_data(ticker):
    try:
        df15 = yf.download(ticker, period="7d", interval="15m", progress=False)
        df1h = yf.download(ticker, period="60d", interval="1h", progress=False)
        df4h = yf.download(ticker, period="180d", interval="4h", progress=False)
        df1d = yf.download(ticker, period="1y", interval="1d", progress=False)

        for df in [df15, df1h, df4h, df1d]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
        return df15, df1h, df4h, df1d
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df15, df1h, df4h, df1d = get_data(ticker)

if df15.empty or len(df15) < 5:
    st.error("❌ Data fetch failed. Trying again automatically...")
    st.stop()

live_price = float(df15['Close'].iloc[-1])

# ==================== LIQUIDITY ZONES ====================
def get_liquidity_zones(df, lookbacks=[20, 60, 200]):
    demand, supply = [], []
    for lb in lookbacks:
        if len(df) < lb: continue
        recent = df.tail(lb)
        # Swing Lows (Demand)
        lows = recent['Low'].rolling(window=5, center=True).min()
        demand.extend(lows.dropna().unique())
        # Swing Highs (Supply)
        highs = recent['High'].rolling(window=5, center=True).max()
        supply.extend(highs.dropna().unique())
    
    demand = sorted(list(set([round(x, 2) for x in demand if not pd.isna(x)])))[-10:]
    supply = sorted(list(set([round(x, 2) for x in supply if not pd.isna(x)])))[-10:]
    return demand, supply

demand_zones, supply_zones = get_liquidity_zones(df1d)  # Daily pe zyada focus

# ==================== UI ====================
col1, col2 = st.columns([1, 2])
with col1:
    st.metric(f"**{selected_coin}**", f"${live_price:,.2f}", f"{datetime.now().strftime('%H:%M:%S')}")

# Liquidity Display (Badi-Badi Zones)
st.subheader("🔥 Major Liquidity Zones")

col_d, col_s = st.columns(2)

with col_d:
    st.success("**Demand / Support Zones** (Entry Points)")
    for zone in demand_zones:
        dist = ((live_price - zone) / zone) * 100
        if abs(dist) < 3:
            st.markdown(f"**${zone:,.2f}** ← **VERY CLOSE** ({dist:+.1f}%)")
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

with col_s:
    st.error("**Supply / Resistance Zones**")
    for zone in supply_zones:
        dist = ((zone - live_price) / live_price) * 100
        if abs(dist) < 3:
            st.markdown(f"**${zone:,.2f}** ← **VERY CLOSE** ({dist:+.1f}%)")
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

# RSI
st.subheader("RSI Status")
try:
    rsi1h = talib.RSI(df1h['Close'], timeperiod=14).iloc[-1]
    st.write(f"**1 Hour RSI:** {rsi1h:.2f}")
except:
    st.write("RSI calculating...")

# Chart
if not df1h.empty:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df1h.index, open=df1h['Open'], high=df1h['High'],
                                 low=df1h['Low'], close=df1h['Close']))
    fig.update_layout(height=650, template="plotly_dark", 
                      title=f"{selected_coin} - 1H Chart with Liquidity")
    st.plotly_chart(fig, use_container_width=True)
