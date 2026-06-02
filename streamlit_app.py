import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib

st.set_page_config(page_title="H32 RSI Liquidity Bot", layout="wide")

st.title("📊 H32 RSI + Liquidity Bot")
st.subheader("Smart Liquidity + Multi TF RSI System")

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

# Timeframe
tf = st.selectbox("**Main Timeframe**", ["15 Minutes", "1 Hour", "4 Hours", "Daily"], index=1)

# Data Fetch
@st.cache_data(ttl=60)
def get_data(ticker):
    df15 = yf.download(ticker, period="3d", interval="15m")
    df1h = yf.download(ticker, period="15d", interval="1h")
    df4h = yf.download(ticker, period="30d", interval="4h")
    df1d = yf.download(ticker, period="90d", interval="1d")
    return df15, df1h, df4h, df1d

try:
    df15, df1h, df4h, df1d = get_data(ticker)

    for df in [df15, df1h, df4h, df1d]:
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

    live_price = float(df15['Close'].iloc[-1])

    # RSI Calculations
    rsi15 = talib.RSI(df15['Close'], timeperiod=14).iloc[-1]
    rsi1h = talib.RSI(df1h['Close'], timeperiod=14).iloc[-1]
    rsi4h = talib.RSI(df4h['Close'], timeperiod=14).iloc[-1]
    rsi1d = talib.RSI(df1d['Close'], timeperiod=14).iloc[-1]

    # Liquidity Zones (Recent Swing Highs & Lows)
    def get_liquidity_zones(df, window=8):
        low_zone = df['Low'].rolling(window=window).min().tail(5).mean()
        high_zone = df['High'].rolling(window=window).max().tail(5).mean()
        return round(low_zone, 4), round(high_zone, 4)

    demand_low, _ = get_liquidity_zones(df1h)
    _, supply_high = get_liquidity_zones(df1h)

    # Signal Logic
    if rsi1h < 30 and live_price <= demand_low * 1.005:
        signal = "🟢 STRONG BUY (Liquidity Grab)"
        color = "lime"
        reason = "RSI Oversold + Price at Demand Liquidity Zone"
    elif rsi1h > 70 and live_price >= supply_high * 0.995:
        signal = "🔴 STRONG SELL (Liquidity Sweep)"
        color = "red"
        reason = "RSI Overbought + Price at Supply Liquidity Zone"
    else:
        signal = "⭕ NEUTRAL / WAIT"
        color = "orange"
        reason = "No strong liquidity setup right now"

    # UI
    col1, col2 = st.columns([1, 2])
    with col1:
        st.metric(f"{selected_coin} Price", f"${live_price:,.4f}")
    with col2:
        st.markdown(f"<h2 style='color:{color}; text-align:center;'>{signal}</h2>", unsafe_allow_html=True)

    st.info(f"**Reason:** {reason}")

    # Liquidity Display
    st.success(f"**Demand Liquidity Zone:** ${demand_low:,.4f}")
    st.error(f"**Supply Liquidity Zone:** ${supply_high:,.4f}")

    # Multi TF RSI
    st.subheader("Multi-Timeframe RSI")
    rsi_data = {
        "15 Min": rsi15,
        "1 Hour": rsi1h,
        "4 Hour": rsi4h,
        "Daily": rsi1d
    }

    for tf_name, val in rsi_data.items():
        if val <= 30:
            st.markdown(f"**{tf_name}:** <span style='color:lime; font-weight:bold;'>{val:.2f} → Oversold</span>", unsafe_allow_html=True)
        elif val >= 70:
            st.markdown(f"**{tf_name}:** <span style='color:red; font-weight:bold;'>{val:.2f} → Overbought</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"**{tf_name}:** <span style='color:white;'>{val:.2f}</span>", unsafe_allow_html=True)

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df1h.index, open=df1h['Open'], high=df1h['High'],
                                 low=df1h['Low'], close=df1h['Close']))
    fig.update_layout(height=600, template="plotly_dark", 
                      title=f"{selected_coin} - Liquidity View (1H)")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error: {str(e)}")
