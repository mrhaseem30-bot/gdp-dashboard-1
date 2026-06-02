import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import talib

st.set_page_config(page_title="H32 Compound Trend Bot", layout="wide")

st.title("⚡ H32 Compound Trend Bot")
st.subheader("SuperTrend + EMA Strategy")

# Coin Selector
coins = {
    "Bitcoin (BTC)": "BTC-USD",
    "Ethereum (ETH)": "ETH-USD",
    "Solana (SOL)": "SOL-USD",
    "Sui (SUI)": "SUI-USD",
    "Chainlink (LINK)": "LINK-USD"
}

selected_coin = st.selectbox("Select Coin", list(coins.keys()))
ticker = coins[selected_coin]

# Timeframe
timeframe = st.selectbox("Select Timeframe", 
    ["15 Minutes", "1 Hour", "4 Hours", "Daily"], index=1)

# Settings
if timeframe == "15 Minutes":
    period, mult, days, interval = 10, 2.5, "2d", "15m"
elif timeframe == "1 Hour":
    period, mult, days, interval = 10, 3.0, "15d", "1h"
elif timeframe == "4 Hours":
    period, mult, days, interval = 11, 3.0, "30d", "4h"
else:
    period, mult, days, interval = 10, 3.0, "90d", "1d"

@st.cache_data(ttl=60)
def get_data(ticker, days, interval):
    return yf.download(ticker, period=days, interval=interval)

try:
    df = get_data(ticker, days, interval)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    live_price = float(df['Close'].iloc[-1])

    # Indicators
    df['EMA20'] = talib.EMA(df['Close'], timeperiod=20)
    df['EMA50'] = talib.EMA(df['Close'], timeperiod=50)

    hl2 = (df['High'] + df['Low']) / 2
    atr = talib.ATR(df['High'], df['Low'], df['Close'], timeperiod=period)
    df['SuperTrend'] = hl2 + (mult * atr)

    # Signal
    last = df.iloc[-1]
    ema_bull = last['EMA20'] > last['EMA50']
    price_above = live_price > last['SuperTrend']

    if ema_bull and price_above:
        signal = "STRONG BUY"
        color = "lime"
        reason = "EMA Bullish + Price above SuperTrend"
    elif not ema_bull and not price_above:
        signal = "STRONG SELL"
        color = "red"
        reason = "EMA Bearish + Price below SuperTrend"
    else:
        signal = "WAIT"
        color = "orange"
        reason = "Mixed Signals - Wait"

    # Display
    col1, col2 = st.columns([1,2])
    with col1:
        st.metric(f"{selected_coin}", f"${live_price:,.4f}")
    with col2:
        st.markdown(f"<h2 style='color:{color}; text-align:center;'>{signal}</h2>", unsafe_allow_html=True)

    st.info(f"**Reason:** {reason}")

    # Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                 low=df['Low'], close=df['Close']))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA20'], name="EMA20", line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=df.index, y=df['EMA50'], name="EMA50", line=dict(color='blue')))
    fig.add_trace(go.Scatter(x=df.index, y=df['SuperTrend'], name="SuperTrend", line=dict(color='violet', width=3)))

    fig.update_layout(height=650, template="plotly_dark", 
                      title=f"{selected_coin} - {timeframe}")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error: {str(e)}")
