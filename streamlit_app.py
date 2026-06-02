import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib
from datetime import datetime

st.set_page_config(page_title="H32 Liquidity Bot", layout="wide")

# Sidebar Controls
with st.sidebar:
    st.title("⚙️ Settings")
    
    coins = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD"
    }
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    ticker = coins[selected_coin]
    
    # Timeframe Selector (TradingView Style)
    timeframe = st.selectbox("Timeframe", 
        ["15m", "30m", "1h", "2h", "4h", "Daily"], index=2)
    
    st.button("🔄 Refresh Now")

st.title("📊 H32 RSI + Liquidity Bot")
st.caption(f"Live • {selected_coin} • {timeframe}")

# ==================== DATA FETCH ====================
@st.cache_data(ttl=20)
def get_data(ticker, tf):
    period_map = {"15m":"5d", "30m":"10d", "1h":"30d", "2h":"60d", "4h":"90d", "Daily":"1y"}
    interval = tf if tf != "Daily" else "1d"
    period = period_map.get(tf, "30d")
    
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df = get_data(ticker, timeframe)

if df.empty or len(df) < 20:
    st.error("Data fetch failed. Auto retrying...")
    st.stop()

live_price = float(df['Close'].iloc[-1])

# ==================== RECENT LIQUIDITY ZONES ====================
def get_recent_liquidity(df, window=8):
    # Recent Swing Lows (Buy/Demand)
    swing_lows = df['Low'].rolling(window=window, center=True).min()
    demand_zones = sorted(list(set([round(x, 2) for x in swing_lows.dropna().tail(12).unique() if x > 0])))
    
    # Recent Swing Highs (Sell/Supply)
    swing_highs = df['High'].rolling(window=window, center=True).max()
    supply_zones = sorted(list(set([round(x, 2) for x in swing_highs.dropna().tail(12).unique() if x > 0])))
    
    # Filter already swept zones
    active_demand = [z for z in demand_zones if z < live_price * 1.05]   # only below or near price
    active_supply = [z for z in supply_zones if z > live_price * 0.95]  # only above or near price
    
    return active_demand[-8:], active_supply[-8:]

demand_zones, supply_zones = get_recent_liquidity(df)

# RSI
rsi = talib.RSI(df['Close'], timeperiod=14).iloc[-1] if len(df) > 14 else None

# ==================== UI ====================
col1, col2 = st.columns([1,2])
with col1:
    st.metric("Current Price", f"${live_price:,.2f}")

with col2:
    if rsi:
        if rsi < 30:
            st.success(f"RSI: {rsi:.1f} → Oversold (Strong Buy Zone)")
        elif rsi > 70:
            st.error(f"RSI: {rsi:.1f} → Overbought (Strong Sell Zone)")
        else:
            st.info(f"RSI: {rsi:.1f}")

# Liquidity Zones
st.subheader("🔥 Active Liquidity Zones")

c1, c2 = st.columns(2)

with c1:
    st.success("**BUY Liquidity (Demand/Support)** - Entry Points")
    for zone in demand_zones:
        dist = ((live_price - zone) / zone) * 100
        if abs(dist) < 2.5:
            st.markdown(f"**${zone:,.2f}** ← **VERY CLOSE** ({dist:+.1f}%)")
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%) below")

with c2:
    st.error("**SELL Liquidity (Supply/Resistance)** - Short Targets")
    for zone in supply_zones:
        dist = ((zone - live_price) / live_price) * 100
        if abs(dist) < 2.5:
            st.markdown(f"**${zone:,.2f}** ← **VERY CLOSE** ({dist:+.1f}%)")
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%) above")

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close']))
fig.update_layout(height=650, template="plotly_dark", 
                  title=f"{selected_coin} - {timeframe} Chart")
st.plotly_chart(fig, use_container_width=True)
