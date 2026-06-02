import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib

st.set_page_config(page_title="H32 Liquidity Bot", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2 { color: #00ffcc; }
    .buy { color: #00ff88; font-weight: bold; }
    .sell { color: #ff4444; font-weight: bold; }
    .high-vol { color: #ffff00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ H32 Liquidity + Volume Bot")
    coins = {
        "Bitcoin (BTC)": "BTC-USD",
        "Ethereum (ETH)": "ETH-USD",
        "Solana (SOL)": "SOL-USD"
    }
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    ticker = coins[selected_coin]
    
    lookback = st.selectbox("Lookback Period", 
        ["1 Day", "1 Week", "1 Month", "3 Months", "6 Months", "1 Year"], 
        index=2)

# Period mapping
period_map = {"1 Day": 5, "1 Week": 10, "1 Month": 40, "3 Months": 100, "6 Months": 200, "1 Year": 400}
days = period_map[lookback]

st.title("📊 H32 RSI + Volume Liquidity Bot")
st.caption(f"{selected_coin} • {lookback} Lookback • Volume + Liquidity")

# Data Fetch
@st.cache_data(ttl=30)
def get_data(ticker):
    df = yf.download(ticker, period="1y", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

df = get_data(ticker)

if df.empty or len(df) < 20:
    st.error("Data fetch failed. Please try again.")
    st.stop()

live_price = float(df['Close'].iloc[-1])
recent_df = df.tail(days)

# ==================== VOLUME + LIQUIDITY ANALYSIS ====================
def get_volume_liquidity_zones(recent_df, live_price):
    # Simple Volume Profile (Price bins)
    price_range = pd.cut(recent_df['Close'], bins=30)
    volume_profile = recent_df.groupby(price_range)['Volume'].sum()
    
    # High Volume Nodes (HVN)
    high_vol_levels = volume_profile.nlargest(8).index
    high_vol_prices = [interval.mid for interval in high_vol_levels]
    
    # Demand Zones (Swing Lows + Volume)
    demand = recent_df['Low'].rolling(window=5, center=True).min().dropna().tail(8)
    demand_zones = sorted([round(x, 2) for x in demand])
    
    # Supply Zones (Swing Highs + Volume)
    supply = recent_df['High'].rolling(window=5, center=True).max().dropna().tail(8)
    supply_zones = sorted([round(x, 2) for x in supply])
    
    return demand_zones, supply_zones, [round(p, 2) for p in high_vol_prices]

demand_zones, supply_zones, high_vol_zones = get_volume_liquidity_zones(recent_df, live_price)

# RSI
rsi = talib.RSI(df['Close'], timeperiod=14).iloc[-1] if len(df) > 14 else None

# UI
col1, col2 = st.columns([1, 1])
with col1:
    st.metric("**CURRENT PRICE**", f"${live_price:,.2f}")
with col2:
    if rsi:
        if rsi < 35:
            st.success(f"RSI: {rsi:.1f} → Strong Buy")
        elif rsi > 65:
            st.error(f"RSI: {rsi:.1f} → Strong Sell")
        else:
            st.info(f"RSI: {rsi:.1f}")

st.markdown("---")
st.subheader(f"🔥 {lookback} Volume + Liquidity Zones")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("**🟢 BUY ZONES (Demand)**", unsafe_allow_html=True)
    for zone in demand_zones:
        dist = ((live_price - zone) / zone) * 100
        if abs(dist) < 3:
            st.markdown(f"<span class='buy'>**${zone:,.2f}** ← HOT BUY ({dist:+.1f}%)</span>", unsafe_allow_html=True)
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

with c2:
    st.markdown("**🔴 SELL ZONES (Supply)**", unsafe_allow_html=True)
    for zone in supply_zones:
        dist = ((zone - live_price) / live_price) * 100
        if abs(dist) < 3:
            st.markdown(f"<span class='sell'>**${zone:,.2f}** ← HOT SELL ({dist:+.1f}%)</span>", unsafe_allow_html=True)
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

with c3:
    st.markdown("**🟡 HIGH VOLUME NODES** (Big Buying/Selling)", unsafe_allow_html=True)
    for zone in sorted(high_vol_zones):
        dist = ((live_price - zone) / zone) * 100 if zone < live_price else ((zone - live_price) / live_price) * 100
        st.write(f"${zone:,.2f} ({dist:+.1f}%)")

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.tail(180).index, open=df.tail(180)['Open'], 
                            high=df.tail(180)['High'], low=df.tail(180)['Low'], 
                            close=df.tail(180)['Close'], name="Price"))
fig.add_trace(go.Bar(x=df.tail(180).index, y=df.tail(180)['Volume'], name="Volume", opacity=0.6, marker_color='gray'))
fig.update_layout(height=650, template="plotly_dark", 
                  title=f"{selected_coin} - Price + Volume")
st.plotly_chart(fig, use_container_width=True)
