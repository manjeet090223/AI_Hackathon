from models import LLMPrediction

class WearableLLMAgent:
    def __init__(self, model):
        self.model = model

    def analyze_situation(self, profile, sensor_data, state_info):
        advice = "Please take a deep breath." if state_info.urgency == "medium" else "Emergency services will be notified."
        if state_info.urgency == "low":
            advice = "Everything looks normal."
            
        return LLMPrediction(
            personalized_risk=state_info.urgency,
            deviation_detected=state_info.deviation_detected,
            explanation=f"LLM Analyzed: HR is {sensor_data.hr} BPM in context of {sensor_data.app_context}.",
            advice=advice
        )
