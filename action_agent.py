"""
Action Agent: Decision Engine Module
Decides whether to interrupt user based on profiler output
"""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class ActionType(Enum):
    """Possible actions the system can take"""
    EMERGENCY_ALERT = "EMERGENCY_ALERT"
    URGENT_ALERT = "URGENT_ALERT"
    SILENT_NOTIFICATION = "SILENT_NOTIFICATION"
    DO_NOT_DISTURB = "DO_NOT_DISTURB"
    NO_ACTION = "NO_ACTION"


@dataclass
class Decision:
    """Represents the system's decision"""
    action: str
    reason: str
    notification_text: str = ""
    escalation_level: int = 0  
    next_steps: list = None 

    def __post_init__(self):
        if self.next_steps is None:
            self.next_steps = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "reason": self.reason,
            "notification_text": self.notification_text,
            "escalation_level": self.escalation_level,
            "next_steps": self.next_steps
        }


class ActionAgent:
    """
    Decision engine that determines appropriate action based on user context.
    
    Decision Rules:
    - urgency > 8 → EMERGENCY ALERT
    - app = maps & low battery → DO NOT DISTURB
    - state = sleeping → block notifications
    - otherwise → NO ACTION or SILENT notification
    """

    def __init__(self):
        self.decision_history: List[Decision] = []

    def decide(self, sensor_data: Dict[str, Any], profile: Dict[str, Any]) -> Decision:
        """
        Make action decision based on profiler output.
        
        Input:
        - sensor_data: raw sensor data
        - profile: UserProfile.to_dict() from profiler agent
        
        Returns: Decision with action type and reasoning
        """
        state = profile.get("state")
        urgency = profile.get("urgency", 0)
        reason = profile.get("reason", "")
        app = sensor_data.get("app", "idle")
        battery = sensor_data.get("battery", 100)
        hr = sensor_data.get("hr", 0)

       
        if state == "emergency" or urgency >= 10:
            decision = Decision(
                action="🚨 EMERGENCY_ALERT",
                reason=f"CRITICAL CONDITION DETECTED (Urgency: {urgency}/10): {reason}",
                notification_text=f"⚠️ EMERGENCY: Heart rate critical at {hr} BPM with minimal movement. Seek immediate help if experiencing chest pain or difficulty breathing.",
                escalation_level=4,
                next_steps=["Contact Emergency Services", "Alert Emergency Contacts", "Log Vital Signs"]
            )
            self.decision_history.append(decision)
            return decision


        if state == "sleeping":
            decision = Decision(
                action=ActionType.DO_NOT_DISTURB.value,
                reason="User is sleeping. Silencing all non-critical notifications.",
                notification_text="",
                escalation_level=0
            )
            self.decision_history.append(decision)
            return decision


        if state == "navigating_low_battery" or (app.lower() == "maps" and battery < 10):
            decision = Decision(
                action=ActionType.DO_NOT_DISTURB.value,
                reason=f"User navigating with critical battery ({battery}%). Avoiding distractions to ensure safety.",
                notification_text="",
                escalation_level=0
            )
            self.decision_history.append(decision)
            return decision


        if 6 <= urgency < 10:
            decision = Decision(
                action=ActionType.URGENT_ALERT.value,
                reason=f"High urgency detected (Urgency: {urgency}/10). {reason}",
                notification_text=self._generate_urgent_notification(state, urgency),
                escalation_level=3
            )
            self.decision_history.append(decision)
            return decision


        if 3 <= urgency < 6:
            decision = Decision(
                action=ActionType.SILENT_NOTIFICATION.value,
                reason=f"Moderate urgency ({urgency}/10). Logging to history without vibration/sound.",
                notification_text=self._generate_silent_notification(state, urgency),
                escalation_level=1
            )
            self.decision_history.append(decision)
            return decision


        decision = Decision(
            action=ActionType.NO_ACTION.value,
            reason=f"Low urgency ({urgency}/10). Normal operation - system silent.",
            notification_text="",
            escalation_level=0
        )
        self.decision_history.append(decision)
        return decision

    def _generate_urgent_notification(self, state: str, urgency: int) -> str:
        """Generate text for urgent alerts"""
        messages = {
            "stressed": "🔴 Your stress levels are elevated. Take a moment to breathe.",
            "elevated_alert": "🔴 Elevated heart rate detected. Check your well-being.",
            "navigating": "🔴 Warning: Distracted driving detected. Focus on the road.",
            "low_battery": "🔴 Battery critically low. Consider charging soon.",
            "exercising": "🟡 High activity detected. Stay hydrated.",
        }
        return messages.get(state, f"🔴 Alert: {state} detected (Urgency: {urgency}/10)")

    def _generate_silent_notification(self, state: str, urgency: int) -> str:
        """Generate text for silent notifications"""
        messages = {
            "exercising": "💪 Great workout! Keep it up.",
            "navigating": "🧭 Navigation active. Route optimized.",
            "low_battery": "🔋 Battery at 15%. Consider charging.",
        }
        return messages.get(state, f"ℹ️ {state} (Urgency: {urgency}/10)")

    def get_context_summary(self) -> Dict[str, Any]:
        """Get summary of recent decisions"""
        if not self.decision_history:
            return {"total_decisions": 0}

        action_counts = {}
        for decision in self.decision_history:
            action = decision.action
            action_counts[action] = action_counts.get(action, 0) + 1

        return {
            "total_decisions": len(self.decision_history),
            "action_distribution": action_counts,
            "last_decision": self.decision_history[-1].to_dict()
        }

    def reset_history(self):
        """Clear decision history"""
        self.decision_history.clear()

from models import ActionDecision

class AdaptiveActionAgent:
    def __init__(self, memory):
        self.memory = memory

    def decide(self, user_id, state_info, llm_pred) -> ActionDecision:
        advice = "Monitoring contextually..."
        if llm_pred:
            advice = llm_pred.advice
        return ActionDecision(advice=advice)

