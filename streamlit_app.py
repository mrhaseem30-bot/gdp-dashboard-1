import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import talib
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="H32 Liquidity Bot", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #ffffff; }
    h1, h2 { color: #00ffcc; }
    .buy { color: #00ff88; font-weight: bold; }
    .sell { color: #ff4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("⚙️ H32 Liquidity Bot")
    coins = {"Bitcoin (BTC)": "BTCUSDT", "Ethereum (ETH)": "ETHUSDT", "Solana (SOL)": "SOLUSDT"}
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    symbol = coins[selected_coin]
    
    lookback = st.selectbox("Lookback Period", 
        ["1 Week", "1 Month", "3 Months", "6 Months", "1 Year"], index=3)

period_map = {"1 Week": 14, "1 Month": 45, "3 Months": 120, "6 Months": 240, "1 Year": 400}
days = period_map[lookback]

st.title("📊 H32 Liquidity + Volume Bot")
st.caption(f"{selected_coin} • {lookback}")

# ==================== DATA FETCH (Binance + Fallback) ====================
@st.cache_data(ttl=20)
def get_data(symbol, days):
    try:
        # Try Binance First
        end = int(datetime.now().timestamp() * 1000)
        start = int((datetime.now() - timedelta(days=days+30)).timestamp() * 1000)
        
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "1d", "startTime": start, "endTime": end, "limit": 1000}
        
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data, columns=['ts','Open','High','Low','Close','Volume','_','_','_','_','_','_'])
            df = df[['ts','Open','High','Low','Close','Volume']].copy()
            df['ts'] = pd.to_datetime(df['ts'], unit='ms')
            df.set_index('ts', inplace=True)
            df = df.astype(float)
            return df
    except:
        pass
    
    # Fallback to yfinance
    st.warning("Binance se data nahi mila, yfinance use kar raha hoon...")
    try:
        import yfinance as yf
        ticker = symbol.replace("USDT", "-USD")
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return pd.DataFrame()

df = get_data(symbol, days)

if df.empty or len(df) < 20:
    st.error("Data fetch failed from both sources. Please refresh after some time.")
    st.stop()

live_price = float(df['Close'].iloc[-1])
recent = df.tail(days)

# Liquidity + Volume Logic
def get_zones(recent, live_price):
    demand = []
    supply = []
    for i in range(10, len(recent)-5):
        # Demand (Buy Liquidity)
        if recent['Low'].iloc[i] == recent['Low'].rolling(7, center=True).min().iloc[i]:
            if recent['Volume'].iloc[i] > recent['Volume'].mean() * 0.7:
                demand.append(round(recent['Low'].iloc[i], 2))
        # Supply (Sell Liquidity)
        if recent['High'].iloc[i] == recent['High'].rolling(7, center=True).max().iloc[i]:
            if recent['Volume'].iloc[i] > recent['Volume'].mean() * 0.7:
                supply.append(round(recent['High'].iloc[i], 2))
    
    return sorted(list(set(demand[-8:]))), sorted(list(set(supply[-8:])))

demand_zones, supply_zones = get_zones(recent, live_price)

rsi = talib.RSI(df['Close'], timeperiod=14).iloc[-1] if len(df) > 14 else None

# UI
col1, col2 = st.columns([1,1])
with col1:
    st.metric("CURRENT PRICE", f"${live_price:,.2f}")
with col2:
    if rsi:
        if rsi < 35:
            st.success(f"RSI {rsi:.1f} → Strong Buy")
        elif rsi > 65:
            st.error(f"RSI {rsi:.1f} → Strong Sell")
        else:
            st.info(f"RSI {rsi:.1f}")

st.subheader(f"🔥 {lookback} High Volume Liquidity Zones")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**🟢 BUY ZONES (Demand)**")
    for z in demand_zones:
        dist = ((live_price - z) / z) * 100
        st.markdown(f"<span class='buy'>**${z:,.2f}** ← HOT ENTRY ({dist:+.1f}%)</span>", unsafe_allow_html=True)

with c2:
    st.markdown("**🔴 SELL ZONES (Supply)**")
    for z in supply_zones:
        dist = ((z - live_price) / live_price) * 100
        st.markdown(f"<span class='sell'>**${z:,.2f}** ← HOT RESISTANCE ({dist:+.1f}%)</span>", unsafe_allow_html=True)

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=recent.index, open=recent['Open'], high=recent['High'],
                            low=recent['Low'], close=recent['Close']))
fig.add_trace(go.Bar(x=recent.index, y=recent['Volume'], name="Volume", opacity=0.5, yaxis="y2"))
fig.update_layout(height=650, template="plotly_dark", title=f"{selected_coin} Chart")
fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
st.plotly_chart(fig, use_container_width=True)
