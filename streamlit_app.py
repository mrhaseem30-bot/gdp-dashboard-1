import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib

st.set_page_config(page_title="H32 RSI + Liquidity Bot", layout="wide")

st.title("📊 H32 RSI + Liquidity Bot")
st.subheader("Smart Multi-TF Liquidity + RSI System")

# Coin Selector
coins = {
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Solana (SOL)": "SOL-USD",
    "Sui (SUI)": "SUI-USD",
    "Chainlink (LINK)": "LINK-USD"
}

selected_coin = st.selectbox("**Select Coin**", list(coins.keys()))
ticker = coins[selected_coin]

# ==================== IMPROVED DATA FETCH ====================
@st.cache_data(ttl=120)
def get_data(ticker):
    try:
        df15 = yf.download(ticker, period="7d", interval="15m", progress=False)
        df1h = yf.download(ticker, period="60d", interval="1h", progress=False)
        df4h = yf.download(ticker, period="180d", interval="4h", progress=False)
        df1d = yf.download(ticker, period="1y", interval="1d", progress=False)

        # Clean columns if multi-index
        for df in [df15, df1h, df4h, df1d]:
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

        return df15, df1h, df4h, df1d
    except Exception as e:
        st.error(f"Data fetch error: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df15, df1h, df4h, df1d = get_data(ticker)

# ==================== SAFE LIVE PRICE ====================
if df15.empty or 'Close' not in df15.columns or len(df15) == 0:
    st.error("❌ Unable to fetch data. Please try again later or select another coin.")
    st.stop()

live_price = float(df15['Close'].iloc[-1])

# ==================== RSI CALCULATION ====================
try:
    rsi15 = talib.RSI(df15['Close'], timeperiod=14).iloc[-1]
    rsi1h = talib.RSI(df1h['Close'], timeperiod=14).iloc[-1] if not df1h.empty else None
    rsi4h = talib.RSI(df4h['Close'], timeperiod=14).iloc[-1] if not df4h.empty else None
    rsi1d = talib.RSI(df1d['Close'], timeperiod=14).iloc[-1] if not df1d.empty else None
except:
    rsi15 = rsi1h = rsi4h = rsi1d = None

# ==================== MULTI LIQUIDITY ZONES ====================
def find_swing_highs_lows(df, window=5):
    highs = []
    lows = []
    for i in range(window, len(df) - window):
        if df['High'].iloc[i] == df['High'].iloc[i-window:i+window+1].max():
            highs.append(df['High'].iloc[i])
        if df['Low'].iloc[i] == df['Low'].iloc[i-window:i+window+1].min():
            lows.append(df['Low'].iloc[i])
    return highs, lows

def get_liquidity_zones(df, lookbacks=[20, 60, 200]):
    demand = []
    supply = []
    for lb in lookbacks:
        if len(df) < lb:
            continue
        recent = df.tail(lb)
        highs, lows = find_swing_highs_lows(recent)
        if highs:
            supply.extend(sorted(highs[-5:], reverse=True))
        if lows:
            demand.extend(sorted(lows[-5:]))
    
    demand = sorted(list(set([round(x, 4) for x in demand])))
    supply = sorted(list(set([round(x, 4) for x in supply])))
    return demand, supply

# Get zones from different timeframes
demand_1h, supply_1h = get_liquidity_zones(df1h, [20, 60])
demand_4h, supply_4h = get_liquidity_zones(df4h, [30, 90])
demand_daily, supply_daily = get_liquidity_zones(df1d, [5, 20, 120])

all_demand = sorted(list(set(demand_1h + demand_4h + demand_daily)))
all_supply = sorted(list(set(supply_1h + supply_4h + supply_daily)))

# Near zones
near_demand = [z for z in all_demand if abs(z - live_price) / live_price < 0.018]
near_supply = [z for z in all_supply if abs(z - live_price) / live_price < 0.018]

# ==================== SIGNAL LOGIC ====================
if rsi1h and rsi1h < 32 and near_demand:
    signal = "🟢 STRONG BUY (Liquidity Grab)"
    color = "lime"
elif rsi1h and rsi1h > 68 and near_supply:
    signal = "🔴 STRONG SELL (Liquidity Sweep)"
    color = "red"
else:
    signal = "⭕ NEUTRAL / WAIT"
    color = "orange"

# ==================== UI ====================
col1, col2 = st.columns([1, 2])
with col1:
    st.metric(f"{selected_coin} Price", f"${live_price:,.4f}")
with col2:
    st.markdown(f"<h2 style='color:{color}; text-align:center;'>{signal}</h2>", unsafe_allow_html=True)

st.info(f"**Reason:** RSI + Price near Liquidity Zone")

# Liquidity Zones Display
st.subheader("🔍 Multi-Timeframe Liquidity Zones")

col_d, col_s = st.columns(2)
with col_d:
    st.success("**Demand Zones (Support)**")
    for z in all_demand[-8:]:
        dist = ((live_price - z) / z) * 100
        st.write(f"${z:,.4f}  →  {dist:+.2f}%")

with col_s:
    st.error("**Supply Zones (Resistance)**")
    for z in all_supply[-8:]:
        dist = ((z - live_price) / live_price) * 100
        st.write(f"${z:,.4f}  →  {dist:+.2f}%")

# Multi TF RSI
st.subheader("Multi-Timeframe RSI")
if rsi15: st.write(f"**15 Min:** {rsi15:.2f}")
if rsi1h: st.write(f"**1 Hour:** {rsi1h:.2f}")
if rsi4h: st.write(f"**4 Hour:** {rsi4h:.2f}")
if rsi1d: st.write(f"**Daily:** {rsi1d:.2f}")

# Chart
if not df1h.empty:
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df1h.index, open=df1h['Open'], high=df1h['High'],
                                 low=df1h['Low'], close=df1h['Close'], name="1H"))
    fig.update_layout(height=600, template="plotly_dark", title=f"{selected_coin} - 1H Chart")
    st.plotly_chart(fig, use_container_width=True)
