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
rate_limiter = RateLimiter(max_per_minute=100)

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
  "stress_level": "unknown", 
  "physical_state": "sedentary",
  "hr_trend": "stable",
  "location_context": "unknown",
  "active_intent": "unknown",
  "confidence": 0.0,
  "anomalies": [],
  "risk_factors": [],
  "suppression_reasons": ["agent_unavailable"],
  "reasoning": "Profiler agent unavailable, defaulting to safe mode"
}

ACTION_FALLBACK = {
  "action": "LOG_ONLY",
  "message": None,
  "urgency_score": 0.0,
  "suppression_active": True,
  "suppression_reason": "agent_unavailable",
  "interruption_cost": "high",
  "escalation_level": 0,
  "next_check_seconds": 10,
  "reasoning_short": "Agent unavailable, logging only",
  "reasoning_full": "System fell back to safe mode.",
  "next_steps": []
}

def _run_profiler_agent_internal(telemetry_window: list[dict]) -> dict:
    window_text = "\n".join([
        f"T-{len(telemetry_window)-1-i}: HR={r.get('hr')}bpm SpO2={r.get('spo2')}% "
        f"GSR={r.get('gsr')} Temp={r.get('temp')}°C "
        f"Accel={r.get('accel')} App={r.get('app')} Battery={r.get('battery')}%"
        for i, r in enumerate(telemetry_window)
    ])
    
    system_prompt = """
You are the Profiler Agent in a wearable health AI system.
Understand user state based on 30s sensor data.

Analyze the sensor data and output ONLY raw JSON. NO CONVERSATION. NO EXPLANATIONS.
JSON SCHEMA:
{
  "primary_state": "working | resting | meditating | exercising | emergency",
  "stress_level": "low | medium | high",
  "physical_state": "sedentary | active | still",
  "hr_trend": "stable | rising | falling",
  "active_intent": "description",
  "confidence": 0.95,
  "reasoning": "Brief explanation"
}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=400,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"SENSOR DATA:\n{window_text}"}
        ]
    )
    raw = response.choices[0].message.content.strip()
    print(f"DEBUG {"AGENT"} RAW: {raw[:150]}...")
    return json.loads(extract_json(raw))

def run_profiler_agent(telemetry_window: list[dict], fallback_cache: dict = None) -> dict:
    return safe_agent_call(_run_profiler_agent_internal, telemetry_window, fallback=fallback_cache or PROFILER_FALLBACK)

def _run_action_agent_internal(latest_sensor: dict, user_profile: dict, user_note: str, decision_history: list[dict]) -> dict:
    history_text = "\n".join([
        f"- {d['action']} ({d['reasoning_short']})"
        for d in decision_history[-5:]
    ]) if decision_history else "No previous decisions."
    
    system_prompt = """
You are the Action Agent. Final decision maker.

PRIORITY RULES:
1. Meditating/bead_counter -> STAY_SILENT
2. Emergency (2AM + High HR + Still) -> EMERGENCY_ALERT
3. Stress during work -> GENTLE_NOTIFY

Output ONLY raw JSON. NO CHATTER.
JSON SCHEMA:
{
  "action": "STAY_SILENT | GENTLE_NOTIFY | EMERGENCY_ALERT",
  "message": "text or null",
  "urgency_score": 0.5,
  "suppression_active": false,
  "reasoning_short": "summary",
  "reasoning_full": "logic"
}
"""
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=350,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"SENSOR: {latest_sensor}\nPROFILE: {user_profile}\nNOTE: {user_note}\nHISTORY: {history_text}"}
        ]
    )
    raw = response.choices[0].message.content.strip()
    print(f"DEBUG {"AGENT"} RAW: {raw[:150]}...")
    return json.loads(extract_json(raw))

def run_action_agent(latest_sensor: dict, user_profile: dict, user_note: str, decision_history: list[dict], fallback_cache: dict = None) -> dict:
    return safe_agent_call(_run_action_agent_internal, latest_sensor, user_profile, user_note, decision_history, fallback=fallback_cache or ACTION_FALLBACK)

class WearableAgentBrain:
    def __init__(self):
        self.telemetry_window = deque(maxlen=10)
        self.decision_history = []
        self.user_feedback = None
        self.feedback_time = 0
        self.profiler_cache = None
        self.action_cache = None
        self.llm_enabled = bool(client)
        
    def set_feedback(self, feedback: str):
        self.user_feedback = feedback
        self.feedback_time = time.time()

    def ingest(self, sensor_reading: dict):
        self.telemetry_window.append(sensor_reading)
        if time.time() - self.feedback_time > 120:
            self.user_feedback = None

        if len(self.telemetry_window) < 3:
            return {"status": "warming_up", "readings": len(self.telemetry_window)}
        
        # AGENT 1
        user_profile = run_profiler_agent(list(self.telemetry_window), fallback_cache=None)
        
        # AGENT 2
        feedback_note = f"USER JUST REPLIED: {self.user_feedback}" if self.user_feedback else ""
        decision = run_action_agent(sensor_reading, user_profile, feedback_note, self.decision_history, fallback_cache=None)
        
        self.decision_history.append({
            "timestamp": sensor_reading.get("timestamp"),
            "action": decision.get("action"),
            "reasoning_short": decision.get("reasoning_short"),
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
        self.profiler_cache = None
        self.action_cache = None

    def get_session_summary(self):
        actions = [d["action"] for d in self.decision_history]
        suppressed = sum(1 for a in actions if a in ["STAY_SILENT", "LOG_ONLY"])
        alerted = sum(1 for a in actions if a in ["EMERGENCY_ALERT", "URGENT_NOTIFY", "GENTLE_NOTIFY"])
        total = len(actions)
        return {
            "total_suppressed": suppressed,
            "total_alerted": alerted,
            "suppression_rate": f"{round(suppressed/total*100)}%" if total > 0 else "0%",
            "most_common_state": "N/A",
            "current_trend": "stable"
        }
