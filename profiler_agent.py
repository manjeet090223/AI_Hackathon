"""
Profiler Agent: Context Understanding Module
Converts raw sensor data into meaningful user state
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple


@dataclass
class UserProfile:
    """Represents the user's current profile"""
    state: str
    urgency: int
    reason: str
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state,
            "urgency": self.urgency,
            "reason": self.reason,
            "confidence": self.confidence
        }


class ProfilerAgent:
    """
    Analyzes sensor data and builds context-aware user profiles.
    
    Rules:
    - High HR + low movement → abnormal / stress
    - High HR + high movement → physical activity
    - Low movement + sleep app → sleeping
    - Maps app + low battery → driving/navigation
    """

    def __init__(self):
        self.hr_baseline = 60  
        self.hr_max_normal = 100  
        self.hr_stress = 120 
        self.hr_emergency = 120  
        self.emergency_movement_threshold = 0.1  

    def _classify_heart_rate(self, hr: int) -> Tuple[str, int]:
        """
        Classify heart rate and return state + base urgency.
        Returns: (hr_state, urgency_points)
        """
        if hr < self.hr_baseline:
            return "low_hr", 1
        elif hr <= self.hr_max_normal:
            return "normal_hr", 1
        elif hr <= self.hr_stress:
            return "elevated_hr", 4
        elif hr < self.hr_emergency:
            return "high_hr", 7
        else:
            return "critical_hr", 10

    def _classify_movement(self, movement: float) -> Tuple[str, int]:
        """
        Classify movement level.
        Returns: (movement_state, urgency_points)
        """
        if movement < 0.1:
            return "stationary", 0
        elif movement < 0.3:
            return "low_movement", 1
        elif movement < 0.6:
            return "moderate_movement", 2
        else:
            return "high_movement", 3

    def _classify_battery(self, battery: int) -> str:
        """Classify battery level"""
        if battery > 50:
            return "good"
        elif battery > 20:
            return "medium"
        else:
            return "critical"

    def _infer_app_context(self, app: str) -> Tuple[str, str]:
        """
        Map app to context. Returns: (context, description)
        """
        app_contexts = {
            "sleep": ("sleeping", "User in sleep mode"),
            "maps": ("navigating", "User actively navigating"),
            "fitness": ("exercising", "User in fitness app"),
            "work": ("focused", "User in work application"),
            "idle": ("idle", "Device idle"),
        }
        return app_contexts.get(app.lower(), ("unknown", f"Using {app}"))

    def profile(self, sensor_data: Dict[str, Any]) -> UserProfile:
        """
        Convert raw sensor data into user profile.
        
        Input:
        {
            "hr": int,
            "movement": float,
            "app": str,
            "battery": int
        }
        
        Returns: UserProfile with state, urgency, and reason
        """
        hr = sensor_data.get("hr", 0)
        movement = sensor_data.get("movement", 0.0)
        app = sensor_data.get("app", "idle")
        battery = sensor_data.get("battery", 100)


        hr_state, hr_urgency = self._classify_heart_rate(hr)
        movement_state, movement_urgency = self._classify_movement(movement)
        battery_state = self._classify_battery(battery)
        app_context, app_reason = self._infer_app_context(app)


        state, urgency, reason = self._combine_signals(
            hr, movement, battery, app,
            hr_state, movement_state, battery_state, app_context
        )


        confidence = self._calculate_confidence(state, hr, movement, app)

        return UserProfile(state=state, urgency=urgency, reason=reason, confidence=confidence)

    def _combine_signals(self, hr: int, movement: float, battery: int, app: str,
                         hr_state: str, movement_state: str, battery_state: str,
                         app_context: str) -> Tuple[str, int, str]:
        """
        Combine multiple signals to determine overall state and urgency.
        Returns: (state, urgency, reason)
        """
        urgency = 0
        reasons = []


        if app_context == "sleeping" and movement < 0.1 and hr < 80:
            state = "sleeping"
            urgency = 1
            reasons.append("Sleep app detected with low movement and HR")
            return state, urgency, " | ".join(reasons)


        if hr >= self.hr_emergency and movement < self.emergency_movement_threshold:
            state = "emergency"
            urgency = 10
            reasons.append(f"CRITICAL: Heart rate {hr} BPM with minimal movement ({movement:.2f}) - potential medical emergency")
            return state, urgency, " | ".join(reasons)


        if hr > 100 and movement > 0.4:
            state = "exercising"
            urgency = 2
            reasons.append(f"Physical activity detected (HR: {hr}, Movement: {movement:.2f})")
            return state, urgency, " | ".join(reasons)


        if hr > 110 and movement < 0.3:
            state = "stressed"
            urgency = 6
            reasons.append(f"Elevated HR {hr} with minimal movement")
            return state, urgency, " | ".join(reasons)


        if app_context == "navigating" and battery < 10:
            state = "navigating_low_battery"
            urgency = 7
            reasons.append("Actively navigating with critical battery (DO NOT DISTURB)")
            return state, urgency, " | ".join(reasons)


        if app_context == "navigating":
            state = "navigating"
            urgency = 5
            reasons.append("User navigating - high context focus required")
            return state, urgency, " | ".join(reasons)


        if hr > self.hr_stress:
            state = "elevated_alert"
            urgency = 5
            reasons.append(f"Elevated heart rate {hr} BPM")
            return state, urgency, " | ".join(reasons)


        if battery < 15:
            state = "low_battery"
            urgency = 4
            reasons.append(f"Battery critical at {battery}%")
            return state, urgency, " | ".join(reasons)


        state = "normal"
        urgency = 1
        reasons.append(f"Normal state (HR: {hr}, Movement: {movement:.2f}, App: {app})")
        return state, urgency, " | ".join(reasons)

    def _calculate_confidence(self, state: str, hr: int, movement: float, app: str) -> float:
        """
        Calculate confidence score using weighted factor analysis.
        
        Returns confidence between 0.0 and 1.0 (rounded to 2 decimal places).
        Higher confidence when signals strongly align with detected state.
        
        Scoring factors:
        - Heart rate alignment with state
        - Movement pattern alignment
        - App context confirmation
        """
        confidence = 0.0
        

        if state == "emergency":
            if hr >= 120:
                confidence += 0.4
            if movement < 0.1:
                confidence += 0.3
            if movement < 0.05:
                confidence += 0.1
        

        elif state == "stressed":
            if hr > 110:
                confidence += 0.3
            if hr > 100:
                confidence += 0.1
            if movement < 0.3:
                confidence += 0.2
            if movement < 0.15:
                confidence += 0.1
        

        elif state == "exercising":
            if movement > 0.7:
                confidence += 0.3
            if movement > 0.5:
                confidence += 0.1
            if hr > 100:
                confidence += 0.2
            if 140 <= hr <= 180:
                confidence += 0.1
        

        elif state == "sleeping":
            if app.lower() == "sleep":
                confidence += 0.3
            if movement < 0.1:
                confidence += 0.2
            if hr < 80:
                confidence += 0.2
        

        elif state in ["navigating", "navigating_low_battery"]:
            if app.lower() == "maps":
                confidence += 0.3
            if 0.2 <= movement <= 0.5:  
                confidence += 0.2
        

        elif state == "normal":
            if 60 <= hr <= 90:
                confidence += 0.3
            if 0.1 <= movement <= 0.4:
                confidence += 0.2
            if app.lower() in ["idle", "work"]:
                confidence += 0.15
        

        confidence = min(1.0, max(0.0, confidence))
        return round(confidence, 2)
