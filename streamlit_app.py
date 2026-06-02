import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import talib
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="H32 Multi API Liquidity Bot", layout="wide")

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
    st.title("⚙️ H32 Multi-API Bot")
    coins = {"Bitcoin (BTC)": "BTCUSDT", "Ethereum (ETH)": "ETHUSDT"}
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    symbol = coins[selected_coin]
    
    lookback = st.selectbox("Lookback Period", 
        ["1 Month", "3 Months", "6 Months", "1 Year"], index=2)

period_map = {"1 Month": 45, "3 Months": 120, "6 Months": 240, "1 Year": 400}
days = period_map[lookback]

st.title("📊 H32 Long Term Liquidity Bot")
st.caption(f"{selected_coin} • {lookback} • Multi API")

# ==================== MULTI API DATA FETCH ====================
@st.cache_data(ttl=180)  # 3 minutes cache
def get_multi_source_data(symbol, days):
    # 1. Binance
    try:
        end = int(datetime.now().timestamp() * 1000)
        start = int((datetime.now() - timedelta(days=days+30)).timestamp() * 1000)
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": symbol, "interval": "1d", "startTime": start, "endTime": end, "limit": 1000}
        resp = requests.get(url, params=params, timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            df = pd.DataFrame(data, columns=['ts','Open','High','Low','Close','Volume','_','_','_','_','_','_'])
            df = df[['ts','Open','High','Low','Close','Volume']].astype(float)
            df['ts'] = pd.to_datetime(df['ts'], unit='ms')
            df.set_index('ts', inplace=True)
            st.success("✅ Binance se data mila")
            return df
    except:
        pass

    # 2. CoinGecko Fallback
    try:
        coin_id = "bitcoin" if "BTC" in symbol else "ethereum"
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
        params = {"vs_currency": "usd", "days": days+30, "interval": "daily"}
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            prices = data['prices']
            df = pd.DataFrame(prices, columns=['timestamp', 'Close'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            st.success("✅ CoinGecko se data mila")
            return df
    except:
        pass

    # 3. yfinance Last Fallback
    try:
        import yfinance as yf
        ticker = "BTC-USD" if "BTC" in symbol else "ETH-USD"
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        st.success("✅ yfinance se data mila")
        return df
    except:
        return pd.DataFrame()

df = get_multi_source_data(symbol, days)

if df.empty or len(df) < 30:
    st.error("Sabhi sources se data nahi aa raha. Thodi der baad refresh karo.")
    st.stop()

live_price = float(df['Close'].iloc[-1])
recent = df.tail(days)

# Liquidity Logic
def get_major_zones(recent, live_price):
    demand = []
    supply = []
    for i in range(15, len(recent)-8):
        # Major Demand Zones
        if recent['Low'].iloc[i] == recent['Low'].rolling(14, center=True).min().iloc[i]:
            demand.append(round(recent['Low'].iloc[i], 2))
        # Major Supply Zones
        if recent['High'].iloc[i] == recent['High'].rolling(14, center=True).max().iloc[i]:
            supply.append(round(recent['High'].iloc[i], 2))
    
    return sorted(list(set(demand[-10:]))), sorted(list(set(supply[-8:])))

demand_zones, supply_zones = get_major_zones(recent, live_price)

rsi = talib.RSI(df['Close'], timeperiod=14).iloc[-1] if len(df) > 14 else None

# UI
col1, col2 = st.columns([1,1])
with col1:
    st.metric("**CURRENT PRICE**", f"${live_price:,.2f}")
with col2:
    if rsi:
        if rsi < 40: st.success(f"RSI {rsi:.1f} → Long Term Buy Possible")
        elif rsi > 70: st.error(f"RSI {rsi:.1f} → Caution")

st.subheader(f"🔥 Major {lookback} Liquidity Zones")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**🟢 MAJOR BUY / DEMAND ZONES**")
    for z in demand_zones:
        dist = ((live_price - z) / z) * 100
        st.markdown(f"<span class='buy'>**${z:,.2f}** ← STRONG ACCUMULATION ({dist:+.1f}%)</span>", unsafe_allow_html=True)

with c2:
    st.markdown("**🔴 MAJOR SELL / SUPPLY ZONES**")
    for z in supply_zones:
        dist = ((z - live_price) / live_price) * 100
        st.markdown(f"<span class='sell'>**${z:,.2f}** ← MAJOR RESISTANCE ({dist:+.1f}%)</span>", unsafe_allow_html=True)

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=recent.index, open=recent['Open'] if 'Open' in recent.columns else recent['Close'],
                            high=recent['High'] if 'High' in recent.columns else recent['Close'],
                            low=recent['Low'] if 'Low' in recent.columns else recent['Close'],
                            close=recent['Close']))
fig.update_layout(height=700, template="plotly_dark", title=f"{selected_coin} Long Term View")
st.plotly_chart(fig, use_container_width=True)
