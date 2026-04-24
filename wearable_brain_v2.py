"""
Wearable Context Brain - Phase 2: Hybrid Intelligence System
Combines rule-based profiler with Groq LLM for enhanced health insights.

Architecture:
Sensor Data → Rule-Based Profiler → [LLM Enhancement if needed] → Action → Output
"""

import json
import time
from typing import Dict, Any, List
from profiler_agent import ProfilerAgent, UserProfile
from action_agent import ActionAgent, Decision
from llm_reasoner import LLMReasonerAgent, HybridDecisionEngine


class WearableContextBrainV2:
    """
    Phase 2: Hybrid intelligence system combining rules and LLM.
    
    Enhanced capabilities:
    - Rule-based fast decisions for clear cases
    - LLM reasoning for ambiguous situations
    - Natural health explanations
    - Personalized health suggestions
    """

    def __init__(self, use_llm: bool = True, groq_api_key: str = None):
        self.profiler = ProfilerAgent()
        self.action_agent = ActionAgent()
        
        # Initialize LLM reasoner (optional, with fallback)
        self.llm_reasoner = LLMReasonerAgent(api_key=groq_api_key) if use_llm else None
        
        # Hybrid decision engine
        self.hybrid_engine = HybridDecisionEngine(
            self.profiler,
            self.action_agent,
            self.llm_reasoner
        ) if self.llm_reasoner else None
        
        self.processing_history: List[Dict[str, Any]] = []
        self.llm_enabled = use_llm and self.llm_reasoner and self.llm_reasoner.llm_available

    def process(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sensor data through hybrid intelligence pipeline.
        
        Returns complete output with rule-based and LLM analysis.
        """
        if self.llm_enabled and self.hybrid_engine:
            # Use hybrid decision engine
            output = self.hybrid_engine.decide(sensor_data)
        else:
            # Fallback to rule-based only
            profile: UserProfile = self.profiler.profile(sensor_data)
            decision: Decision = self.action_agent.decide(sensor_data, profile.to_dict())
            
            output = {
                "timestamp": time.time(),
                "input": sensor_data,
                "rule_based": {
                    "state": profile.state,
                    "urgency": profile.urgency,
                    "confidence": profile.confidence,
                    "reason": profile.reason,
                    "action": decision.action
                },
                "llm_enhanced": None,
                "final_decision": decision.to_dict(),
                "hybrid_reasoning": False
            }
        
        # Store in history
        self.processing_history.append(output)
        return output

    def format_output(self, output: Dict[str, Any]) -> str:
        """Format output for readable console display."""
        return json.dumps(output, indent=2)

    def get_system_summary(self) -> Dict[str, Any]:
        """Get overall system performance summary."""
        return {
            "total_processed": len(self.processing_history),
            "llm_enabled": self.llm_enabled,
            "rule_based_only_count": sum(1 for o in self.processing_history if not o.get("hybrid_reasoning")),
            "hybrid_count": sum(1 for o in self.processing_history if o.get("hybrid_reasoning")),
            "most_common_states": self._get_most_common_states(),
            "llm_stats": self._get_llm_stats() if self.llm_enabled else None
        }

    def _get_most_common_states(self) -> Dict[str, int]:
        """Track most common user states detected."""
        state_counts = {}
        for entry in self.processing_history:
            state = entry["rule_based"]["state"]
            state_counts[state] = state_counts.get(state, 0) + 1
        return dict(sorted(state_counts.items(), key=lambda x: x[1], reverse=True))

    def _get_llm_stats(self) -> Dict[str, Any]:
        """Get LLM usage statistics."""
        if not self.llm_reasoner:
            return None
        
        history = self.llm_reasoner.get_llm_history(limit=100)
        if not history:
            return {"calls": 0}
        
        avg_time = sum(h["output"]["reasoning_time"] for h in history) / len(history)
        
        return {
            "total_calls": len(self.llm_reasoner.call_history),
            "recent_calls": len(history),
            "avg_reasoning_time": round(avg_time, 3),
            "recent_reasoning_times": [h["output"]["reasoning_time"] for h in history[-5:]]
        }

    def reset(self):
        """Reset system state."""
        self.processing_history.clear()
        self.action_agent.reset_history()
        if self.llm_reasoner:
            self.llm_reasoner.clear_history()


class ScenarioSimulator:
    """
    Simulates real-time wearable data with predefined scenarios.
    Enhanced for Phase 2 testing with hybrid intelligence.
    """

    SCENARIOS = {
        "scenario_1_sleeping": {
            "name": "Sleeping",
            "description": "User in sleep mode with low HR and minimal movement",
            "data": {
                "hr": 65,
                "movement": 0.05,
                "battery": 80,
                "app": "sleep"
            }
        },
        "scenario_2_navigation": {
            "name": "Navigation (Low Battery)",
            "description": "User navigating with critical battery - DO NOT DISTURB",
            "data": {
                "hr": 90,
                "movement": 0.3,
                "battery": 8,
                "app": "maps"
            }
        },
        "scenario_3_emergency": {
            "name": "Emergency Alert",
            "description": "Critical HR with minimal movement - potential medical emergency",
            "data": {
                "hr": 130,
                "movement": 0.01,
                "battery": 50,
                "app": "idle"
            }
        },
        "scenario_4_exercise": {
            "name": "Exercising",
            "description": "Physical activity with high HR and movement",
            "data": {
                "hr": 140,
                "movement": 0.75,
                "battery": 60,
                "app": "fitness"
            }
        },
        "scenario_5_stress": {
            "name": "Stress Detection",
            "description": "Elevated HR with low movement - stress/anxiety",
            "data": {
                "hr": 115,
                "movement": 0.15,
                "battery": 45,
                "app": "work"
            }
        },
        "scenario_6_normal": {
            "name": "Normal Activity",
            "description": "Normal baseline - no alerts needed",
            "data": {
                "hr": 75,
                "movement": 0.25,
                "battery": 70,
                "app": "idle"
            }
        }
    }

    @staticmethod
    def run_all_scenarios(brain: WearableContextBrainV2) -> List[Dict[str, Any]]:
        """
        Run all predefined scenarios through the hybrid system.
        Returns list of outputs for each scenario.
        """
        results = []
        for scenario_key, scenario_info in ScenarioSimulator.SCENARIOS.items():
            print(f"\n{'='*80}")
            print(f"Running: {scenario_info['name']}")
            print(f"Description: {scenario_info['description']}")
            print(f"{'='*80}\n")

            output = brain.process(scenario_info["data"])
            results.append({
                "scenario": scenario_info["name"],
                "output": output
            })

            # Pretty print output
            print(brain.format_output(output))

        return results

    @staticmethod
    def run_continuous_simulation(brain: WearableContextBrainV2, duration: int = 10, interval: float = 2.0):
        """
        Simulate real-time sensor stream continuously with hybrid intelligence.
        
        Args:
            brain: WearableContextBrainV2 instance
            duration: Total simulation duration in seconds
            interval: Time between sensor readings in seconds
        """
        print(f"\n{'='*80}")
        print("CONTINUOUS REAL-TIME SIMULATION (HYBRID INTELLIGENCE)")
        print(f"Duration: {duration}s, Interval: {interval}s")
        print(f"{'='*80}\n")

        start_time = time.time()
        iteration = 0

        # Rotate through scenarios
        scenario_keys = list(ScenarioSimulator.SCENARIOS.keys())

        while time.time() - start_time < duration:
            iteration += 1
            scenario_key = scenario_keys[iteration % len(scenario_keys)]
            scenario_info = ScenarioSimulator.SCENARIOS[scenario_key]

            output = brain.process(scenario_info["data"])
            
            # Compact display
            state = output['rule_based']['state']
            urgency = output['rule_based']['urgency']
            action = output['final_decision']['action']
            hybrid = "🧠 LLM" if output.get('hybrid_reasoning') else "⚡ Rule"
            
            print(f"[{iteration}] {hybrid} | State: {state:20} | Urgency: {urgency:2}/10 | Action: {action}")

            time.sleep(interval)

        print(f"\n{'='*80}")
        print("SIMULATION COMPLETE")
        print(f"Processed: {len(brain.processing_history)} readings")
        print(f"{'='*80}\n")


def main():
    """Main execution with Phase 2 hybrid intelligence."""
    print("\n" + "="*80)
    print("WEARABLE CONTEXT BRAIN - Phase 2: Hybrid Intelligence System")
    print("Rule-Based Profiler + Groq LLM Integration")
    print("="*80)

    # Initialize system (LLM is optional, will fallback if not available)
    brain = WearableContextBrainV2(use_llm=True)
    
    if brain.llm_enabled:
        print("\n✅ LLM Integration: ENABLED (Groq API)")
        print("   Model: llama-3.1-70b-versatile")
        print("   LLM will enhance ambiguous cases with health reasoning")
    else:
        print("\n⚠️ LLM Integration: DISABLED (Fallback to Rule-Based)")
        print("   Ensure GROQ_API_KEY env var is set for LLM features")

    # Phase 1: Scenario Testing with Hybrid Intelligence
    print("\n" + "-" * 80)
    print("Phase 1: Scenario Testing (Hybrid Intelligence)")
    print("-" * 80)
    results = ScenarioSimulator.run_all_scenarios(brain)

    # System Summary after Phase 1
    print("\n" + "="*80)
    print("PHASE 1 SUMMARY")
    print("="*80)
    summary = brain.get_system_summary()
    print(json.dumps(summary, indent=2))

    # Phase 2: Continuous Simulation
    print("\n" + "-" * 80)
    print("Phase 2: Continuous Real-Time Simulation")
    print("-" * 80)
    brain.reset()  # Clear history for fresh simulation
    ScenarioSimulator.run_continuous_simulation(brain, duration=15, interval=1.0)

    # Final Summary
    print("\n" + "="*80)
    print("FINAL SYSTEM SUMMARY")
    print("="*80)
    final_summary = brain.get_system_summary()
    print(json.dumps(final_summary, indent=2))

    print("\n✅ Phase 2 System completed successfully!")
    print("\nNext Steps:")
    print("1. Set GROQ_API_KEY environment variable for full LLM features")
    print("2. Review LLM outputs for ambiguous cases in logs")
    print("3. Fine-tune LLM prompts based on real-world feedback")
    print("4. Monitor decision accuracy and false alarm rates")


if __name__ == "__main__":
    main()
