import random
from models import StateInfo

class PersonalizedProfiler:
    def __init__(self, memory):
        self.memory = memory

    def evaluate_condition(self, user_id, sensor_data):
        hr = sensor_data.hr
        urgency = "low"
        state = "normal"
        if hr > 150:
            urgency = "high"
            state = "emergency"
        elif hr > 100:
            urgency = "medium"
            state = "stressed"
            
        return StateInfo(
            urgency=urgency,
            deviation_detected=urgency != "low",
            state=state,
            confidence=0.85 + random.uniform(0, 0.1)
        )
