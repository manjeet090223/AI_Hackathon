import os
import time
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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

@app.get("/")
async def get_index():
    return FileResponse("index.html", headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

@app.get("/favicon.ico")
async def favicon():
    return HTTPException(status_code=204)


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
        "a": { "hr": 108, "spo2": 97.0, "gsr": 0.72, "temp": 37.2, "accel": 0.01, "app": "work" },
        "b": { "hr": 131, "spo2": 94.0, "gsr": 0.91, "temp": 38.9, "accel": 0.02, "app": "sleep" },
        "c": { "hr": 79,  "spo2": 98.0, "gsr": 0.31, "temp": 36.6, "accel": 0.85, "app": "maps" },
        "d": { "hr": 52,  "spo2": 99.0, "gsr": 0.12, "temp": 36.1, "accel": 0.01, "app": "sleep" },
        "e": { "hr": 165, "spo2": 96.0, "gsr": 0.95, "temp": 38.2, "accel": 1.80, "app": "fitness" },
        "f": { "hr": 62,  "spo2": 100.0, "gsr": 0.08, "temp": 36.4, "accel": 0.01, "app": "meditation" },
        "g": { "hr": 88,  "spo2": 97.0, "gsr": 0.45, "temp": 36.8, "accel": 0.45, "app": "podcasts" },
        "h": { "hr": 95,  "spo2": 96.0, "gsr": 0.82, "temp": 37.0, "accel": 0.15, "app": "maps" }
    }
    
    t = targets.get(mode, targets["a"])
    lerp = lambda prev, target, factor: prev + (target - prev) * factor
    
    noise = {
        "hr":    random.gauss(0, 1.5),
        "spo2":  random.gauss(0, 0.2),
        "gsr":   random.gauss(0, 0.05),
        "temp":  random.gauss(0, 0.05),
        "accel": random.gauss(0, 0.02),
    }
    
    hr    = lerp(state.prev_hr,    t["hr"],    0.15) + noise["hr"]
    spo2  = lerp(state.prev_spo2,  t["spo2"],  0.10) + noise["spo2"]
    gsr   = lerp(state.prev_gsr,   t["gsr"],   0.10) + noise["gsr"]
    temp  = lerp(state.prev_temp,  t["temp"],  0.08) + noise["temp"]
    accel = lerp(state.prev_accel, t["accel"], 0.20) + abs(noise["accel"])
    
    hr    = max(40, min(200, hr))
    spo2  = max(85, min(100, spo2))
    gsr   = max(0.01, min(5.0, gsr))
    temp  = max(35.0, min(42.0, temp))
    accel = max(0.0, min(3.0, accel))
    
    state.prev_hr    = hr
    state.prev_spo2  = spo2
    state.prev_gsr   = gsr
    state.prev_temp  = temp
    state.prev_accel = accel
    state.sim_cycle += 1
    
    # STAGE 2: GALAXY WATCH BLE PACKET FORMAT
    ble_packet = {
        "ble_header": {
            "device_id": "GALAXY-WATCH-4-BT",
            "rssi": random.randint(-65, -45),
            "protocol": "GATT",
            "service_uuid": "0000180d-0000-1000-8000-00805f9b34fb"
        },
        "payload": {
            "heart_rate": round(hr, 1),
            "spo2": round(spo2, 1),
            "gsr": round(gsr, 2),
            "skin_temp": round(temp, 1),
            "accel": {
                "x": round(random.uniform(-0.1, 0.1), 3),
                "y": round(random.uniform(-0.1, 0.1), 3),
                "z": round(0.98 + random.uniform(-0.02, 0.02), 3),
                "mag": round(accel, 3)
            },
            "battery": 78
        },
        "metadata": {
            "timestamp": int(time.time() * 1000),
            "cycle": state.sim_cycle,
            "mode": mode,
            "app": t["app"]
        }
    }
    return ble_packet


# ── API ENDPOINTS ──
class SimulateRequest(BaseModel):
    mode: str
    sensor_data: dict = None
    window_stats: dict = None
    baseline: dict = None

def map_to_ui_format(output: dict) -> dict:
    if output.get("status") == "warming_up":
        # Fallback while deque fills
        return {
            "sensor_data": output.get("sensor", {}),
            "profiler_output": {
                "state_headline": "Warming Up...",
                "confidence_pct": 0,
                "reasoning_trace": [f"Collecting data... {output.get('readings')}/3"],
                "radar_values": {"hr_risk": 0.1, "social": 0.1, "env": 0.5, "battery": 0.2, "time_risk": 0.3, "accel": 0.1}
            },
            "action_output": {
                "decision": "SUPPRESS",
                "action_type": "SILENT_LOG",
                "urgency": 0.0,
                "reasoning_steps": ["Warming up context window..."]
            },
            "source": "agent"
        }
    
    try:
        sensor_dict = output.get("sensor", {})
        payload = sensor_dict.get("payload", {})
        metadata = sensor_dict.get("metadata", {})
        profiler = output.get("profiler", {})
        decision = output.get("decision", {})
        
        # Flatten for UI
        sensor_data = {
            "hr": payload.get("heart_rate") or 72,
            "spo2": payload.get("spo2") or 98,
            "gsr": payload.get("gsr") or 0.5,
            "temp": payload.get("skin_temp") or 36.6,
            "accel": payload.get("accel", {}).get("mag") or 0.0,
            "bat": payload.get("battery") or 100,
            "src": "LIVE-BLE",
            "app": metadata.get("app") or "idle"
        }

        state_headline = str(profiler.get("primary_state", "unknown")).replace("_", " ").title()
        
        # Map 6 Actions to 3 UI Categories for Style consistency, but keep raw type
        action_str = str(decision.get("action", "SILENT_LOG"))
        if action_str in ["SILENT_LOG", "HAPTIC_ONLY"]:
            mapped_decision = "SUPPRESS"
        elif action_str in ["GENTLE_NOTIFY", "ACTIVE_ALERT", "CAREGIVER_PING"]:
            mapped_decision = "NOTIFY"
        else:
            mapped_decision = "INTERRUPT"
            
        # Build Rich Reasoning Trace
        reasoning_trace = [
            f"PROFILER_AGENT: State = {state_headline} ({int(profiler.get('state_confidence', 0.5)*100)}%)",
            f"PROFILER_AGENT: Environment = {profiler.get('environment', 'unknown')}",
            f"PROFILER_AGENT: Cost = {profiler.get('interruption_cost', 0.5)} | Stakes = {profiler.get('social_stakes', 'LOW')}",
            f"PROFILER_AGENT: Reasoning = {profiler.get('reasoning', 'Analyzing...')}"
        ]
        
        urgency_score = float(decision.get("urgency_score", 0.0))
        
        radar_values = {
            "hr_risk": round(float(decision.get("health_risk_score", 0.3)), 2),
            "social": round(float(profiler.get("interruption_cost", 0.5)), 2),
            "env": 0.5,
            "battery": round(1 - float(sensor_data["bat"]) / 100, 2),
            "time_risk": 0.3,
            "accel": round(min(1.0, float(sensor_data["accel"])), 2)
        }
        
        profiler_output = {
            "state_headline": state_headline,
            "confidence_pct": int(profiler.get("state_confidence", 0.5) * 100),
            "reasoning_trace": reasoning_trace,
            "urgency_score": urgency_score,
            "radar_values": radar_values,
            "cost_score": profiler.get("interruption_cost", 0.5)
        }
        
        return {
            "sensor_data": sensor_data,
            "profiler_output": profiler_output,
            "action_output": {
                "decision": mapped_decision,
                "action_type": action_str,
                "urgency": urgency_score,
                "override_flag": decision.get("override_applied") or "NONE",
                "notification_text": decision.get("notification_text"),
                "reasoning_steps": [f"ACTION_AGENT: {decision.get('reasoning', '')}"]
            },
            "source": "agent"
        }
    except Exception as e:
        print(f"Error in map_to_ui_format: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "Mapping error", "status": "error"}
    except Exception as e:
        print(f"Error in map_to_ui_format: {e}")
        import traceback
        traceback.print_exc()
        return {"error": "Mapping error", "status": "error"}


@app.post("/simulate_step")
def simulate_step(req: SimulateRequest):
    try:
        # Prefer client data (real sensors) over server-generated data
        if req.sensor_data and req.sensor_data.get('hr') is not None:
            sensor_data = {
                "ble_header": {"device_id": "REAL-SENSOR-MERGE", "rssi": -50},
                "payload": {
                    "heart_rate": req.sensor_data.get("hr"),
                    "spo2": req.sensor_data.get("spo2"),
                    "gsr": req.sensor_data.get("gsr"),
                    "skin_temp": req.sensor_data.get("temp"),
                    "accel": {"mag": req.sensor_data.get("accel")},
                    "battery": req.sensor_data.get("bat")
                },
                "metadata": {
                    "timestamp": int(time.time() * 1000),
                    "app": req.sensor_data.get("app", "unknown"),
                    "mode": req.mode
                }
            }
            # Update state to keep LERPing smooth if we switch back to sim
            state.prev_hr = req.sensor_data.get("hr")
            state.prev_accel = req.sensor_data.get("accel")
        else:
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

@app.post("/user_feedback")
async def user_feedback(req: dict):
    feedback = req.get("feedback", "FINE")
    if brain:
        brain.set_feedback(feedback)
        # Force a return to normal scenario in the simulator
        return {"status": "feedback_received", "action": "RESET_SIM"}
    return {"error": "Brain not initialized"}

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
