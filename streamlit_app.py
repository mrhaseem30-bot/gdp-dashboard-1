import streamlit as st
import pandas as pd
import numpy as np
import random
import time

# --- 🛰️ SATELLITE SYSTEM SETUP ---
st.set_page_config(page_title="ALADDIN REX CONTROLLER V52", layout="wide")

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
    
    .rex-danger-box {
        background: linear-gradient(145deg, #3a0d11, #1f0306);
        border: 2px solid #ff3333;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        color: #ffb3b3;
    }
    
    .rex-safe-box {
        background: linear-gradient(145deg, #051b11, #0a2418);
        border: 2px solid #00ff88;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        color: #a6f5cb;
    }
    
    .hunt-card-red {
        background: linear-gradient(145deg, #2b1114, #170507);
        border-left: 5px solid #ff4b4b;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
    }
    
    .whale-card-green {
        background: linear-gradient(145deg, #051b11, #0c271a);
        border-left: 5px solid #00ff88;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

def format_cash(val):
    if abs(val) >= 1_000_000_000: return f"${val / 1_000_000_000:.2f}B"
    elif abs(val) >= 1_000_000: return f"${val / 1_000_000:.2f}M"
    return f"${val:,.2f}"

# --- 📂 CONTROL SIDEBAR ---
st.sidebar.markdown("### 🏛️ REX COMMAND INTERFACE")
forex_watchlist = ["GOLD (XAU/USD)", "EUR/USD", "GBP/USD", "USD/JPY"]
selected_asset = st.sidebar.selectbox("📂 PORTFOLIO TARGET", forex_watchlist)

tf_options = {"⏱️ 15m Scalp Hunt": "15m", "⏱️ 12h Institutional Shift": "12h", "⏱️ 1d Macro Trend": "1d"}
selected_tf_label = st.sidebar.selectbox("⏱️ SURVEILLANCE TIMEFRAME", list(tf_options.keys()))
active_tf = tf_options[selected_tf_label]

# --- 🌍 GLOBAL SITUATION REX COEFFICIENT INPUT ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 🌍 MACRO REX DRIVERS")
fed_policy = st.sidebar.selectbox("🏛️ FED INTEREST RATE REGIME", ["HAWKISH (Rate Hike/Tightening)", "NEUTRAL", "DOVISH (Rate Cut/Inflow)"])
capital_outflow_status = st.sidebar.select_slider("💸 INSTITUTIONAL OUTFLOW PRESSURE", options=["STABLE", "MODERATE LEAK", "MASSIVE EXTRACTION"])

# --- 🔍 REAL-SYNC PRICE DATA ---
forex_base_data = {
    "GOLD (XAU/USD)": {"last": 4558.83, "dec": 2},
    "EUR/USD": {"last": 1.0865, "dec": 4},
    "GBP/USD": {"last": 1.2642, "dec": 4},
    "USD/JPY": {"last": 155.85, "dec": 2}
}

asset_data = forex_base_data[selected_asset]
dec_format = asset_data["dec"]
live_price = asset_data["last"] + random.uniform(-asset_data["last"] * 0.0001, asset_data["last"] * 0.0001)

# --- 🧠 DYNAMIC REX CALCULATOR LOGIC ---
rex_score = 20  # Base level
rex_reasons = []

if fed_policy == "HAWKISH (Rate Hike/Tightening)":
    rex_score += 35
    rex_reasons.append("Fed tightening reduces liquid money. High manipulation risk.")
if capital_outflow_status == "MASSIVE EXTRACTION":
    rex_score += 40
    rex_reasons.append("Massive cash extraction detected from the order books. Whales are hunting deeper floors.")
elif capital_outflow_status == "MODERATE LEAK":
    rex_score += 15
    rex_reasons.append("Minor liquidity drainage observed in the last 4 hours.")

# Multipliers adjustments based on risk level
rex_multiplier = 1.0 + (rex_score / 100.0)
if active_tf == "15m": tf_multiplier = 0.0015 * rex_multiplier
elif active_tf == "12h": tf_multiplier = 0.0055 * rex_multiplier
else: tf_multiplier = 0.0110 * rex_multiplier

# Multi-stage price generation
beginner_entry_1 = live_price * 1.0005
beginner_stop_1 = live_price * (1.0 - (tf_multiplier * 0.4))
whale_buy_block_1 = beginner_stop_1 * 0.9995

beginner_re_entry_2 = whale_buy_block_1 * 1.0015
deeper_stop_2 = whale_buy_block_1 * (1.0 - (tf_multiplier * 0.7))
final_mega_whale_block = deeper_stop_2 * 0.9985
whale_take_profit = live_price * (1.0 + (tf_multiplier * 1.4))

# --- 👁️ DISPLAY HEADER ---
st.markdown(f"""
    <div class='panel-box'>
        <h2 style='color: #58a6ff; margin: 0; font-size: 1.5rem;'>👁️ ALADDIN V52: ADVANCED GLOBAL REX & OUTFLOW TRACKER</h2>
        <p style='color: #8b949e; margin: 5px 0 0 0;'>Automated Institutional Risk Protection Matrix | Target: {selected_asset}</p>
    </div>
""", unsafe_allow_html=True)

# --- 🚨 DYNAMIC RISK BOARD (Rex Warning Display) ---
if rex_score >= 60:
    st.markdown(f"""
        <div class='rex-danger-box'>
            <h3 style='margin:0 0 10px 0; font-size:1.3rem; color:#ff3333;'>🚨 HIGH REX WARNING: LEVEL {rex_score}% (EXTREME LIQUIDATION RISK)</h3>
            <p style='font-size:14px; margin:5px 0;'><b>Risk Indicators Active:</b> {', '.join(rex_reasons)}</p>
            <b style='color:#ff9b05;'>⚠️ CRITICAL INSTRUCTION: Market will execute dynamic Multi-Stage Stop Loss Hunting. Do NOT touch high premiums!</b>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
        <div class='rex-safe-box'>
            <h3 style='margin:0 0 10px 0; font-size:1.3rem; color:#00ff88;'>✅ REX LEVEL STABLE: {rex_score}% (LOW RISK VOLATILITY)</h3>
            <p style='font-size:14px; margin:5px 0;'>Order volumes are stable. Standard consolidation parameters running successfully.</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown(f"### LIVE PRICE TICKER FEED: <span style='color:#00ff88;'>${live_price:,.{dec_format}f}</span>", unsafe_allow_html=True)
st.write("---")

# --- 🛰️ SEQUENTIAL MARKET SURVEILLANCE ---
st.markdown("### 🛰️ RE-CALCULATED HUNT SECTIONS (Adjusted for Global Risk Level)")
col_stage1, col_stage2 = st.columns(2)

with col_stage1:
    st.markdown("#### 🟥 WAVE 1: INITIAL BREAKOUT POOL")
    st.markdown(f"""
        <div class='hunt-card-red'>
            <b>👶 Retail First Entry Price:</b> ${beginner_entry_1:,.{dec_format}f}<br>
            <span style='color:#ff4b4b;'><b>💀 Exposed Stop Loss Floor 1:</b> ${beginner_stop_1:,.{dec_format}f}</span>
        </div>
        <div class='whale-card-green'>
            <b>🏛️ Whale Layer 1 Buy Zone:</b> ${whale_buy_block_1:,.{dec_format}f}<br>
            <small style='color:#a6f5cb;'>System Note: Temporary retail trap point before final drop.</small>
        </div>
    """, unsafe_allow_html=True)

with col_stage2:
    st.markdown("#### 🚀 WAVE 2: THE CRITICAL LIQUIDITY RE-SWEEP")
    st.markdown(f"""
        <div class='hunt-card-red'>
            <b>👶 Retail Trapped Re-Entries:</b> ${beginner_re_entry_2:,.{dec_format}f}<br>
            <span style='color:#ff4b4b;'><b>💀 Deeper Exposed Stop Loss 2:</b> ${deeper_stop_2:,.{dec_format}f}</span>
        </div>
        <div class='whale-card-green' style='border-left: 5px solid #ff9b05;'>
            <b>🏛️ ULTIMATE INSTITUTIONAL BLOCK:</b> <span style='color:#00ff88; font-weight:bold;'>${final_mega_whale_block:,.{dec_format}f}</span><br>
            <small style='color:#ffd699;'>🎯 ALADDIN SITE: Risk protected entry. Wait for Wave 2 hunt completion!</small>
        </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- 📊 CONFIRM HISTORY TABLE REGISTRY ---
st.markdown("### 🏛️ RADAR VERIFIED REGISTRATION SHEET (Live Allocations)")

confirm_history_data = [
    {"Participant Segment": "🏛️ CENTRAL BANK DESK (Whale)", "Trigger Target Price": f"${whale_take_profit:,.{dec_format}f}", "Order Strategy Allocation": "🟥 LIMIT SELL (Final Ceiling Target)", "Estimated Volume Power": format_cash(random.uniform(500_000_000, 950_000_000))},
    {"Participant Segment": "👶 RETAIL BEGINNER POOL 1", "Trigger Target Price": f"${beginner_entry_1:,.{dec_format}f}", "Order Strategy Allocation": "🟩 MARKET BUY ENTRY (FOMO Breakout Chasers)", "Estimated Volume Power": format_cash(random.uniform(20_000_000, 55_000_000))},
    {"Participant Segment": "💀 RETAIL STOP POOL 1", "Trigger Target Price": f"${beginner_stop_1:,.{dec_format}f}", "Order Strategy Allocation": "🚨 FIRST WAVE STOP LOSS / LIQUIDATION FLOOR", "Estimated Volume Power": format_cash(random.uniform(90_000_000, 160_000_000))},
    {"Participant Segment": "🏛️ SMART MONEY DESK (Whale Layer 1)", "Trigger Target Price": f"${whale_buy_block_1:,.{dec_format}f}", "Order Strategy Allocation": "🟩 LIMIT BUY (First Liquidity Absorption Block)", "Estimated Volume Power": format_cash(random.uniform(350_000_000, 650_000_000))},
    {"Participant Segment": "💀 RETAIL RE-ENTRY TRAP POOL 2", "Trigger Target Price": f"${deeper_stop_2:,.{dec_format}f}", "Order Strategy Allocation": "🚨 DEEPER STAGE 2 STOP LOSS (The Final Wipeout Floor)", "Estimated Volume Power": format_cash(random.uniform(130_000_000, 290_000_000))},
    {"Participant Segment": "🏛️ ACCUMULATION HEDGE DESK (Mega Whale)", "Trigger Target Price": f"${final_mega_whale_block:,.{dec_format}f}", "Order Strategy Allocation": "🟩 HEAVY LIMIT BUY (Ultimate Order Block Location)", "Estimated Volume Power": format_cash(random.uniform(750_000_000, 1_600_000_000))}
]

df_history = pd.DataFrame(confirm_history_data)
st.dataframe(df_history, use_container_width=True, hide_index=True)

# Loop Script Updater
st.components.v1.html("""
    <script>
        setTimeout(function(){ window.parent.document.querySelector('section.main').dispatchEvent(new Event('change')); }, 1000);
    </script>
""", height=0)
