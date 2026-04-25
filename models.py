from dataclasses import dataclass
from typing import List

@dataclass
class UserProfile:
    user_id: str
    avg_resting_hr: int
    sleep_time: str
    wake_time: str
    recent_hr: List[int]

@dataclass
class SensorData:
    timestamp: str
    hr: int
    movement: str
    app_context: str

@dataclass
class StateInfo:
    urgency: str
    deviation_detected: bool
    state: str
    confidence: float

@dataclass
class LLMPrediction:
    personalized_risk: str
    deviation_detected: bool
    explanation: str
    advice: str

@dataclass
class ActionDecision:
    advice: str
