import os
import json
import time
from collections import deque
from groq import Groq
import groq
from dotenv import load_dotenv

load_dotenv()

class RateLimiter:
    def __init__(self, max_per_minute=100):
        self.max_per_minute = max_per_minute
        self.calls = deque()
    
    def can_call(self) -> bool:
        now = time.time()
        while self.calls and self.calls[0] < now - 60:
            self.calls.popleft()
        if len(self.calls) < self.max_per_minute:
            self.calls.append(now)
            return True
        return False

# Global Rate Limiter
rate_limiter = RateLimiter(max_per_minute=300)

# Initialize Groq client
client = None
if os.getenv("GROQ_API_KEY"):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_json(text: str) -> str:
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1:
        return text[start:end+1]
    return text

def safe_agent_call(func, *args, fallback: dict, **kwargs) -> dict:
    try:
        if not client:
            print("ERROR: Groq client not initialized")
            return fallback
        return func(*args, **kwargs)
    except groq.RateLimitError as e:
        print(f"RATE LIMIT: {e}")
        return fallback
    except Exception as e:
        print(f"AGENT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return fallback

PROFILER_FALLBACK = {
  "primary_state": "unknown",
  "state_confidence": 0.0,
  "stress_level": "low", 
  "stress_confidence": 0.0,
  "active_intent": "unknown",
  "environment": "unknown",
  "time_context": "unknown",
  "interruption_cost": 0.5,
  "social_stakes": "LOW",
  "hrv_trend": "stable",
  "predicted_next_state": "unknown",
  "prediction_confidence": 0.0,
  "reasoning": "Profiler fallback active"
}

ACTION_FALLBACK = {
  "action": "SILENT_LOG",
  "urgency_score": 0.0,
  "health_risk_score": 0.0,
  "interruption_cost_score": 0.5,
  "override_applied": "AGENT_FALLBACK",
  "notification_text": None,
  "escalation_applied": False,
  "reasoning": "Action fallback active"
}

def _run_profiler_agent_internal(telemetry_window: list[dict]) -> dict:
    # Extract telemetry arrays for the prompt
    hr_array = [r.get('payload', {}).get('heart_rate') for r in telemetry_window]
    spo2_array = [r.get('payload', {}).get('spo2') for r in telemetry_window]
    accel_array = [r.get('payload', {}).get('accel', {}).get('mag') for r in telemetry_window]
    
    # Simple HRV approximation from HR fluctuations if not present
    hrv_val = 40 # Default
    if len(hr_array) > 1:
        diffs = [abs(hr_array[i] - hr_array[i-1]) for i in range(1, len(hr_array))]
        hrv_val = sum(diffs) / len(diffs) * 10 # Rough scaling

    latest = telemetry_window[-1]
    payload = latest.get('payload', {})
    metadata = latest.get('metadata', {})
    
    # Time context
    hour = datetime.fromtimestamp(metadata.get('timestamp', time.time()*1000)/1000).hour
    time_ctx = "sleep" if (hour < 6 or hour > 22) else "morning" if hour < 12 else "work" if hour < 18 else "evening"

    system_prompt = f"""
You are a wearable health context profiler.
Analyze this 30-second sensor window and return ONLY valid JSON.

SENSOR WINDOW (last 10 readings):
HR values: {hr_array}
SpO2 values: {spo2_array}
Motion magnitude: {accel_array}
Skin temp: {payload.get('skin_temp')}°C
Active app: {metadata.get('app')}
Time of day: {time_ctx} (Hour: {hour})
Battery: {payload.get('battery')}%

Return this exact JSON — no other text:
{{
 "primary_state": "working | resting | meditating | exercising | emergency",
 "state_confidence": float 0-1,
 "stress_level": "low"|"medium"|"high"|"critical",
 "stress_confidence": float 0-1,
 "active_intent": string,
 "environment": "home"|"office"|"commute"|"unknown",
 "time_context": "sleep"|"morning"|"work"|"evening",
 "interruption_cost": float 0-1,
 "social_stakes": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL",
 "hrv_trend": "rising"|"stable"|"falling",
 "predicted_next_state": string,
 "prediction_confidence": float 0-1,
 "reasoning": string max 2 sentences
}}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=500,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Analyze latest window."}
        ]
    )
    raw = response.choices[0].message.content.strip()
    print(f"DEBUG PROFILER RAW: {raw[:150]}...")
    return json.loads(extract_json(raw))

def run_profiler_agent(telemetry_window: list[dict], fallback_cache: dict = None) -> dict:
    return safe_agent_call(_run_profiler_agent_internal, telemetry_window, fallback=fallback_cache or PROFILER_FALLBACK)

def _run_action_agent_internal(latest_sensor: dict, user_profile: dict, user_note: str, decision_history: list[dict], suppress_count: int) -> dict:
    history_text = "\n".join([
        f"- {d['action']} ({d.get('reasoning_short', 'No detail')})"
        for d in decision_history[-5:]
    ]) if decision_history else "No previous decisions."
    
    system_prompt = f"""
You are a wearable AI action decision engine.
Your job: decide whether to interrupt the user.

PROFILER OUTPUT: {json.dumps(user_profile)}
LATEST SENSORS: hr={latest_sensor.get('payload', {}).get('heart_rate')}, spo2={latest_sensor.get('payload', {}).get('spo2')}, accel={latest_sensor.get('payload', {}).get('accel', {}).get('mag')}
DECISION HISTORY (last 5): {history_text}
CONSECUTIVE SUPPRESSES: {suppress_count}
SESSION CONTEXT: {user_note}

PRIORITY RULES (in order):
1. If primary_state is meditating or bead_counter → SILENT_LOG
2. If hr > 130 AND accel < 0.1 AND (time_context = sleep OR primary_state = emergency) → EMERGENCY_CALL
3. If interruption_cost > 0.7 AND health_risk < 0.4 → SILENT_LOG
4. If suppress_count >= 3 AND urgency rising → escalate one level
5. Compare health_risk vs interruption_cost → decide

Return this exact JSON:
{{
 "action": "SILENT_LOG"|"HAPTIC_ONLY"|"GENTLE_NOTIFY"|"ACTIVE_ALERT"|"CAREGIVER_PING"|"EMERGENCY_CALL",
 "urgency_score": float 0-1,
 "health_risk_score": float 0-1,
 "interruption_cost_score": float 0-1,
 "notification_text": "Polite, empathetic message (only for GENTLE_NOTIFY/ACTIVE_ALERT, e.g., 'Remember to keep your shoulders relaxed')",
 "escalation_applied": boolean,
 "reasoning": string max 3 sentences
}}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=400,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Determine action."}
        ]
    )
    raw = response.choices[0].message.content.strip()
    print(f"DEBUG ACTION RAW: {raw[:150]}...")
    return json.loads(extract_json(raw))

def run_action_agent(latest_sensor: dict, user_profile: dict, user_note: str, decision_history: list[dict], suppress_count: int, fallback_cache: dict = None) -> dict:
    return safe_agent_call(_run_action_agent_internal, latest_sensor, user_profile, user_note, decision_history, suppress_count, fallback=fallback_cache or ACTION_FALLBACK)

from datetime import datetime

class WearableAgentBrain:
    def __init__(self):
        self.telemetry_window = deque(maxlen=10)
        self.decision_history = []
        self.user_feedback = None
        self.feedback_time = 0
        self.profiler_cache = None
        self.action_cache = None
        self.llm_enabled = bool(client)
        self.consecutive_suppress_count = 0
        self.last_state = None
        
    def set_feedback(self, feedback: str):
        self.user_feedback = feedback
        self.feedback_time = time.time()

    def ingest(self, sensor_reading: dict):
        self.telemetry_window.append(sensor_reading)
        if time.time() - self.feedback_time > 120:
            self.user_feedback = None

        if len(self.telemetry_window) < 3:
            return {"status": "warming_up", "readings": len(self.telemetry_window)}
        
        # AGENT 1: Profiler
        user_profile = run_profiler_agent(list(self.telemetry_window), fallback_cache=None)
        
        # Track state consistency
        current_state = user_profile.get("primary_state")
        if current_state != self.last_state:
            self.consecutive_suppress_count = 0
            self.last_state = current_state

        # AGENT 2: Action
        feedback_note = f"USER JUST REPLIED: {self.user_feedback}" if self.user_feedback else ""
        decision = run_action_agent(sensor_reading, user_profile, feedback_note, self.decision_history, self.consecutive_suppress_count, fallback_cache=None)
        
        # Update suppression memory
        if decision.get("action") == "SILENT_LOG":
            self.consecutive_suppress_count += 1
        else:
            self.consecutive_suppress_count = 0

        self.decision_history.append({
            "timestamp": sensor_reading.get("timestamp"),
            "action": decision.get("action"),
            "reasoning_short": decision.get("reasoning", "No detail")[:50],
            "urgency_score": decision.get("urgency_score")
        })
        if len(self.decision_history) > 20:
            self.decision_history = self.decision_history[-20:]
        
        return {
            "sensor": sensor_reading,
            "profiler": user_profile,
            "decision": decision,
            "status": "ready"
        }
    
    def reset(self):
        self.telemetry_window.clear()
        self.decision_history.clear()
        self.user_feedback = None
        self.feedback_time = 0
        self.profiler_cache = None
        self.action_cache = None
        self.consecutive_suppress_count = 0
        self.last_state = None

    def get_session_summary(self):
        actions = [d["action"] for d in self.decision_history]
        suppressed = sum(1 for a in actions if a == "SILENT_LOG")
        alerted = sum(1 for a in actions if a != "SILENT_LOG")
        total = len(actions)
        return {
            "total_suppressed": suppressed,
            "total_alerted": alerted,
            "suppression_rate": f"{round(suppressed/total*100)}%" if total > 0 else "0%",
            "most_common_state": self.last_state or "N/A",
            "current_trend": "stable"
        }

