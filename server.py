import os
import time
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Import the actual AI brain
from wearable_brain_v2 import WearableContextBrainV2

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

# Initialize the real Groq-powered AI Brain
try:
    brain = WearableContextBrainV2(use_llm=True)
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

@app.post("/simulate_step")
async def simulate_step(req: SimulateRequest):
    try:
        sensor_data = generate_sensor_data(req.mode)
        
        # Handle Mode Switches (force LLM update if scenario changes)
        if req.mode != state.last_mode:
            state.last_llm_time = 0
            state.last_mode = req.mode

        now = time.time()
        should_throttle_llm = (now - state.last_llm_time) < 8.0 # 8 second cache limit
        
        # We temporarily disable LLM if we are throttling to avoid rate limits
        original_llm_enabled = brain.llm_enabled
        if should_throttle_llm:
            brain.llm_enabled = False
            
        # Process through actual WearableContextBrainV2
        output = brain.process(sensor_data)
        
        # Restore LLM state
        brain.llm_enabled = original_llm_enabled

        # Update cache if LLM actually ran
        if output.get("hybrid_reasoning") and output.get("llm_enhanced"):
            state.cached_llm_response = output["llm_enhanced"]
            state.last_llm_time = now
            
        # Inject cached LLM response if we throttled this frame
        if should_throttle_llm and state.cached_llm_response:
            output["llm_enhanced"] = state.cached_llm_response
        
        # -- MAP OUTPUT TO UI FORMAT --
        rule = output.get("rule_based", {})
        llm = output.get("llm_enhanced")
        decision = output.get("final_decision", {})
        
        # Extract profiler info
        if llm:
            state_label = llm.get("final_state", "").title()
            confidence = llm.get("confidence", 0.9)
            reasoning = [
                f"Risk Assessment: {llm.get('risk_level', '').upper()}",
                llm.get("explanation", ""),
                f"Advice: {llm.get('advice', '')}"
            ]
        else:
            state_label = rule.get("state", "").title()
            confidence = rule.get("confidence", 0.8)
            reasoning = [
                "Using Rule-Based Analysis",
                rule.get("reason", "")
            ]
            
        # Extract action info
        action_str = decision.get("action", "NO_ACTION")
        is_suppress = "SUPPRESS" in action_str or "SILENT" in action_str or "DO_NOT_DISTURB" in action_str
        mapped_decision = "SUPPRESS" if is_suppress else "INTERRUPT"
        
        ui_payload = {
            "sensor_data": sensor_data,
            "profiler_output": {
                "state_label": state_label,
                "confidence": confidence,
                "reasoning": reasoning
            },
            "action_output": {
                "decision": mapped_decision,
                "action_type": action_str,
                "urgency": rule.get("urgency", 5) / 10.0,
                "override_flag": "AI_GENERATED",
                "reasoning_steps": decision.get("next_steps", []) or [decision.get("reason", "")]
            }
        }
        
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

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Wearable AI Local Sim Server (Groq Edition) on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
