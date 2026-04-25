import streamlit as st
import time
import json
import random
import base64
from datetime import datetime
from dataclasses import asdict
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Wearable AI Intelligence Engine",
    page_icon="⌚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
    /* Global Dark Theme */
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Neon Colors */
    :root {
        --neon-green: #00E676;
        --neon-yellow: #FFEA00;
        --neon-red: #FF1744;
    }

    /* Animations */
    @keyframes pulse-red {
        0% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0.7); }
        70% { box-shadow: 0 0 0 20px rgba(255, 23, 68, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 23, 68, 0); }
    }
    
    @keyframes shake {
        0% { transform: translate(1px, 1px) rotate(0deg); }
        10% { transform: translate(-1px, -2px) rotate(-1deg); }
        20% { transform: translate(-3px, 0px) rotate(1deg); }
        30% { transform: translate(3px, 2px) rotate(0deg); }
        40% { transform: translate(1px, -1px) rotate(1deg); }
        50% { transform: translate(-1px, 2px) rotate(-1deg); }
        60% { transform: translate(-3px, 1px) rotate(0deg); }
        70% { transform: translate(3px, 1px) rotate(-1deg); }
        80% { transform: translate(-1px, -1px) rotate(1deg); }
        90% { transform: translate(1px, 2px) rotate(0deg); }
        100% { transform: translate(1px, -2px) rotate(-1deg); }
    }

    .pulse-emergency {
        animation: pulse-red 1.5s infinite;
        border: 4px solid var(--neon-red) !important;
    }
    
    .shake-emergency {
        animation: shake 0.5s infinite;
    }

    /* Watch Face Container */
    .watch-face {
        width: 320px;
        height: 320px;
        background: radial-gradient(circle at center, #1E232D 0%, #000000 100%);
        border-radius: 50%;
        border: 10px solid #333;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        position: relative;
        box-shadow: 0 0 30px rgba(0,0,0,0.5);
    }
    
    .watch-hr { font-size: 4rem; font-weight: 800; margin: 0; }
    .watch-label { font-size: 1rem; color: #888; text-transform: uppercase; letter-spacing: 2px; }
    
    /* User View Cards */
    .user-card {
        background-color: #1E232D;
        padding: 40px;
        border-radius: 25px;
        text-align: center;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Hide default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# SECTION 2 — SESSION STATE SETUP
# ═══════════════════════════════════════════════════════════

def init_session_state():
    defaults = {
        # Simulation control
        "sim_running": False,
        "sim_mode": "normal",          # "normal" | "stress" | "emergency"
        "sim_cycle": 0,
        
        # Previous sensor values (for smooth transitions)
        "prev_hr": 72.0,
        "prev_spo2": 98.0,
        "prev_gsr": 2.4,
        "prev_temp": 36.6,
        "prev_accel": 0.45,
        
        # Latest pipeline outputs
        "sensor_data": None,
        "profiler_output": None,
        "action_output": None,
        
        # History for charts (last 30 points each)
        "hr_history": [72.0] * 30,
        "spo2_history": [98.0] * 30,
        "gsr_history": [2.4] * 30,
        "temp_history": [36.6] * 30,
        
        # Agent trace log (last 10 entries)
        "agent_trace": [],
        
        # Fallback flag
        "using_fallback": False,
        
        # Countdown for emergency
        "emergency_countdown": 5,
        
        # App UI states
        "acknowledged": False,
        "calling": False,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

# ═══════════════════════════════════════════════════════════
# SECTION 3 — SENSOR DATA GENERATOR
# ═══════════════════════════════════════════════════════════

import math

def generate_sensor_data(mode: str) -> dict:
    """
    Generates one frame of realistic wearable sensor data.
    Uses previous st.session_state values for smooth transitions.
    LERP factor 0.15 = gradual drift, not instant jumps.
    """
    
    # Target ranges per mode
    targets = {
        "normal": {
            "hr": 72,        # resting heart rate
            "spo2": 98.2,    # healthy blood oxygen
            "gsr": 2.4,      # low galvanic skin response
            "temp": 36.6,    # normal skin temp
            "accel": 0.45,   # moderate movement
        },
        "stress": {
            "hr": 108,       # elevated HR
            "spo2": 96.8,    # slightly reduced O2
            "gsr": 7.2,      # high stress conductance
            "temp": 37.1,    # slightly elevated temp
            "accel": 0.08,   # near-still (sitting, tense)
        },
        "emergency": {
            "hr": 134,       # dangerously high
            "spo2": 93.5,    # critically low oxygen
            "gsr": 13.8,     # extreme stress response
            "temp": 38.7,    # elevated body temp
            "accel": 0.02,   # completely still
        }
    }
    
    t = targets[mode]
    lerp = lambda prev, target, factor: prev + (target - prev) * factor
    
    # Noise per sensor (realistic jitter)
    noise = {
        "hr":    random.gauss(0, 2.5),     # ±2.5 BPM natural variability
        "spo2":  random.gauss(0, 0.3),     # ±0.3% measurement noise
        "gsr":   random.gauss(0, 0.4),     # ±0.4μS skin conductance
        "temp":  random.gauss(0, 0.08),    # ±0.08°C sensor noise
        "accel": random.gauss(0, 0.03),    # ±0.03 g movement jitter
    }
    
    # Smooth interpolation from previous values
    hr    = lerp(st.session_state.prev_hr,    t["hr"],    0.18) + noise["hr"]
    spo2  = lerp(st.session_state.prev_spo2,  t["spo2"],  0.12) + noise["spo2"]
    gsr   = lerp(st.session_state.prev_gsr,   t["gsr"],   0.15) + noise["gsr"]
    temp  = lerp(st.session_state.prev_temp,  t["temp"],  0.10) + noise["temp"]
    accel = lerp(st.session_state.prev_accel, t["accel"], 0.20) + abs(noise["accel"])
    
    # Clamp to physiologically valid ranges
    hr    = max(40, min(200, hr))
    spo2  = max(85, min(100, spo2))
    gsr   = max(0.1, min(25.0, gsr))
    temp  = max(35.0, min(42.0, temp))
    accel = max(0.0, min(3.0, accel))
    
    # Store for next frame's LERP
    st.session_state.prev_hr    = hr
    st.session_state.prev_spo2  = spo2
    st.session_state.prev_gsr   = gsr
    st.session_state.prev_temp  = temp
    st.session_state.prev_accel = accel
    
    # Build output dict
    data = {
        "hr":           round(hr, 1),
        "spo2":         round(spo2, 1),
        "gsr":          round(gsr, 2),
        "temp":         round(temp, 1),
        "accel":        round(accel, 3),
        "battery":      st.session_state.get("battery", 78),
        "mode":         mode,
        "cycle":        st.session_state.sim_cycle,
        "timestamp":    datetime.now().isoformat(),
        # Derived flags (used by agents)
        "hr_critical":  hr > 120,
        "spo2_low":     spo2 < 95,
        "is_still":     accel < 0.05,
        "temp_high":    temp > 38.0,
    }
    
    # Append to history (rolling window of 30)
    for key in ["hr", "spo2", "gsr", "temp"]:
        history_key = f"{key}_history"
        st.session_state[history_key].append(data[key])
        if len(st.session_state[history_key]) > 30:
            st.session_state[history_key].pop(0)
    
    return data

# ═══════════════════════════════════════════════════════════
# SECTION 4 — PROFILER AGENT (with fallback)
# ═══════════════════════════════════════════════════════════

def profiler_agent(data: dict) -> dict:
    """
    Analyzes sensor data to classify user state.
    Falls back to rule-based logic if LLM fails.
    """
    
    prompt = f"""
You are a wearable AI profiler. Analyze this sensor data and 
return ONLY valid JSON. No explanation, no markdown, no preamble.

SENSOR DATA:
- Heart Rate: {data['hr']} BPM
- Blood Oxygen: {data['spo2']}%
- GSR (stress): {data['gsr']} μS
- Skin Temp: {data['temp']}°C
- Accelerometer: {data['accel']} g
- Battery: {data['battery']}%
- Mode hint: {data['mode']}
- HR Critical: {data['hr_critical']}
- SpO2 Low: {data['spo2_low']}
- User Still: {data['is_still']}

Return this exact JSON structure:
{{
  "state_label": "string (e.g. 'Deep Sleep', 'Job Interview', 'Active Commute', 'Cardiac Event')",
  "confidence": float between 0.0 and 1.0,
  "environment": "indoor|outdoor|vehicle|unknown",
  "social_context": "alone|meeting|public|emergency",
  "interruption_cost": "LOW|MEDIUM|HIGH|CRITICAL",
  "reasoning": ["line 1", "line 2", "line 3"]
}}
"""
    
    try:
        # Since we don't have an actual LLM client in this script directly matching the payload,
        # we trigger fallback for the demo.
        raise Exception("LLM Client unavailable")
    except Exception as e:
        # FALLBACK: Rule-based classification
        st.session_state.using_fallback = True
        return _profiler_fallback(data)

def _profiler_fallback(data: dict) -> dict:
    """
    Rule-based profiler. Activates when LLM is unavailable.
    Deterministic, fast, always works.
    """
    hr = data["hr"]
    spo2 = data["spo2"]
    accel = data["accel"]
    gsr = data["gsr"]
    
    # Classify state
    if hr > 125 and accel < 0.05 and spo2 < 95:
        label = "Anomalous Cardiac Event"
        social = "emergency"
        cost = "LOW"         # Low cost to interrupt — must act
        confidence = 0.95
        reasoning = [
            f"HR {hr:.0f} BPM exceeds critical threshold (125)",
            f"Accelerometer {accel:.3f}g — user completely still",
            f"SpO2 {spo2:.1f}% below safe limit (95%)",
        ]
    elif hr > 95 and gsr > 5.0 and accel < 0.15:
        label = "High-Stress Situation"
        social = "meeting"
        cost = "HIGH"
        confidence = 0.82
        reasoning = [
            f"HR {hr:.0f} BPM elevated above baseline",
            f"GSR {gsr:.1f}μS indicates high arousal",
            f"Near-stillness suggests seated, engaged activity",
        ]
    else:
        label = "Normal Activity"
        social = "alone"
        cost = "MEDIUM"
        confidence = 0.91
        reasoning = [
            f"HR {hr:.0f} BPM within normal resting range",
            f"GSR {gsr:.1f}μS — baseline stress levels",
            f"Movement pattern consistent with regular activity",
        ]
    
    return {
        "state_label": label,
        "confidence": confidence,
        "environment": "indoor",
        "social_context": social,
        "interruption_cost": cost,
        "reasoning": reasoning,
    }

# ═══════════════════════════════════════════════════════════
# SECTION 5 — ACTION AGENT (with fallback)
# ═══════════════════════════════════════════════════════════

def action_agent(profile: dict, data: dict) -> dict:
    """
    Decides whether to interrupt the user or stay silent.
    This is the core intelligence of the system.
    """
    
    prompt = f"""
You are a wearable AI action engine. Given the user profile below,
decide the action. Return ONLY valid JSON. No explanation.

USER PROFILE:
- State: {profile['state_label']}
- Confidence: {profile['confidence']}
- Social context: {profile['social_context']}
- Interruption cost: {profile['interruption_cost']}
- Reasoning: {profile['reasoning']}

RAW SENSORS:
- HR: {data['hr']} BPM (critical: {data['hr_critical']})
- SpO2: {data['spo2']}% (low: {data['spo2_low']})
- Battery: {data['battery']}%
- Is still: {data['is_still']}

Return this exact JSON structure:
{{
  "decision": "SUPPRESS|INTERRUPT",
  "action_type": "silent_log|notify|vibrate|emergency_call",
  "urgency": float between 0.0 and 1.0,
  "override_flag": "NONE|SOCIAL_OVERRIDE|NAV_OVERRIDE|EMERGENCY_OVERRIDE",
  "reasoning_steps": ["step 1", "step 2", "step 3", "step 4"],
  "message_to_user": "string shown to user if interrupted"
}}
"""
    
    try:
        raise Exception("LLM Client unavailable")
    except Exception as e:
        st.session_state.using_fallback = True
        return _action_fallback(profile, data)

def _action_fallback(profile: dict, data: dict) -> dict:
    """
    Rule-based action engine. Always produces valid output.
    """
    cost = profile["interruption_cost"]
    social = profile["social_context"]
    hr_crit = data["hr_critical"]
    spo2_low = data["spo2_low"]
    
    # Emergency: always interrupt
    if social == "emergency" or (hr_crit and spo2_low):
        return {
            "decision": "INTERRUPT",
            "action_type": "emergency_call",
            "urgency": 0.97,
            "override_flag": "EMERGENCY_OVERRIDE",
            "reasoning_steps": [
                "HR + SpO2 combination indicates medical emergency",
                "User is completely still — not exertion-related",
                "No social context that prevents interruption",
                "Emergency protocol triggered immediately",
            ],
            "message_to_user": "Critical heart activity detected. Calling emergency services.",
        }
    
    # High social cost: suppress
    if cost in ("HIGH", "CRITICAL") and not hr_crit:
        return {
            "decision": "SUPPRESS",
            "action_type": "silent_log",
            "urgency": 0.18,
            "override_flag": "SOCIAL_OVERRIDE",
            "reasoning_steps": [
                f"Interruption cost is {cost} — social situation detected",
                "No life-threatening sensor readings present",
                "Logging event silently to history",
                "Will escalate if readings worsen",
            ],
            "message_to_user": "",
        }
    
    # Stress: notify gently
    if profile["confidence"] > 0.7 and data["hr"] > 90:
        return {
            "decision": "INTERRUPT",
            "action_type": "notify",
            "urgency": 0.45,
            "override_flag": "NONE",
            "reasoning_steps": [
                f"HR {data['hr']:.0f} elevated but not critical",
                "Stress markers detected — user may benefit from guidance",
                "Interruption cost is acceptable",
                "Gentle notification appropriate",
            ],
            "message_to_user": "Elevated stress detected. Try taking a slow breath.",
        }
    
    # Default: suppress and log
    return {
        "decision": "SUPPRESS",
        "action_type": "silent_log",
        "urgency": 0.08,
        "override_flag": "NONE",
        "reasoning_steps": [
            "All biometrics within normal range",
            "No action required",
            "Continuing silent monitoring",
            "Next evaluation in 1 second",
        ],
        "message_to_user": "",
    }

# ═══════════════════════════════════════════════════════════
# SECTION 6 — SIMULATION CONTROLLER
# ═══════════════════════════════════════════════════════════

def run_simulation_cycle():
    """
    Executes one full pipeline cycle.
    Called every render when sim_running is True.
    """
    mode = st.session_state.sim_mode
    
    # Step 1: Generate sensor data
    sensor_data = generate_sensor_data(mode)
    
    # Step 2: Run Profiler Agent
    profiler_output = profiler_agent(sensor_data)
    
    # Step 3: Run Action Agent
    action_output = action_agent(profiler_output, sensor_data)
    
    # Step 4: Store results in session state
    st.session_state.sensor_data = sensor_data
    st.session_state.profiler_output = profiler_output
    st.session_state.action_output = action_output
    st.session_state.sim_cycle += 1
    
    # Step 5: Update agent trace log
    trace_entry = {
        "cycle": st.session_state.sim_cycle,
        "time": sensor_data["timestamp"],
        "hr": sensor_data["hr"],
        "decision": action_output["decision"],
        "urgency": action_output["urgency"],
        "state": profiler_output["state_label"],
        "override": action_output["override_flag"],
    }
    st.session_state.agent_trace.insert(0, trace_entry)
    st.session_state.agent_trace = st.session_state.agent_trace[:10]
    
    return sensor_data, profiler_output, action_output

def render_header():
    # Only show emergency sound when necessary
    decision = st.session_state.action_output or {}
    decision_val = decision.get("decision", "--")
    urgency = decision.get("urgency", 0.0)
    
    if decision_val == "INTERRUPT" and urgency > 0.9 and not st.session_state.acknowledged:
        st.markdown("""
            <audio autoplay loop>
                <source src="https://www.soundjay.com/buttons/beep-07.mp3" type="audio/mpeg">
            </audio>
        """, unsafe_allow_html=True)
    
    st.title("Wearable AI Intelligence Engine")
    
def render_controls():
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("▶ Run Simulation", type="primary", 
                     disabled=st.session_state.sim_running):
            st.session_state.sim_running = True
            st.session_state.sim_cycle = 0
            st.session_state.acknowledged = False
            st.session_state.calling = False
            st.rerun()
    
    with col2:
        if st.button("⏹ Stop", 
                     disabled=not st.session_state.sim_running):
            st.session_state.sim_running = False
            st.rerun()
    
    with col3:
        mode = st.selectbox(
            "Simulation Mode",
            options=["normal", "stress", "emergency"],
            index=["normal","stress","emergency"].index(
                st.session_state.sim_mode
            ),
            key="mode_select",
            disabled=st.session_state.sim_running,
            label_visibility="collapsed",
        )
        if mode != st.session_state.sim_mode:
            st.session_state.sim_mode = mode
            st.session_state.acknowledged = False
            st.session_state.calling = False

def render_sensors():
    data     = st.session_state.sensor_data     or {}
    decision = st.session_state.action_output   or {}
    
    decision_val   = decision.get("decision",         "--")
    action_type    = decision.get("action_type",      "--")
    urgency        = decision.get("urgency",          0.0)
    override       = decision.get("override_flag",    "NONE")
    
    st.divider()
    
    # Cycle counter (proves it's live)
    st.caption(f"Cycle #{st.session_state.sim_cycle} · "
               f"Mode: {st.session_state.sim_mode.upper()}")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("❤️ Heart Rate",  f"{data.get('hr','--')} BPM",
                delta=f"{data.get('hr',72)-72:+.1f}" if data else None)
    col2.metric("🫁 SpO₂",        f"{data.get('spo2','--')}%")
    col3.metric("⚡ GSR",         f"{data.get('gsr','--')} μS")
    col4.metric("🌡️ Temp",        f"{data.get('temp','--')}°C")
    
    # Decision banner
    if decision_val == "INTERRUPT":
        st.error(f"🚨 INTERRUPT — {action_type.upper()} | Urgency: {urgency:.2f}")
    elif decision_val == "SUPPRESS":
        st.info(f"👁 SUPPRESS — {override} | Urgency: {urgency:.2f}")

def render_agents():
    # We will use the existing tabs format for User View and Advanced Debug
    tab_user, tab_advanced, tab_watch = st.tabs(["👤 USER VIEW", "🧪 ADVANCED DEBUG", "⌚ WATCH MODE"])
    
    data     = st.session_state.sensor_data     or {}
    profile  = st.session_state.profiler_output or {}
    decision = st.session_state.action_output   or {}
    
    state_label    = profile.get("state_label",       "Waiting...")
    confidence     = profile.get("confidence",        0.0)
    int_cost       = profile.get("interruption_cost", "--")
    p_reasoning    = profile.get("reasoning",         [])
    
    decision_val   = decision.get("decision",         "--")
    action_type    = decision.get("action_type",      "--")
    urgency        = decision.get("urgency",          0.0)
    override       = decision.get("override_flag",    "NONE")
    steps          = decision.get("reasoning_steps",  [])
    msg            = decision.get("message_to_user",  "")
    
    # --- 👤 USER VIEW ---
    with tab_user:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if decision_val == "INTERRUPT" and urgency > 0.9:
            st.markdown(f"""
                <div class='user-card' style='border: 4px solid var(--neon-red);'>
                    <h1 style='color:var(--neon-red); font-size:4rem;'>🚨 Something is wrong</h1>
                    <p style='font-size:1.5rem;'>{msg or 'We detected an unusual heart rate pattern.'}</p>
                </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1: 
                if st.button("📞 CALL FOR HELP", use_container_width=True, type="primary"):
                    st.session_state.calling = True
            with c2: 
                if st.button("✅ I'M OKAY", use_container_width=True):
                    st.session_state.acknowledged = True
        elif decision_val == "INTERRUPT":
            st.markdown(f"""
                <div class='user-card' style='border: 4px solid var(--neon-yellow);'>
                    <h1 style='color:var(--neon-yellow);'>You seem stressed</h1>
                    <p style='font-size:1.2rem;'>{msg}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class='user-card'>
                    <h1 style='color:var(--neon-green);'>You're doing great 👍</h1>
                    <p style='font-size:1.2rem;'>Everything looks normal.</p>
                </div>
            """, unsafe_allow_html=True)
            
    # --- 🧪 ADVANCED DEBUG ---
    with tab_advanced:
        st.markdown("#### AI Reasoning Dashboard")
        a_col1, a_col2 = st.columns([1, 1])
        
        with a_col1:
            st.markdown("##### Live Data")
            st.metric("Heart Rate", f"{data.get('hr', '--')} BPM")
            st.metric("Accelerometer", f"{data.get('accel', '--')} g")
            
            # Chart Integration
            st.markdown("##### History")
            st.line_chart(
                data={
                    "Heart Rate": st.session_state.hr_history,
                    "SpO2":       st.session_state.spo2_history,
                },
                use_container_width=True,
                height=150,
            )
        
        with a_col2:
            st.markdown("##### AI Brain")
            st.write(f"**State:** {state_label}")
            st.write(f"**Confidence:** {int(confidence*100)}%")
            st.progress(confidence)
            st.write(f"**Interruption Cost:** {int_cost}")
            st.write(f"**Urgency:** {urgency:.2f}")
        
        st.divider()
        st.markdown("##### 🔍 AI Thinking Trace")
        if st.session_state.using_fallback:
            st.warning("⚠️ Using fallback logic (LLM API unavailable or rate-limited)")
        st.info(" | ".join(steps) if steps else "Waiting for reasoning...")
        st.json({"final_decision": decision})
        
    # --- ⌚ WATCH MODE ---
    with tab_watch:
        render_watch(data, state_label, decision_val, urgency)

def render_watch(data, state_label, decision_val, urgency):
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Animation Classes
    container_class = "watch-face"
    if decision_val == "INTERRUPT" and urgency > 0.9 and not st.session_state.acknowledged:
        container_class += " pulse-emergency shake-emergency"
    
    color_code = "var(--neon-green)"
    if decision_val == "INTERRUPT" and urgency <= 0.9: color_code = "var(--neon-yellow)"
    if decision_val == "INTERRUPT" and urgency > 0.9: color_code = "var(--neon-red)"
    
    st.markdown(f"""
        <div class='{container_class}'>
            <p class='watch-label'>HR</p>
            <p class='watch-hr' style='color:{color_code};'>{data.get('hr', '--')}</p>
            <p style='color:{color_code}; font-weight:700; font-size:1.5rem;'>{state_label.upper() if state_label != 'Waiting...' else 'WAITING'}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.calling:
        st.markdown("<h2 style='text-align:center; color:var(--neon-red);'>Calling Emergency Services... 📞</h2>", unsafe_allow_html=True)
        st.progress(random.random()) # Fake calling animation


def render_trace():
    data     = st.session_state.sensor_data     or {}
    profile  = st.session_state.profiler_output or {}
    decision = st.session_state.action_output   or {}
    
    with st.expander("🔍 Live Agent Trace", expanded=False):
        
        # Fallback warning
        if st.session_state.using_fallback:
            st.warning("⚠️ Using fallback logic — LLM unavailable")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.caption("📡 SENSOR INPUT")
            if data:
                st.json({
                    "hr":    data.get("hr"),
                    "spo2":  data.get("spo2"),
                    "gsr":   data.get("gsr"),
                    "temp":  data.get("temp"),
                    "accel": data.get("accel"),
                    "flags": {
                        "hr_critical": data.get("hr_critical"),
                        "spo2_low":    data.get("spo2_low"),
                        "is_still":    data.get("is_still"),
                    }
                })
        
        with col_b:
            st.caption("🧠 PROFILER OUTPUT")
            if profile:
                st.json({
                    "state":       profile.get("state_label"),
                    "confidence":  profile.get("confidence"),
                    "int_cost":    profile.get("interruption_cost"),
                    "social":      profile.get("social_context"),
                    "reasoning":   profile.get("reasoning"),
                })
        
        with col_c:
            st.caption("⚡ ACTION OUTPUT")
            if decision:
                st.json({
                    "decision":  decision.get("decision"),
                    "action":    decision.get("action_type"),
                    "urgency":   decision.get("urgency"),
                    "override":  decision.get("override_flag"),
                    "steps":     decision.get("reasoning_steps"),
                })
        
        # Decision history table
        st.caption("📋 DECISION HISTORY")
        if st.session_state.agent_trace:
            import pandas as pd
            df = pd.DataFrame(st.session_state.agent_trace)
            st.dataframe(
                df[["cycle","hr","state","decision","urgency","override"]],
                use_container_width=True,
                hide_index=True,
            )

def main():
    # 1. Initialize all session state
    init_session_state()
    
    # 2. Run pipeline cycle (if simulation active)
    #    This must happen BEFORE any widget rendering
    if st.session_state.sim_running:
        run_simulation_cycle()
    
    # 3. Render page header + nav
    render_header()
    
    # 4. Render control buttons
    render_controls()
    
    # 5. Render sensor data panel (binds to session_state)
    render_sensors()
    
    # 6. Render agent panels (profiler + action)
    render_agents()
    
    # 7. Render watch view
    # render_watch() is inside render_agents to maintain tab structure
    
    # 8. Render agent trace (bottom expander)
    render_trace()
    
    # 9. Handle auto-refresh for simulation loop
    if st.session_state.sim_running:
        time.sleep(1.0)
        st.rerun()

if __name__ == "__main__":
    main()
