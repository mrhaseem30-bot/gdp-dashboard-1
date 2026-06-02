import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib
from datetime import datetime

st.set_page_config(page_title="H32 Liquidity Bot", layout="wide", page_icon="📈")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2, h3 { color: #00ffcc; }
    .buy-zone { color: #00ff88; font-weight: bold; }
    .sell-zone { color: #ff4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ H32 Liquidity Bot")
    coins = {"Bitcoin (BTC)": "BTC-USD", "Ethereum (ETH)": "ETH-USD", "Solana (SOL)": "SOL-USD"}
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    ticker = coins[selected_coin]
    
    period_option = st.selectbox("Lookback Period (Liquidity)", 
        ["1 Week", "2 Weeks", "15 Days", "1 Month", "3 Months"], index=3)
    
    chart_tf = st.selectbox("Chart Timeframe", ["15m", "1h", "4h", "1d"], index=2)

# Period to days mapping
period_days = {
    "1 Week": 7, "2 Weeks": 14, "15 Days": 15, 
    "1 Month": 30, "3 Months": 90
}
days = period_days[period_option]

st.title("📊 H32 RSI + Liquidity Bot")
st.caption(f"**{selected_coin}** • {period_option} Lookback • {chart_tf} Chart")

# Data Fetch
@st.cache_data(ttl=20)
def get_data(ticker, days, chart_tf):
    try:
        df_main = yf.download(ticker, period=f"{days+10}d", interval=chart_tf, progress=False)
        if isinstance(df_main.columns, pd.MultiIndex):
            df_main.columns = df_main.columns.get_level_values(0)
        return df_main
    except:
        return pd.DataFrame()

df = get_data(ticker, days, chart_tf)

if df.empty or len(df) < 20:
    st.error("Data fetch failed. Please try again.")
    st.stop()

live_price = float(df['Close'].iloc[-1])

# ==================== PERIOD WISE LIQUIDITY ====================
def get_liquidity_zones(df, lookback_days):
    # Take only recent data for this period
    recent_df = df.tail(lookback_days * 24 if 'h' in chart_tf else lookback_days)  # rough adjustment
    
    # Demand Zones (Swing Lows)
    demand = recent_df['Low'].rolling(window=5, center=True).min().dropna()
    demand_zones = sorted(list(set([round(x, 2) for x in demand.tail(8)])))
    
    # Supply Zones (Swing Highs)
    supply = recent_df['High'].rolling(window=5, center=True).max().dropna()
    supply_zones = sorted(list(set([round(x, 2) for x in supply.tail(8)])))
    
    return demand_zones, supply_zones

demand_zones, supply_zones = get_liquidity_zones(df, days)

# RSI (on current chart TF)
rsi = talib.RSI(df['Close'], timeperiod=14).iloc[-1] if len(df) > 14 else None

# UI
col1, col2 = st.columns([1,1])
with col1:
    st.metric("**CURRENT PRICE**", f"${live_price:,.2f}")
with col2:
    if rsi:
        if rsi < 35:
            st.success(f"RSI {rsi:.1f} → Strong Buy")
        elif rsi > 65:
            st.error(f"RSI {rsi:.1f} → Strong Sell")
        else:
            st.info(f"RSI {rsi:.1f}")

st.markdown("---")
st.subheader(f"🔥 {period_option} Liquidity Zones")

c1, c2 = st.columns(2)

with c1:
    st.markdown("**BUY ZONES (Demand / Support)**", unsafe_allow_html=True)
    for zone in demand_zones:
        dist = ((live_price - zone) / zone) * 100
        if abs(dist) < 2:
            st.markdown(f"**${zone:,.2f}** ← **HOT BUY ENTRY** ({dist:+.1f}%)", unsafe_allow_html=True)
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

with c2:
    st.markdown("**SELL ZONES (Supply / Resistance)**", unsafe_allow_html=True)
    for zone in supply_zones:
        dist = ((zone - live_price) / live_price) * 100
        if abs(dist) < 2:
            st.markdown(f"**${zone:,.2f}** ← **HOT SELL** ({dist:+.1f}%)", unsafe_allow_html=True)
        else:
            st.write(f"${zone:,.2f} ({dist:+.1f}%)")

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                            low=df['Low'], close=df['Close']))
fig.update_layout(height=650, template="plotly_dark", 
                  title=f"{selected_coin} - {chart_tf} Chart ({period_option})")
st.plotly_chart(fig, use_container_width=True)
