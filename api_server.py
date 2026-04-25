import os
import time
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the actual AI brain
from pure_agents import WearableAgentBrain
import json

load_dotenv()

app = FastAPI(title="Wearable AI Bridge")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── GLOBAL SIMULATION STATE & BRAIN ──
class SimState:
    def __init__(self):
        self.prev_hr = 72.0
        self.prev_spo2 = 98.0
        self.prev_gsr = 2.4
        self.prev_temp = 36.6
        self.prev_accel = 0.45
        self.sim_cycle = 0
        
        # Caching for LLM rate-limit prevention
        self.last_llm_time = 0
        self.cached_llm_response = None
        self.last_mode = "normal"

state = SimState()
start_time = time.time()

# Initialize the real Groq-powered AI Brain
try:
    brain = WearableAgentBrain()
except Exception as e:
    print(f"Failed to init brain: {e}")
    brain = None




# ── SENSOR GENERATOR ──
def generate_sensor_data(mode: str) -> dict:
    targets = {
        "normal": { "hr": 72, "spo2": 98.2, "gsr": 2.4, "temp": 36.6, "accel": 0.45 },
        "stress": { "hr": 108, "spo2": 96.8, "gsr": 7.2, "temp": 37.1, "accel": 0.08 },
        "emergency": { "hr": 134, "spo2": 93.5, "gsr": 13.8, "temp": 38.7, "accel": 0.02 }
    }
    
    t = targets.get(mode, targets["normal"])
    lerp = lambda prev, target, factor: prev + (target - prev) * factor
    
    noise = {
        "hr":    random.gauss(0, 2.5),
        "spo2":  random.gauss(0, 0.3),
        "gsr":   random.gauss(0, 0.4),
        "temp":  random.gauss(0, 0.08),
        "accel": random.gauss(0, 0.03),
    }
    
    hr    = lerp(state.prev_hr,    t["hr"],    0.18) + noise["hr"]
    spo2  = lerp(state.prev_spo2,  t["spo2"],  0.12) + noise["spo2"]
    gsr   = lerp(state.prev_gsr,   t["gsr"],   0.15) + noise["gsr"]
    temp  = lerp(state.prev_temp,  t["temp"],  0.10) + noise["temp"]
    accel = lerp(state.prev_accel, t["accel"], 0.20) + abs(noise["accel"])
    
    hr    = max(40, min(200, hr))
    spo2  = max(85, min(100, spo2))
    gsr   = max(0.1, min(25.0, gsr))
    temp  = max(35.0, min(42.0, temp))
    accel = max(0.0, min(3.0, accel))
    
    state.prev_hr    = hr
    state.prev_spo2  = spo2
    state.prev_gsr   = gsr
    state.prev_temp  = temp
    state.prev_accel = accel
    state.sim_cycle += 1
    
    # Map 'app' context for the LLM based on mode
    app_context = "idle"
    if mode == "stress": app_context = "work"
    if mode == "normal": app_context = "maps"
    
    data = {
        "hr":           round(hr, 1),
        "spo2":         round(spo2, 1),
        "gsr":          round(gsr, 2),
        "temp":         round(temp, 1),
        "accel":        round(accel, 3),
        "movement":     round(accel, 3), # Needed by LLM profiler
        "app":          app_context,     # Needed by LLM profiler
        "battery":      78,
        "mode":         mode,
        "cycle":        state.sim_cycle,
        "timestamp":    datetime.now().isoformat(),
        "hr_critical":  hr > 120,
        "spo2_low":     spo2 < 95,
        "is_still":     accel < 0.05,
        "temp_high":    temp > 38.0,
    }
    return data


# ── API ENDPOINTS ──
class SimulateRequest(BaseModel):
    mode: str

def map_to_ui_format(output: dict) -> dict:
    if output.get("status") == "warming_up":
        # Fallback while deque fills
        return {
            "sensor_data": output.get("sensor", {}),
            "profiler_output": {
                "state_headline": "Warming Up...",
                "confidence_pct": 0,
                "social_risk_pct": 0,
                "interruption_cost_pct": 0,
                "reasoning_trace": [f"Collecting data... {output.get('readings')}/3"],
                "action_decision": "STAY SILENT",
                "urgency_score": 0.0,
                "override_flag": "NONE",
                "watch_status_text": "Normal",
                "watch_notification_text": None,
                "show_eye_icon": True,
                "radar_values": {"hr_risk": 0, "social": 0, "env": 0, "battery": 0, "time_risk": 0, "accel": 0},
                "latency": "0ms",
                "radar_values": {"hr_risk": 0.1, "social": 0.1, "env": 0.5, "battery": 0.2, "time_risk": 0.3, "accel": 0.1}
            },
            "action_output": {
                "decision": "SUPPRESS",
                "action_type": "LOG_ONLY",
                "urgency": 0.0,
                "override_flag": "NONE",
                "reasoning_steps": ["Warming up context window..."]
            },
            "source": "agent"
        }
    
    try:
        sensor_data = output.get("sensor", {})
        profiler = output.get("profiler", {})
        decision = output.get("decision", {})
        
        state_headline = str(profiler.get("primary_state", "unknown")).replace("_", " ").title()
        
        # Robust confidence parsing
        conf = profiler.get("confidence", 0.0)
        try:
            confidence_pct = int(float(conf) * 100)
        except (ValueError, TypeError):
            confidence_pct = 0
        
        # Map Action
        action_str = str(decision.get("action", "STAY_SILENT"))
        is_suppress = action_str in ["STAY_SILENT", "LOG_ONLY"]
        mapped_decision = "SUPPRESS" if is_suppress else "INTERRUPT"
        
        # Override flags
        override_flag = "NONE"
        if decision.get("suppression_active"):
            supp_reason = str(decision.get("suppression_reason", "")).lower()
            if any(x in supp_reason for x in ["sleep", "meditat", "pray", "bead"]):
                override_flag = "SOCIAL CONTEXT OVERRIDE"
            elif "navigat" in supp_reason:
                override_flag = "NAVIGATION OVERRIDE"
        elif action_str == "EMERGENCY_ALERT":
            override_flag = "EMERGENCY PROTOCOL"
            
        reasoning_trace = [
            f"→ State: {state_headline}",
            f"→ Intent: {profiler.get('active_intent', 'unknown')}",
            f"→ {decision.get('reasoning_short', 'Analyzing telemetry...')}"
        ]
        
        try:
            urgency_score = float(decision.get("urgency_score", 0.0))
        except (ValueError, TypeError):
            urgency_score = 0.0
        
        # Heuristic for radar
        ic = str(decision.get("interruption_cost", "low")).lower()
        interruption_cost_pct = 95 if ic == "critical" else 75 if ic == "high" else 40 if ic == "medium" else 10
        social_risk_pct = 90 if override_flag == "SOCIAL CONTEXT OVERRIDE" else 10
        
        hr_val = sensor_data.get("hr", 72)
        hr_risk = min(1.0, max(0, (hr_val - 60) / 80))
        
        radar_values = {
            "hr_risk": round(hr_risk, 2),
            "social": round(social_risk_pct / 100, 2),
            "env": 0.5,
            "battery": round(1 - sensor_data.get("battery", 100) / 100, 2),
            "time_risk": 0.3,
            "accel": round(min(1.0, float(sensor_data.get("accel", 0))), 2)
        }
        
        profiler_output = {
            "state_headline": state_headline,
            "confidence_pct": confidence_pct,
            "social_risk_pct": social_risk_pct,
            "interruption_cost_pct": interruption_cost_pct,
            "reasoning_trace": reasoning_trace,
            "action_decision": "STAY SILENT" if is_suppress else "ALERT NOW",
            "urgency_score": urgency_score,
            "override_flag": override_flag,
            "watch_status_text": "Silent" if is_suppress else "ALERT",
            "watch_notification_text": decision.get("message") if not is_suppress else None,
            "show_eye_icon": is_suppress,
            "radar_values": radar_values,
            "latency": f"{output.get('total_latency_ms', 0)}ms"
        }
        
        return {
            "sensor_data": sensor_data,
            "profiler_output": profiler_output,
            "action_output": {
                "decision": mapped_decision,
                "action_type": action_str,
                "urgency": urgency_score,
                "override_flag": override_flag,
                "reasoning_steps": [decision.get("reasoning_full", "")]
            },
            "source": "agent"
        }
    except Exception as e:
        print(f"Error in map_to_ui_format: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "Mapping error", "status": "error"}


@app.post("/simulate_step")
async def simulate_step(req: SimulateRequest):
    try:
        sensor_data = generate_sensor_data(req.mode)
        
        # Handle Mode Switches
        if req.mode != state.last_mode:
            state.last_mode = req.mode

        output = brain.ingest(sensor_data)
        ui_payload = map_to_ui_format(output)
        
        return ui_payload
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reset")
async def reset_state():
    global state
    state = SimState()
    brain.reset()
    return {"status": "reset"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "llm_enabled": brain.llm_enabled if brain else False,
        "uptime_seconds": int(time.time() - start_time)
    }

@app.get("/session_summary")
async def session_summary():
    if not brain:
        return {"error": "Brain not initialized"}
    return brain.get_session_summary()

@app.post("/agent_simulate")
async def agent_simulate(req: dict):
    scenario_id = req.get("scenario", "A")
    
    if not brain:
        return {"error": "Brain not initialized", "fallback": True}
        
    try:
        import random
        # Scenario-specific sensor generation
        scenario_sensors = {
            "A": {"hr": 108 + random.randint(-4,4), "spo2": round(96.8 + random.uniform(-0.3,0.3),1), "gsr": round(7.2 + random.uniform(-0.5,0.5),2), "temp": round(37.1 + random.uniform(-0.1,0.1),1), "accel": round(0.08 + random.uniform(-0.03,0.03),3), "movement": round(0.08 + random.uniform(-0.03,0.03),3), "app": "work", "battery": 67, "time": "14:31", "timestamp": str(time.time())},
            "B": {"hr": 131 + random.randint(-5,5), "spo2": round(94.0 + random.uniform(-0.5,0.3),1), "gsr": round(13.8 + random.uniform(-0.8,0.8),2), "temp": round(38.9 + random.uniform(-0.2,0.2),1), "accel": round(0.02 + random.uniform(-0.01,0.01),3), "movement": round(0.02 + random.uniform(-0.01,0.01),3), "app": "sleep", "battery": 34, "time": "02:17", "timestamp": str(time.time())},
            "C": {"hr": 79 + random.randint(-3,3), "spo2": round(98.0 + random.uniform(-0.2,0.2),1), "gsr": round(0.31 + random.uniform(-0.05,0.05),2), "temp": round(36.6 + random.uniform(-0.1,0.1),1), "accel": round(0.85 + random.uniform(-0.1,0.1),3), "movement": round(0.85 + random.uniform(-0.1,0.1),3), "app": "maps", "battery": 5, "time": "18:45", "gps_familiarity": "unfamiliar", "timestamp": str(time.time())},
            "D": {"hr": 118 + random.randint(-4,4), "spo2": round(99.0 + random.uniform(-0.2,0.2),1), "gsr": round(0.15 + random.uniform(-0.03,0.03),2), "temp": round(36.4 + random.uniform(-0.1,0.1),1), "accel": round(0.01 + random.uniform(-0.005,0.005),3), "movement": round(0.01 + random.uniform(-0.005,0.005),3), "app": "bead_counter", "battery": 82, "time": "06:15", "timestamp": str(time.time())},
        }
        
        sensor_data = scenario_sensors.get(scenario_id, scenario_sensors["A"])
        
        # Reset brain but pre-fill memory to avoid warming up delay in scenarios
        brain.reset()
        for _ in range(5):
            # Fill window with scenario-like data but don't call LLM
            brain.telemetry_window.append(sensor_data)
        
        # Now call once for real
        output = brain.ingest(sensor_data)
        
        return map_to_ui_format(output)
        
        return map_to_ui_format(output)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e), "fallback": True}

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Wearable AI Local Sim Server (Groq Edition) on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
