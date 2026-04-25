import random
from models import StateInfo

class PersonalizedProfiler:
    def __init__(self, memory):
        self.memory = memory
        self.normal_reading_buffer = []

    def evaluate_condition(self, user_id, sensor_data, profile):
        hr = sensor_data.hr
        
        stress_threshold = profile.avg_resting_hr * profile.hr_stress_multiplier
        emergency_threshold = profile.avg_resting_hr * profile.hr_emergency_multiplier
        
        urgency = "low"
        state = "normal"
        if hr > emergency_threshold:
            urgency = "high"
            state = "emergency"
        elif hr > stress_threshold:
            urgency = "medium"
            state = "stressed"
        
        if state == "normal":
            self.normal_reading_buffer.append(hr)
            if len(self.normal_reading_buffer) >= 20:
                profile.avg_resting_hr = int(sum(self.normal_reading_buffer) / 20)
                self.normal_reading_buffer = []
            
        return StateInfo(
            urgency=urgency,
            deviation_detected=urgency != "low",
            state=state,
            confidence=0.85 + random.uniform(0, 0.1)
        )
