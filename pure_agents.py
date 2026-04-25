import os
import json
import time
from collections import deque
from groq import Groq
import groq
from dotenv import load_dotenv

load_dotenv()

class RateLimiter:
    def __init__(self, calls_per_minute=25):
        self.calls_per_minute = calls_per_minute
        self.calls = deque()
    
    def can_call(self) -> bool:
        now = time.time()
        # Remove calls older than 60 seconds
        while self.calls and self.calls[0] < now - 60:
            self.calls.popleft()
        if len(self.calls) < self.calls_per_minute:
            self.calls.append(now)
            return True
        return False

# Initialize rate limiter
rate_limiter = RateLimiter(calls_per_minute=25)

# Initialize Groq client
client = None
if os.getenv("GROQ_API_KEY"):
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Caches for rate limiting / failures
_cached_profiler_response = None
_cached_action_response = None

def safe_agent_call(func, *args, fallback: dict, **kwargs) -> dict:
    try:
        if not client:
            print("Groq client not initialized (missing API key)")
            return fallback
            
        result = func(*args, **kwargs)
        return result
    except json.JSONDecodeError as e:
        print(f"Agent returned malformed JSON: {e}")
        return fallback
    except groq.RateLimitError:
        print("Groq rate limit hit, using last cached response")
        return fallback
    except groq.APIConnectionError:
        print("Groq API unreachable")
        return fallback
    except Exception as e:
        print(f"Unexpected agent error: {e}")
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
  "suppression_reason": "agent_unavailable — defaulting to safe silence",
  "interruption_cost": "high",
  "escalation_level": 0,
  "next_check_seconds": 10,
  "reasoning_short": "Agent unavailable, logging only",
  "reasoning_full": "System fell back to safe mode.",
  "next_steps": []
}

def _run_profiler_agent_internal(telemetry_window: list[dict]) -> dict:
    global _cached_profiler_response
    if not rate_limiter.can_call():
        return _cached_profiler_response or PROFILER_FALLBACK
        
    window_text = "\n".join([
        f"T-{len(telemetry_window)-1-i}: HR={r.get('hr')}bpm SpO2={r.get('spo2')}% "
        f"GSR={r.get('gsr')} Temp={r.get('temp')}°C "
        f"Accel={r.get('accel')} App={r.get('app')} Battery={r.get('battery')}%"
        for i, r in enumerate(telemetry_window)
    ])
    
    system_prompt = """
You are the Profiler Agent in a wearable health AI system.
Your only job is to understand what the user is currently 
experiencing based on 30 seconds of sensor data.

You are a medical-grade context interpreter. You think like 
a doctor who can see biometric data — you look for patterns, 
trends, and combinations of signals, not just single values.

YOUR REASONING PROCESS — think through all of these:

1. HEART RATE ANALYSIS
   - What is the trend? (rising/falling/stable/volatile)
   - Is it appropriate for the detected activity?
   - Is the value dangerous for someone who is sedentary?
   - HR > 100 + sitting still = concerning
   - HR > 130 + sitting still = potentially dangerous
   - HR > 100 + high accel = normal exercise response

2. MOVEMENT ANALYSIS  
   - Accel < 0.05 = completely still (sleeping/sitting/meditating)
   - Accel 0.05-0.3 = minimal movement (typing, fidgeting)
   - Accel 0.3-0.8 = walking
   - Accel > 0.8 = running or intense activity

3. APP CONTEXT — this is the most important signal
   - bead_counter = user is meditating or praying (NEVER alert)
   - maps + unfamiliar GPS = navigating unknown area (high focus)
   - sleep = user is sleeping (suppress everything except emergency)
   - fitness = intentional workout (elevated HR is expected)
   - work = desk work (elevated HR = stress, not exercise)
   - idle + elevated HR = most concerning combination

4. STRESS INDICATORS
   - GSR (galvanic skin response) > 8 = elevated stress
   - GSR > 15 = high stress or physical exertion
   - HR elevated + GSR elevated + accel low = mental/emotional stress
   - Skin temp > 38.0°C = fever or intense physical stress

5. TIME CONTEXT
   - 22:00 - 06:00 = sleeping hours
   - Any HR > 110 during sleeping hours + accel < 0.05 = emergency flag
   - Morning (06:00-09:00) + elevated HR = could be just waking up

6. BATTERY CONTEXT
   - Battery < 10% = device may die soon, factor into urgency
   - If user is navigating and battery < 10% = critical situation

7. TREND DETECTION (look across all 10 readings)
   - Is HR consistently rising over last 5 readings? = escalating
   - Did HR spike suddenly in last 1-2 readings? = acute event
   - Has GSR been rising steadily? = building stress
   - Is accel near zero throughout all 10 readings? = prolonged stillness

You must output ONLY valid JSON, no explanation, no markdown:
{
  "primary_state": "one of: sleeping/resting/meditating/walking/running/working/commuting/stressed/distressed/exercising/navigating/unknown",
  "stress_level": "one of: none/low/moderate/high/critical",
  "physical_state": "one of: sedentary/light_activity/moderate_activity/intense_activity",
  "hr_trend": "one of: rising/falling/stable/volatile/spiking",
  "location_context": "one of: home/familiar/unfamiliar/unknown",
  "active_intent": "what is the user intentionally doing right now, max 8 words",
  "anomalies": ["list any concerning signal combinations you detected"],
  "risk_factors": ["list specific reasons this could be dangerous"],
  "suppression_reasons": ["list specific reasons NOT to alert right now"],
  "confidence": "float 0.0 to 1.0 — how confident are you in this profile",
  "reasoning": "3-4 sentences explaining your full analysis"
}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=400,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
Analyze this 30-second window of wearable sensor data.
Most recent reading is T-0, oldest is T-9.

SENSOR WINDOW:
{window_text}

Current time: {telemetry_window[-1].get('time', '12:00')}
Active app: {telemetry_window[-1].get('app', 'idle')}
GPS familiarity: {telemetry_window[-1].get('gps_familiarity', 'unknown')}
Battery: {telemetry_window[-1].get('battery', 100)}%

What is happening with this person right now?
"""}
        ]
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Clean and parse
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    
    parsed = json.loads(raw.strip())
    
    # Ensure float for confidence
    if "confidence" in parsed and isinstance(parsed["confidence"], str):
        try:
            parsed["confidence"] = float(parsed["confidence"])
        except ValueError:
            parsed["confidence"] = 0.5
            
    _cached_profiler_response = parsed
    return parsed

def run_profiler_agent(telemetry_window: list[dict]) -> dict:
    return safe_agent_call(_run_profiler_agent_internal, telemetry_window, fallback=_cached_profiler_response or PROFILER_FALLBACK)

def _run_action_agent_internal(latest_sensor: dict, user_profile: dict, user_note: str, decision_history: list[dict]) -> dict:
    global _cached_action_response
    if not rate_limiter.can_call():
        return _cached_action_response or ACTION_FALLBACK

    history_text = "\n".join([
        f"  {i+1}. {d.get('action','?')} — {d.get('reasoning_short','')}"
        for i, d in enumerate(decision_history[-5:])
    ]) if decision_history else "  No previous decisions"
    
    system_prompt = """
You are the Action Agent in a wearable health AI system.
You are the final decision maker. You decide whether to 
interrupt the user, stay silent, or escalate to emergency.

You think like a brilliant, cautious doctor who deeply 
respects the user's autonomy and attention. You know that:

- FALSE ALERTS destroy trust. A user who gets 5 false 
  alerts will ignore the 6th real one. This can kill them.
- MISSED ALERTS destroy safety. Not alerting during a real 
  cardiac event is catastrophic.
- CONTEXT IS EVERYTHING. The same HR means different things 
  in different situations.

YOUR DECISION FRAMEWORK:

STEP 1 — CHECK FOR ABSOLUTE EMERGENCY (override everything):
  If ALL of these are true simultaneously:
    → HR > 125 AND accel < 0.05 AND app is not fitness/bead_counter
    → Profiler says anomalies detected
    → No exercise context
  Then: EMERGENCY_ALERT. No suppression can override this.
  
  If HR > 140 AND accel < 0.05: EMERGENCY_ALERT always.
  If SpO2 < 92%: EMERGENCY_ALERT always.

STEP 2 — CHECK FOR SUPPRESSION CONTEXTS (these silence alerts):
  Any ONE of these suppresses non-emergency alerts:
    - STAY_SILENT if: user just acknowledged an alert (feedback: "I'M FINE") in the last 2 minutes.
    - STAY_SILENT if: primary_state = "sleeping" [unless HR > 110 AND stress > 70 AND timestamp is night/2AM]
    - EMERGENCY_ALERT if: HR > 130 AND activity = "still" AND stress > 80 AND timestamp is unexpected (e.g. 2AM sleeping).
    - EMERGENCY_ALERT if: HR < 45 AND user is not sleeping.
    - NOTIFY if: HR is moderately elevated (100-120) while still, but only if confidence > 0.8.
    - STAY_SILENT if: active_app = "bead_counter" [user is meditating — NEVER interrupt].
    - STAY_SILENT if: confidence < 0.6 [too much uncertainty].
    - LOG_ONLY: for all other low-risk states.

STEP 3 — ASSESS INTERRUPTION COST:
  High cost (prefer silence):
    - social_risk: user in meeting/interview/important event
    - time = sleeping hours (22:00-06:00)
    - user just dismissed an alert in last 2 minutes
    - profiler says stress_level = moderate (might make it worse)
  
  Low cost (can interrupt):
    - user is idle with no active app
    - user is at home
    - battery is fine
    - time is normal waking hours

STEP 4 — MAKE THE CALL:
  EMERGENCY_ALERT: life-threatening signals, no suppression possible
  URGENT_NOTIFY: serious concern, low interruption cost
  GENTLE_NOTIFY: moderate concern, good time to check in
  STAY_SILENT: suppression context active OR low urgency
  LOG_ONLY: minor signal, just record it

STEP 5 — WRITE YOUR MESSAGE (if alerting):
  - Max 12 words
  - Calm, never panicked (except EMERGENCY)
  - Actionable: tell user what to DO, not just what's happening
  - EMERGENCY only: "Your heart rate is critically high. 
    Tap to call emergency services."

Non-emergency examples:
  - "Your heart rate is elevated. Try taking slow breaths."
  - "Stress detected. You have a 2-minute break due."
  - "Battery critical. Plug in when you can."

You must output ONLY valid JSON, no explanation, no markdown:
{
  "action": "one of: EMERGENCY_ALERT/URGENT_NOTIFY/GENTLE_NOTIFY/STAY_SILENT/LOG_ONLY",
  "message": "message to show user if alerting, null if silent",
  "urgency_score": "float 0.0 to 1.0",
  "suppression_active": true or false,
  "suppression_reason": "why suppressed if applicable, null otherwise",
  "interruption_cost": "one of: low/medium/high/critical",
  "escalation_level": "int 0-4 (0=silent, 4=emergency services)",
  "next_check_seconds": "how many seconds until next evaluation, int",
  "reasoning_short": "one sentence max explaining this decision",
  "reasoning_full": "2-3 sentences with full justification",
  "next_steps": ["list of recommended follow-up actions if any"]
}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0.1,
        max_tokens=350,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"""
LATEST SENSOR READING:
HR: {latest_sensor.get('hr')} BPM
SpO2: {latest_sensor.get('spo2', 98)}%
GSR: {latest_sensor.get('gsr', 2.4)}
Skin Temp: {latest_sensor.get('temp', 36.6)}°C
Movement: {latest_sensor.get('accel', 0.5)}
Active App: {latest_sensor.get('app', 'idle')}
Battery: {latest_sensor.get('battery', 100)}%
Time: {latest_sensor.get('time', '12:00')}
GPS: {latest_sensor.get('gps_familiarity', 'unknown')}

PROFILER AGENT SAYS:
Primary State: {user_profile.get('primary_state', 'unknown')}
Stress Level: {user_profile.get('stress_level', 'unknown')}
HR Trend: {user_profile.get('hr_trend', 'stable')}
Active Intent: {user_profile.get('active_intent', 'unknown')}
Anomalies: {user_profile.get('anomalies', [])}
Risk Factors: {user_profile.get('risk_factors', [])}
Suppression Reasons: {user_profile.get('suppression_reasons', [])}
Confidence: {user_profile.get('confidence', 0.5)}
Profiler Reasoning: {user_profile.get('reasoning', '')}

RELEVANT USER NOTE (IF ANY):
"{user_note or 'No note provided by user.'}"

RECENT DECISION HISTORY:
{history_text}

What action should the system take right now?
"""}
        ]
    )
    
    raw = response.choices[0].message.content.strip()
    
    if "```json" in raw:
        raw = raw.split("```json")[1].split("```")[0]
    elif "```" in raw:
        raw = raw.split("```")[1].split("```")[0]
    
    parsed = json.loads(raw.strip())
    
    # Ensure float for urgency
    if "urgency_score" in parsed and isinstance(parsed["urgency_score"], str):
        try:
            parsed["urgency_score"] = float(parsed["urgency_score"])
        except ValueError:
            parsed["urgency_score"] = 0.5
            
    _cached_action_response = parsed
    return parsed

def run_action_agent(latest_sensor: dict, user_profile: dict, user_note: str, decision_history: list[dict]) -> dict:
    return safe_agent_call(_run_action_agent_internal, latest_sensor, user_profile, user_note, decision_history, fallback=_cached_action_response or ACTION_FALLBACK)

class WearableAgentBrain:
    def __init__(self):
        self.telemetry_window = deque(maxlen=10)
        self.decision_history = []
        self.user_feedback = None  # Stores "I'M FINE" or "CANCELLED"
        self.feedback_time = 0
        # Client initialized globally for rate limiter tracking
        self.llm_enabled = bool(client)
        
    def set_feedback(self, feedback: str):
        self.user_feedback = feedback
        self.feedback_time = time.time()

    def ingest(self, sensor_reading: dict):
        """Call this every 3 seconds with new sensor data"""
        self.telemetry_window.append(sensor_reading)
        
        # Clear feedback after 2 minutes
        if time.time() - self.feedback_time > 120:
            self.user_feedback = None

        # Need at least 3 readings before making decisions
        if len(self.telemetry_window) < 3:
            return {"status": "warming_up", "readings": len(self.telemetry_window)}
        
        # AGENT 1: Profile the user
        profiler_start = time.time()
        user_profile = run_profiler_agent(list(self.telemetry_window))
        profiler_latency = round(time.time() - profiler_start, 3)
        
        # AGENT 2: Decide what to do
        # Add feedback to the "note" field so the agent sees it
        feedback_note = f"USER JUST REPLIED: {self.user_feedback}" if self.user_feedback else ""
        
        action_start = time.time()
        decision = run_action_agent(
            latest_sensor=sensor_reading,
            user_profile=user_profile,
            user_note=feedback_note,
            decision_history=self.decision_history
        )
        action_latency = round(time.time() - action_start, 3)

        
        # Store decision for context in future calls
        self.decision_history.append({
            "timestamp": sensor_reading.get("timestamp"),
            "action": decision.get("action"),
            "reasoning_short": decision.get("reasoning_short"),
            "urgency_score": decision.get("urgency_score")
        })
        
        # Keep only last 20 decisions in memory
        if len(self.decision_history) > 20:
            self.decision_history = self.decision_history[-20:]
        
        return {
            "sensor": sensor_reading,
            "profiler": user_profile,
            "profiler_latency_ms": int(profiler_latency * 1000),
            "decision": decision,
            "action_latency_ms": int(action_latency * 1000),
            "total_latency_ms": int((profiler_latency + action_latency) * 1000),
            "status": "ready"
        }
    
    def get_session_stats(self):
        if not self.decision_history:
            return {}
        actions = [d["action"] for d in self.decision_history]
        suppressed = sum(1 for a in actions if a in ["STAY_SILENT", "LOG_ONLY"])
        alerted = sum(1 for a in actions if a in ["EMERGENCY_ALERT", "URGENT_NOTIFY", "GENTLE_NOTIFY"])
        total = len(actions)
        return {
            "total_decisions": total,
            "suppressed": suppressed,
            "alerted": alerted,
            "suppression_rate": f"{round(suppressed/total*100)}%" if total > 0 else "0%",
            "last_action": actions[-1] if actions else None
        }

    def get_session_summary(self):
        # Maps to the format expected by the API endpoint
        stats = self.get_session_stats()
        return {
            "total_suppressed": stats.get("suppressed", 0),
            "total_alerted": stats.get("alerted", 0),
            "suppression_rate": stats.get("suppression_rate", "0%"),
            "most_common_state": "N/A",  # No longer tracking this simply
            "current_trend": "stable"
        }
        
    def reset(self):
        self.telemetry_window.clear()
        self.decision_history.clear()
