import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import talib
from datetime import datetime, timedelta
import requests

st.set_page_config(page_title="H32 Binance Liquidity Bot", layout="wide", page_icon="📈")

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
    st.title("⚙️ H32 Binance Volume Bot")
    coins = {"Bitcoin (BTC)": "BTCUSDT", "Ethereum (ETH)": "ETHUSDT", "Solana (SOL)": "SOLUSDT"}
    selected_coin = st.selectbox("Select Coin", list(coins.keys()))
    symbol = coins[selected_coin]
    
    lookback = st.selectbox("Lookback Period", 
        ["1 Week", "1 Month", "3 Months", "6 Months", "1 Year"], index=3)

# Binance Data Fetch Function
def get_binance_data(symbol, interval="1d", days=200):
    try:
        end_time = int(datetime.now().timestamp() * 1000)
        start_time = int((datetime.now() - timedelta(days=days+30)).timestamp() * 1000)
        
        url = f"https://api.binance.com/api/v3/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": 1000
        }
        response = requests.get(url, params=params)
        data = response.json()
        
        df = pd.DataFrame(data, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'CloseTime', 
                                       'QuoteVolume', 'Trades', 'TakerBuyBase', 'TakerBuyQuote', 'Ignore'])
        df = df[['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        df = df.astype(float)
        return df
    except:
        st.error("Binance API se data nahi aa raha. Retry kar rahe hain...")
        return pd.DataFrame()

# Period mapping
period_map = {"1 Week": 14, "1 Month": 45, "3 Months": 120, "6 Months": 240, "1 Year": 400}
days = period_map[lookback]

df = get_binance_data(symbol, "1d", days)

if df.empty or len(df) < 20:
    st.error("Data fetch failed. Please refresh.")
    st.stop()

live_price = float(df['Close'].iloc[-1])
recent = df.tail(days)

st.title("📊 H32 Binance Liquidity + Volume Bot")
st.caption(f"{selected_coin} • {lookback} • Real Binance Data")

# Volume Weighted Liquidity
def get_liquidity_zones(recent, live_price):
    # High Volume Zones
    recent = recent.copy()
    recent['price_bin'] = pd.cut(recent['Close'], bins=35)
    vol_profile = recent.groupby('price_bin')['Volume'].sum()
    high_vol_prices = [round(interval.mid, 2) for interval in vol_profile.nlargest(8).index]
    
    # Demand Zones (Recent High Volume Lows)
    demand_zones = []
    for i in range(10, len(recent)-5):
        if recent['Low'].iloc[i] == recent['Low'].rolling(7, center=True).min().iloc[i]:
            if recent['Volume'].iloc[i] > recent['Volume'].mean() * 0.8:
                demand_zones.append(round(recent['Low'].iloc[i], 2))
    
    # Supply Zones
    supply_zones = []
    for i in range(10, len(recent)-5):
        if recent['High'].iloc[i] == recent['High'].rolling(7, center=True).max().iloc[i]:
            if recent['Volume'].iloc[i] > recent['Volume'].mean() * 0.8:
                supply_zones.append(round(recent['High'].iloc[i], 2))
    
    return sorted(list(set(demand_zones[-8:]))), sorted(list(set(supply_zones[-8:]))), sorted(list(set(high_vol_prices)))

demand_zones, supply_zones, high_vol_zones = get_liquidity_zones(recent, live_price)

rsi = talib.RSI(df['Close'], timeperiod=14).iloc[-1] if len(df) > 14 else None

# UI
col1, col2 = st.columns([1,1])
with col1:
    st.metric("**CURRENT PRICE**", f"${live_price:,.2f}")
with col2:
    if rsi:
        if rsi < 35: st.success(f"RSI {rsi:.1f} → Strong Buy")
        elif rsi > 65: st.error(f"RSI {rsi:.1f} → Strong Sell")
        else: st.info(f"RSI {rsi:.1f}")

st.subheader(f"🔥 {lookback} High Volume Liquidity Zones (Binance Real Data)")

c1, c2 = st.columns(2)

with c1:
    st.markdown("**🟢 BUY ZONES (Demand)**", unsafe_allow_html=True)
    for z in demand_zones:
        dist = ((live_price - z) / z) * 100
        st.markdown(f"<span class='buy'>**${z:,.2f}** ← HOT ENTRY ({dist:+.1f}%)</span>", unsafe_allow_html=True)

with c2:
    st.markdown("**🔴 SELL ZONES (Supply)**", unsafe_allow_html=True)
    for z in supply_zones:
        dist = ((z - live_price) / live_price) * 100
        st.markdown(f"<span class='sell'>**${z:,.2f}** ← HOT RESISTANCE ({dist:+.1f}%)</span>", unsafe_allow_html=True)

st.markdown("**🟡 HIGH VOLUME NODES** (Jahan sabse zyada trading hui)")
for z in high_vol_zones:
    dist = abs(live_price - z) / live_price * 100
    st.write(f"${z:,.2f} ({dist:.1f}% away)")

# Chart
fig = go.Figure()
fig.add_trace(go.Candlestick(x=recent.index, open=recent['Open'], high=recent['High'],
                            low=recent['Low'], close=recent['Close']))
fig.add_trace(go.Bar(x=recent.index, y=recent['Volume'], name="Volume", opacity=0.5, yaxis="y2"))
fig.update_layout(height=650, template="plotly_dark", title=f"{selected_coin} - Binance Data")
fig.update_layout(yaxis2=dict(overlaying='y', side='right'))
st.plotly_chart(fig, use_container_width=True)
