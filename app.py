import streamlit as st
import time
import json
import random
import base64
from datetime import datetime
from dataclasses import asdict
from dotenv import load_dotenv

# Import Phase 3 Components
from models import UserProfile, SensorData
from memory_store import UserMemoryStore
from profiler import PersonalizedProfiler
from llm_agent import WearableLLMAgent
from action_agent import AdaptiveActionAgent

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="Wearable AI Intelligence Engine",
    page_icon="⌚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Advanced CSS for Animations & UI
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

# --- INITIALIZATION ---
@st.cache_resource
def init_brain():
    memory = UserMemoryStore()
    profile = UserProfile(
        user_id="demo_user",
        avg_resting_hr=65,
        sleep_time="23:00",
        wake_time="07:00",
        recent_hr=[65, 66, 64, 67, 65]
    )
    memory.add_user(profile)
    profiler = PersonalizedProfiler(memory)
    llm_agent = WearableLLMAgent(model="llama-3.1-8b-instant")
    action_agent = AdaptiveActionAgent(memory)
    return memory, profiler, llm_agent, action_agent

memory, profiler, llm_agent, action_agent = init_brain()

# Session State for Simulation & UI Modes
if 'current_hr' not in st.session_state:
    st.session_state.current_hr = 65.0
if 'target_hr' not in st.session_state:
    st.session_state.target_hr = 65.0
if 'movement_score' not in st.session_state:
    st.session_state.movement_score = 10.0
if 'target_movement' not in st.session_state:
    st.session_state.target_movement = 10.0
if 'app_context' not in st.session_state:
    st.session_state.app_context = "idle"
if 'brain_output' not in st.session_state:
    st.session_state.brain_output = None
if 'acknowledged' not in st.session_state:
    st.session_state.acknowledged = False
if 'calling' not in st.session_state:
    st.session_state.calling = False

# --- ENGINE LOGIC ---
def update_engine():
    # Gradual transitions
    st.session_state.current_hr += (st.session_state.target_hr - st.session_state.current_hr) / 5 + random.uniform(-0.5, 0.5)
    st.session_state.movement_score += (st.session_state.target_movement - st.session_state.movement_score) / 4
    
    mov_label = "low" if st.session_state.movement_score < 30 else ("medium" if st.session_state.movement_score < 70 else "high")
    
    sensor_data = SensorData(
        timestamp=datetime.now().strftime("%H:%M:%S"),
        hr=int(st.session_state.current_hr),
        movement=mov_label,
        app_context=st.session_state.app_context
    )
    
    state_info = profiler.evaluate_condition("demo_user", sensor_data)
    
    # Update AI Brain (optimized)
    if st.session_state.brain_output is None or state_info.urgency != "low" or random.random() < 0.1:
        profile = memory.get_profile("demo_user")
        try:
            llm_pred = llm_agent.analyze_situation(profile, sensor_data, state_info)
        except:
            llm_pred = None # Fallback logic handled in UI
        
        # Mocking LLM if failed to avoid demo crash
        if not llm_pred:
            from models import LLMPrediction
            llm_pred = LLMPrediction(
                personalized_risk=state_info.urgency,
                deviation_detected=state_info.deviation_detected,
                explanation="[FALLBACK] Rule-based pattern matching active.",
                advice="Monitoring contextually..."
            )
            
        decision = action_agent.decide("demo_user", state_info, llm_pred)
        st.session_state.brain_output = {
            "sensor_data": sensor_data,
            "state_info": state_info,
            "llm_pred": llm_pred,
            "decision": decision
        }
    else:
        st.session_state.brain_output["sensor_data"] = sensor_data
        st.session_state.brain_output["state_info"] = state_info

update_engine()
run = st.session_state.brain_output
state = run['state_info']
llm = run['llm_pred']
decision = run['decision']

# --- EMERGENCY SOUND ---
if state.urgency == "high" and not st.session_state.acknowledged:
    # Play a standard alert beep using data URI (base64)
    # This is a short synthesized beep
    st.markdown("""
        <audio autoplay loop>
            <source src="https://www.soundjay.com/buttons/beep-07.mp3" type="audio/mpeg">
        </audio>
    """, unsafe_allow_html=True)

# --- TOP NAVIGATION & SCENARIOS ---
tab_user, tab_advanced, tab_watch = st.tabs(["👤 USER VIEW", "🧪 ADVANCED DEBUG", "⌚ WATCH MODE"])

with st.sidebar:
    st.title("Scenario Control")
    if st.button("😴 Sleep Mode", use_container_width=True):
        st.session_state.target_hr = 54.0
        st.session_state.target_movement = 5.0
        st.session_state.app_context = "Sleep Tracker"
        st.session_state.acknowledged = False
        st.session_state.calling = False
    if st.button("🏃 Workout Mode", use_container_width=True):
        st.session_state.target_hr = 125.0
        st.session_state.target_movement = 85.0
        st.session_state.app_context = "Fitness App"
    if st.button("🚨 Crisis Mode", use_container_width=True):
        st.session_state.target_hr = 165.0
        st.session_state.target_movement = 10.0
        st.session_state.app_context = "None"
        st.session_state.acknowledged = False
        st.session_state.calling = False
    
    st.divider()
    st.caption("Engine: 🟢 Active")
    st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

# --- 👤 USER VIEW ---
with tab_user:
    st.markdown("<br><br>", unsafe_allow_html=True)
    if state.urgency == "high":
        st.markdown(f"""
            <div class='user-card' style='border: 4px solid var(--neon-red);'>
                <h1 style='color:var(--neon-red); font-size:4rem;'>🚨 Something is wrong</h1>
                <p style='font-size:1.5rem;'>We detected an unusual heart rate pattern.</p>
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
    elif state.urgency == "medium":
        st.markdown(f"""
            <div class='user-card' style='border: 4px solid var(--neon-yellow);'>
                <h1 style='color:var(--neon-yellow);'>You seem stressed</h1>
                <p style='font-size:1.2rem;'>{decision.advice}</p>
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
        st.metric("Heart Rate", f"{int(st.session_state.current_hr)} BPM")
        st.metric("Movement", f"{int(st.session_state.movement_score)}%")
        st.progress(st.session_state.movement_score / 100)
    
    with a_col2:
        st.markdown("##### AI Brain")
        st.write(f"**State:** {state.state}")
        st.write(f"**Confidence:** {int(state.confidence*100)}%")
        st.progress(state.confidence)
        st.write(f"**Urgency:** {state.urgency.upper()}")
    
    st.divider()
    st.markdown("##### 🔍 AI Thinking Trace")
    if "[FALLBACK]" in llm.explanation:
        st.warning("⚠️ Using fallback logic (LLM API unavailable or rate-limited)")
    st.info(llm.explanation)
    st.json({"final_decision": asdict(decision)})

# --- ⌚ WATCH MODE ---
with tab_watch:
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Animation Classes
    container_class = "watch-face"
    if state.urgency == "high" and not st.session_state.acknowledged:
        container_class += " pulse-emergency shake-emergency"
    
    color_code = "var(--neon-green)"
    if state.urgency == "medium": color_code = "var(--neon-yellow)"
    if state.urgency == "high": color_code = "var(--neon-red)"
    
    st.markdown(f"""
        <div class='{container_class}'>
            <p class='watch-label'>HR</p>
            <p class='watch-hr' style='color:{color_code};'>{int(st.session_state.current_hr)}</p>
            <p style='color:{color_code}; font-weight:700; font-size:1.5rem;'>{state.state.upper()}</p>
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.calling:
        st.markdown("<h2 style='text-align:center; color:var(--neon-red);'>Calling Emergency Services... 📞</h2>", unsafe_allow_html=True)
        st.progress(random.random()) # Fake calling animation

# --- FOOTER AUTO-REFRESH ---
time.sleep(1.2)
st.rerun()
