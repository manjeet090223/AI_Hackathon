"""
LLM Reasoner Agent: Phase 2 Enhancement
Integrates Groq LLM for intelligent health analysis and decision-making.

This module enhances the rule-based system by leveraging LLM reasoning
for ambiguous cases, providing natural explanations, and health suggestions.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time


@dataclass
class LLMResponse:
    """Structure for LLM reasoning output"""
    final_state: str
    risk_level: str  # low, medium, high, critical
    explanation: str
    advice: str
    should_alert: bool
    confidence: float = 0.0
    reasoning_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "final_state": self.final_state,
            "risk_level": self.risk_level,
            "explanation": self.explanation,
            "advice": self.advice,
            "should_alert": self.should_alert,
            "confidence": self.confidence,
            "reasoning_time": round(self.reasoning_time, 3)
        }


class LLMReasonerAgent:
    """
    Health intelligence reasoner using Groq LLM.
    
    Provides context-aware analysis for:
    - Ambiguous health states
    - Risk assessment
    - Personalized health suggestions
    - Natural explanations for decisions
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "mixtral-8x7b-32768"):
        """
        Initialize LLM reasoner.
        
        Args:
            api_key: Groq API key (defaults to GROQ_API_KEY env var)
            model: LLM model to use (default: mixtral-8x7b-32768 - currently active)
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.call_history = []
        
        # Import Groq client
        try:
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.llm_available = True
        except (ImportError, ValueError) as e:
            print(f"⚠️ Warning: Groq LLM not available. Falling back to rule-based system.")
            print(f"   Error: {e}")
            self.llm_available = False
            self.client = None

    def reason(self, sensor_data: Dict[str, Any], profile: Dict[str, Any]) -> Optional[LLMResponse]:
        """
        Use LLM to reason about health condition.
        
        Args:
            sensor_data: Raw sensor readings {hr, movement, app, battery}
            profile: Rule-based profile {state, urgency, confidence, reason}
        
        Returns:
            LLMResponse with reasoning output, or None if LLM unavailable
        """
        if not self.llm_available or not self.client:
            return None

        try:
            start_time = time.time()
            
            # Build structured prompt
            prompt = self._build_prompt(sensor_data, profile)
            
            # Call Groq LLM (using chat completion API)
            message = self.client.chat.completions.create(
                model=self.model,
                max_tokens=300,
                temperature=0.2,  # Low temperature for consistency
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            # Parse response
            response_text = message.choices[0].message.content.strip()
            llm_response = self._parse_llm_response(response_text, time.time() - start_time)
            
            # Store in history
            self.call_history.append({
                "input": {"sensor_data": sensor_data, "profile": profile},
                "output": llm_response.to_dict(),
                "timestamp": time.time()
            })
            
            return llm_response
            
        except Exception as e:
            print(f"⚠️ LLM Error: {e}. Falling back to rule-based decision.")
            return None

    def _build_prompt(self, sensor_data: Dict[str, Any], profile: Dict[str, Any]) -> str:
        """Build structured prompt for LLM analysis."""
        hr = sensor_data.get("hr", 0)
        movement = sensor_data.get("movement", 0.0)
        app = sensor_data.get("app", "idle")
        battery = sensor_data.get("battery", 100)
        
        state = profile.get("state", "unknown")
        urgency = profile.get("urgency", 0)
        confidence = profile.get("confidence", 0.0)
        reason = profile.get("reason", "")
        
        prompt = f"""You are an intelligent wearable health assistant analyzing user health data.

USER'S CURRENT DATA:
- Heart Rate: {hr} BPM
- Movement Level: {movement:.2f} (0=stationary, 1=high activity)
- Active App: {app}
- Device Battery: {battery}%

SYSTEM'S INITIAL PREDICTION:
- Detected State: {state}
- Urgency Level: {urgency}/10
- Confidence: {confidence:.1%}
- Reason: {reason}

YOUR ANALYSIS TASKS:
1. Validate or refine the system's prediction
2. Assess true risk level
3. Explain your assessment briefly
4. Provide actionable health advice
5. Determine if alert should be sent

CONTEXT RULES:
- Emergency: HR >= 120 + minimal movement (<0.1) = potential medical issue
- Stress: HR > 110 + low movement (<0.3) = mental/emotional stress
- Exercise: HR > 100 + high movement (>0.7) = expected cardiovascular response
- Normal: HR 60-90 + moderate movement = baseline health

RESPOND WITH ONLY VALID JSON (no markdown, no explanations):
{{
  "final_state": "state name",
  "risk_level": "low|medium|high|critical",
  "explanation": "brief assessment",
  "advice": "actionable suggestion",
  "should_alert": true/false
}}"""
        return prompt

    def _parse_llm_response(self, response_text: str, reasoning_time: float) -> LLMResponse:
        """
        Parse LLM JSON response into structured format.
        
        Args:
            response_text: Raw response from LLM
            reasoning_time: Time taken for LLM call
        
        Returns:
            LLMResponse object
        """
        try:
            # Extract JSON from response (handles markdown code blocks)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]
            
            data = json.loads(response_text.strip())
            
            # Validate required fields
            required_fields = ["final_state", "risk_level", "explanation", "advice", "should_alert"]
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Map risk level to confidence
            risk_confidence = {
                "low": 0.2,
                "medium": 0.5,
                "high": 0.8,
                "critical": 1.0
            }
            
            confidence = risk_confidence.get(data["risk_level"].lower(), 0.5)
            
            return LLMResponse(
                final_state=str(data["final_state"]).lower().strip(),
                risk_level=str(data["risk_level"]).lower().strip(),
                explanation=str(data["explanation"]).strip(),
                advice=str(data["advice"]).strip(),
                should_alert=bool(data["should_alert"]),
                confidence=confidence,
                reasoning_time=reasoning_time
            )
        except (json.JSONDecodeError, ValueError, KeyError, IndexError) as e:
            print(f"⚠️ Failed to parse LLM response: {e}")
            # Return safe default
            return LLMResponse(
                final_state="unknown",
                risk_level="medium",
                explanation="LLM analysis inconclusive",
                advice="Continue monitoring",
                should_alert=False,
                confidence=0.3,
                reasoning_time=reasoning_time
            )

    def should_use_llm(self, profile: Dict[str, Any]) -> bool:
        """
        Determine if LLM reasoning should be used.
        
        Use LLM when:
        - Confidence is low (< 0.6)
        - State is ambiguous (stressed, borderline)
        - Manual review recommended
        
        Args:
            profile: Rule-based profile
        
        Returns:
            True if LLM reasoning should be invoked
        """
        confidence = profile.get("confidence", 1.0)
        state = profile.get("state", "")
        urgency = profile.get("urgency", 0)
        
        # Use LLM for low-confidence cases
        if confidence < 0.6:
            return True
        
        # Use LLM for ambiguous states
        ambiguous_states = ["stressed", "elevated_alert", "unknown"]
        if state in ambiguous_states:
            return True
        
        # Use LLM for medium urgency (6-8) to validate before alerting
        if 6 <= urgency < 10:
            return True
        
        return False

    def get_llm_history(self, limit: int = 10) -> list:
        """Get recent LLM reasoning calls for analysis."""
        return self.call_history[-limit:]

    def clear_history(self):
        """Clear LLM call history."""
        self.call_history.clear()


class HybridDecisionEngine:
    """
    Combines rule-based system with LLM reasoning for optimal decisions.
    
    Architecture:
    1. Fast rule-based classification
    2. Selective LLM enhancement for ambiguous cases
    3. Decision merging and final output
    """

    def __init__(self, profiler, action_agent, llm_reasoner):
        """
        Initialize hybrid decision engine.
        
        Args:
            profiler: ProfilerAgent instance
            action_agent: ActionAgent instance
            llm_reasoner: LLMReasonerAgent instance
        """
        self.profiler = profiler
        self.action_agent = action_agent
        self.llm_reasoner = llm_reasoner
        self.decision_history = []

    def decide(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make hybrid decision with optional LLM enhancement.
        
        Pipeline:
        1. Get rule-based profile (fast)
        2. Check if LLM reasoning needed
        3. If yes, call LLM for context
        4. Merge decisions
        5. Generate final action
        
        Args:
            sensor_data: Raw sensor readings
        
        Returns:
            Complete decision output with explanations
        """
        # Step 1: Rule-based analysis (always)
        rule_profile = self.profiler.profile(sensor_data)
        rule_decision = self.action_agent.decide(sensor_data, rule_profile.to_dict())
        
        # Step 2: Determine if LLM reasoning needed
        use_llm = self.llm_reasoner.should_use_llm(rule_profile.to_dict())
        
        llm_response = None
        final_decision = rule_decision
        
        # Step 3: Call LLM if needed
        if use_llm:
            llm_response = self.llm_reasoner.reason(sensor_data, rule_profile.to_dict())
            
            # Step 4: Merge decisions if LLM available
            if llm_response:
                final_decision = self._merge_decisions(
                    rule_decision,
                    rule_profile.to_dict(),
                    llm_response,
                    sensor_data
                )
        
        # Step 5: Create output
        output = {
            "timestamp": time.time(),
            "input": sensor_data,
            "rule_based": {
                "state": rule_profile.state,
                "urgency": rule_profile.urgency,
                "confidence": rule_profile.confidence,
                "reason": rule_profile.reason,
                "action": rule_decision.action
            },
            "llm_enhanced": llm_response.to_dict() if llm_response else None,
            "final_decision": final_decision.to_dict(),
            "hybrid_reasoning": use_llm
        }
        
        # Store in history
        self.decision_history.append(output)
        
        return output

    def _merge_decisions(self, rule_decision, rule_profile, llm_response, sensor_data) -> Any:
        """
        Merge rule-based and LLM decisions intelligently.
        
        Priority logic:
        1. If LLM risk is "critical" → EMERGENCY
        2. If LLM risk is "high" → URGENT
        3. If LLM suggests alert → notification
        4. Otherwise → no action
        """
        from action_agent import Decision
        
        hr = sensor_data.get("hr", 0)
        risk_level = llm_response.risk_level
        
        # Critical emergency
        if risk_level == "critical":
            return Decision(
                action="🚨 EMERGENCY_ALERT (LLM Validated)",
                reason=f"LLM Risk Assessment: {llm_response.explanation}",
                notification_text=f"⚠️ EMERGENCY: {llm_response.advice}",
                escalation_level=4,
                next_steps=["Contact Emergency Services", "Alert Emergency Contacts"]
            )
        
        # High risk warning
        elif risk_level == "high":
            return Decision(
                action="🔴 URGENT_ALERT (LLM Enhanced)",
                reason=f"LLM Assessment: {llm_response.explanation}",
                notification_text=f"Alert: {llm_response.advice}",
                escalation_level=3,
                next_steps=[]
            )
        
        # Should alert but not critical
        elif llm_response.should_alert:
            return Decision(
                action="🟡 NOTIFICATION (LLM Recommended)",
                reason=f"LLM Insight: {llm_response.explanation}",
                notification_text=f"Suggestion: {llm_response.advice}",
                escalation_level=1,
                next_steps=[]
            )
        
        # LLM says no action needed
        else:
            return Decision(
                action="✅ NO_ACTION (LLM Confirmed)",
                reason=f"LLM Assessment: {llm_response.explanation}",
                notification_text="",
                escalation_level=0,
                next_steps=[]
            )

    def get_decision_summary(self, limit: int = 10) -> Dict[str, Any]:
        """Get summary of recent hybrid decisions."""
        recent = self.decision_history[-limit:]
        
        llm_used_count = sum(1 for d in recent if d.get("hybrid_reasoning"))
        
        return {
            "total_decisions": len(self.decision_history),
            "recent_count": len(recent),
            "llm_used": llm_used_count,
            "llm_usage_rate": f"{(llm_used_count/len(recent)*100):.1f}%" if recent else "0%",
            "recent_decisions": recent
        }
