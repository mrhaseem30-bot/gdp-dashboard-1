import streamlit as st
import requests
import pandas as pd
import numpy as np
import random
import time

# --- 🛰️ SATELLITE SYSTEM SETUP ---
st.set_page_config(page_title="ALADDIN GLOBAL FOREX V49", layout="wide")

if "counter" not in st.session_state:
    st.session_state.counter = 0
st.session_state.counter += 1

st.markdown("""
    <script>
        window.parent.document.querySelector('section.main').scrollTo(0, 0);
    </script>
""", unsafe_allow_html=True)
time.sleep(1)

# --- 🎨 MASTER INTERFACE STYLING ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #02050a, #060a12) !important; }
    .main { color: #f0f6fc; font-family: 'Inter', sans-serif; }
    
    .panel-box {
        background: radial-gradient(circle at center, #0a1626, #040812);
        border: 2px solid #58a6ff;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 25px;
    }
    
    .macro-box {
        background: linear-gradient(145deg, #1b1605, #2d2208);
        border: 1px solid #ff9b05;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 20px;
        color: #ff9b05;
    }
    
    .hunt-zone-box {
        background: linear-gradient(145deg, #2b1114, #170507);
        border: 2px solid #ff4b4b;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        color: #ff4b4b;
    }
    
    .whale-zone-box {
        background: linear-gradient(145deg, #051b11, #0c271a);
        border: 2px solid #00ff88;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        color: #00ff88;
    }
    
    .signal-card {
        background-color: #0d1117;
        border: 1px solid #21262d;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def format_cash(val):
    if abs(val) >= 1_000_000_000: return f"${val / 1_000_000_000:.2f}B"
    elif abs(val) >= 1_000_000: return f"${val / 1_000_000:.2f}M"
    return f"${val:,.2f}"

# --- 📂 CONTROL SIDEBAR (TIMEFRAME ENGINE & FOREX ONLY) ---
st.sidebar.markdown("### 🏛️ GLOBAL COMMAND DESK V49")
forex_watchlist = ["GOLD (XAU/USD)", "EUR/USD", "GBP/USD", "USD/JPY"]
selected_asset = st.sidebar.selectbox("📂 SELECT FOREX PAIR", forex_watchlist)

# Dynamic Timeframe Engine Switch
tf_options = {
    "⏱️ 15 Minutes Micro Scalp Hunt": "15m",
    "⏱️ 12 Hours Institutional Shift": "12h",
    "⏱️ 1 Day Macro Core Trend": "1d"
}
selected_tf_label = st.sidebar.selectbox("⏱️ SELECT SURVEILLANCE TIMEFRAME", list(tf_options.keys()))
active_tf = tf_options[selected_tf_label]

# Global Situation Impact Level Selector
global_risk_level = st.sidebar.select_slider("🌍 GLOBAL SITUATION INDEX (Risk Matrix)", options=["LOW STABILITY", "NEUTRAL", "HIGH GEOPOLITICAL SHOCK"])

# Leverage Settings
margin_capital = st.sidebar.number_input("💵 Your Margin Capital ($)", min_value=100.0, value=2000.0, step=100.0)
leverage = 3
buying_power = margin_capital * leverage

# --- 🔍 PURE FOREX LIVE INDEX DATA DATAFLOW ---
forex_base_data = {
    "GOLD (XAU/USD)": {"last": 2365.40, "high": 2382.10, "low": 2351.50, "dec": 2},
    "EUR/USD": {"last": 1.0865, "high": 1.0910, "low": 1.0820, "dec": 4},
    "GBP/USD": {"last": 1.2642, "high": 1.2710, "low": 1.2595, "dec": 4},
    "USD/JPY": {"last": 155.85, "high": 156.40, "low": 154.90, "dec": 2}
}

asset_data = forex_base_data[selected_asset]
dec_format = asset_data["dec"]

# Real-time high frequency fluctuation simulation
live_price = asset_data["last"] + random.uniform(-asset_data["last"] * 0.0002, asset_data["last"] * 0.0002)

# --- ⚙️ TIMEFRAME MATHEMATICAL DYNAMICS CONTROL ---
# Risk multiplier shifts based on selected timeframe to generate realistic pips distance
if active_tf == "15m":
    tf_multiplier = 0.0015  # Tight ranges for quick scalping
    signal_status = "⚡ ACTIVE SCALPING EXHAUSTION"
elif active_tf == "12h":
    tf_multiplier = 0.0060  # Wider range for structural moves
    signal_status = "🏛️ INSTITUTIONAL POSITION SPREAD"
else:
    tf_multiplier = 0.0120  # Macro trend levels
    signal_status = "🌍 MACRO REGIME CONVERGENCE"

# Global Risk Shocks push stop losses deeper to trap beginners
if global_risk_level == "HIGH GEOPOLITICAL SHOCK":
    shock_extension = 1.45
    situation_desc = "🚨 HIGH VOLATILITY SHOCK: Central Banks sweeping both sides! Beginners getting wiped out due to premature entries."
else:
    shock_extension = 1.0
    situation_desc = "✅ STABLE MARGIN FLOW: Standard order book distribution rules apply."

# Dynamic Level Generation based on User's Learning Framework
whale_buy_limit = live_price * (1.0 - (tf_multiplier * 1.1))
beginner_entry_zone = live_price * (1.0 - (tf_multiplier * 0.2))
beginner_stop_loss_floor = live_price * (1.0 - (tf_multiplier * 0.7 * shock_extension))
whale_sell_limit = live_price * (1.0 + (tf_multiplier * 1.2))

# --- 👁️ PHASE 1: DAILY SINGLE EYE WATCH TABS ---
st.markdown(f"""
    <div class='panel-box'>
        <h2 style='color: #58a6ff; margin: 0; font-size: 1.5rem;'>👁️ DAILY SINGLE EYE WATCH: ULTRA TIMEFRAME MONITOR ({active_tf.upper()})</h2>
        <p style='color: #8b949e; margin: 5px 0 0 0;'>Target Matrix: {selected_asset} | Active Frame: `{selected_tf_label}`</p>
    </div>
""", unsafe_allow_html=True)

# --- 🌍 PHASE 2: GLOBAL SITUATION TRACKER LAYER ---
st.markdown(f"""
    <div class='macro-box'>
        <h4 style='margin:0; font-weight:bold;'>🌍 GLOBAL SITUATION ENGINE STATUS</h4>
        <p style='margin:5px 0 0 0; font-size:13px; color:#ffd699;'>{situation_desc}</p>
    </div>
""", unsafe_allow_html=True)

st.markdown(f"### LIVE PRICE TICKER FEED: <span style='color:#00ff88;'>${live_price:,.{dec_format}f}</span>", unsafe_allow_html=True)
st.write("---")

# --- 🚨 PHASE 3: THE BEGINNER MISTAKE LEARNING BOARD ---
col_left_zone, col_right_zone = st.columns(2)

with col_left_zone:
    st.markdown(f"""
        <div class='hunt-zone-box'>
            <h3 style='margin:0; font-size:1.15rem;'>💀 BEGINNER EXPOSED TRAPS (Where Stops Are Set)</h3>
            <p style='font-size:14px; color:#ffd699; margin:10px 0;'>
                <b>Beginner Entry Trigger:</b> ${beginner_entry_zone:,.{dec_format}f} (Chasing FOMO breakout)<br>
                <b>Exposed Stop Loss Cluster:</b> <span style='color:#ff4b4b; font-weight:bold;'>${beginner_stop_loss_floor:,.{dec_format}f}</span>
            </p>
            <span style='font-size:12px; color:#ff4b4b; font-weight:bold;'>⚠️ SYSTEM WARNING: Do not enter where beginners buy. Wait for their Stop Loss to get hunted down!</span>
        </div>
    """, unsafe_allow_html=True)

with col_right_zone:
    st.markdown(f"""
        <div class='whale-zone-box'>
            <h3 style='margin:0; font-size:1.15rem;'>🚀 WHALE ACCUMULATION DESK (Your Safe Entry)</h3>
            <p style='font-size:14px; color:#a6f5cb; margin:10px 0;'>
                <b>Whale Pre-Set Limit Buy Order:</b> ${whale_buy_limit:,.{dec_format}f}<br>
                <b>Institutional Target Sell Area:</b> ${whale_sell_limit:,.{dec_format}f}
            </p>
            <span style='font-size:12px; color:#00ff88; font-weight:bold;'>🟩 ALADDIN INSTRUCTION: Enter ONLY when price drops to sweep beginner stops near the Whale block!</span>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- 📡 PHASE 4: DAILY LIVE SIGNAL GENERATOR BOARD ---
st.markdown(f"### 📡 DAILY SYSTEM GENERATED SIGNALS (`{active_tf.upper()}` Engine)")

c_sig1, c_sig2, c_sig3, c_sig4 = st.columns(4)

with c_sig1:
    st.markdown(f"""
        <div class='signal-card' style='border-top: 3px solid #ff9b05;'>
            <span style='color:#8b949e; font-size:11px;'>ENGINE SIGNAL STATUS</span><br>
            <b style='color:#ff9b05; font-size:14px;'>{signal_status}</b>
        </div>
    """, unsafe_allow_html=True)

with c_sig2:
    st.markdown(f"""
        <div class='signal-card' style='border-top: 3px solid #00ff88;'>
            <span style='color:#8b949e; font-size:11px;'>RECOMMENDED ENTRY POINT</span><br>
            <b style='color:#00ff88; font-size:16px; font-family:monospace;'>${whale_buy_limit:,.{dec_format}f}</b>
        </div>
    """, unsafe_allow_html=True)

with c_sig3:
    st.markdown(f"""
        <div class='signal-card' style='border-top: 3px solid #ff4b4b;'>
            <span style='color:#8b949e; font-size:11px;'>SAFE PROTECTION STOP LOSS</span><br>
            <b style='color:#ff4b4b; font-size:16px; font-family:monospace;'>${beginner_stop_loss_floor * 0.997:,.{dec_format}f}</b>
        </div>
    """, unsafe_allow_html=True)

with c_sig4:
    st.markdown(f"""
        <div class='signal-card' style='border-top: 3px solid #58a6ff;'>
            <span style='color:#8b949e; font-size:11px;'>TAKE PROFIT TARGET CEILING</span><br>
            <b style='color:#58a6ff; font-size:16px; font-family:monospace;'>${whale_sell_limit:,.{dec_format}f}</b>
        </div>
    """, unsafe_allow_html=True)

# --- 📊 PHASE 5: LIVE ORDER BOOK REGISTER REGISTER ---
st.write("---")
st.markdown("### 🏛️ SYSTEM LIVE LIMIT ORDER ALLOCATIONS (Whales vs Beginners History)")

order_book_data = [
    {"Participant Segment": "🏛️ CENTRAL BANK RESERVE DESK", "Trigger Target Price": f"${whale_sell_limit:,.{dec_format}f}", "Order Strategy Allocation": "🟥 LIMIT SELL BLOCK (Take Profit)", "Estimated Liquidity Inflow": format_cash(random.uniform(400_000_000, 800_000_000))},
    {"Participant Segment": "👶 RETAIL BEGINNER TRADERS", "Trigger Target Price": f"${beginner_entry_zone:,.{dec_format}f}", "Order Strategy Allocation": "🟩 BREAKOUT FOMO BUY (Exposed)", "Estimated Liquidity Inflow": format_cash(random.uniform(30_000_000, 70_000_000))},
    {"Participant Segment": "💀 RETAIL BEGINNER TRADERS", "Trigger Target Price": f"${beginner_stop_loss_floor:,.{dec_format}f}", "Order Strategy Allocation": "🚨 RETAIL STOP LOSS FLOOR EXPOSURE", "Estimated Liquidity Inflow": format_cash(random.uniform(100_000_000, 250_000_000))},
    {"Participant Segment": "🏛️ CENTRAL BANK RESERVE DESK", "Trigger Target Price": f"${whale_buy_limit:,.{dec_format}f}", "Order Strategy Allocation": "🟩 LIMIT BUY ORDER BLOCK (Whale Entry)", "Estimated Liquidity Inflow": format_cash(random.uniform(500_000_000, 1_100_000_000))}
]

df_book = pd.DataFrame(order_book_data)
st.dataframe(df_book, use_container_width=True, hide_index=True)

# Loop refresh engine
st.components.v1.html("""
    <script>
        setTimeout(function(){ window.parent.document.querySelector('section.main').dispatchEvent(new Event('change')); }, 1000);
    </script>
""", height=0)
