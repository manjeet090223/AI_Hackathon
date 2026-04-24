"""
Wearable Context Brain - Main System
Real-time multi-agent intelligence for wearable devices
"""

import json
import time
from typing import Dict, Any, List
from profiler_agent import ProfilerAgent, UserProfile
from action_agent import ActionAgent, Decision


class WearableContextBrain:
    """
    Multi-agent intelligence system for wearable devices.
    
    Architecture:
    Sensor Stream → Profiler Agent → Action Agent → Output
    """

    def __init__(self):
        self.profiler = ProfilerAgent()
        self.action_agent = ActionAgent()
        self.processing_history: List[Dict[str, Any]] = []

    def process(self, sensor_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process sensor data through the multi-agent system.
        
        Returns complete output with input, profile, and decision.
        """
        # Stage 1: Profiler Agent - Context Understanding
        profile: UserProfile = self.profiler.profile(sensor_data)

        # Stage 2: Action Agent - Decision Making
        decision: Decision = self.action_agent.decide(sensor_data, profile.to_dict())

        # Compile output
        output = {
            "timestamp": time.time(),
            "input": sensor_data,
            "profile": profile.to_dict(),
            "decision": decision.to_dict()
        }

        # Store in history
        self.processing_history.append(output)

        return output

    def format_output(self, output: Dict[str, Any]) -> str:
        """Format output for readable console display"""
        return json.dumps(output, indent=2)

    def get_system_summary(self) -> Dict[str, Any]:
        """Get overall system performance summary"""
        return {
            "total_processed": len(self.processing_history),
            "profiler_confidence": self._avg_confidence(),
            "action_distribution": self.action_agent.get_context_summary(),
            "most_common_states": self._get_most_common_states()
        }

    def _avg_confidence(self) -> float:
        """Calculate average profiler confidence"""
        if not self.processing_history:
            return 0.0
        confidences = [
            p["profile"]["confidence"] 
            for p in self.processing_history
        ]
        return sum(confidences) / len(confidences)

    def _get_most_common_states(self) -> Dict[str, int]:
        """Track most common user states detected"""
        state_counts = {}
        for entry in self.processing_history:
            state = entry["profile"]["state"]
            state_counts[state] = state_counts.get(state, 0) + 1
        return dict(sorted(state_counts.items(), key=lambda x: x[1], reverse=True))

    def reset(self):
        """Reset system state"""
        self.processing_history.clear()
        self.action_agent.reset_history()


class ScenarioSimulator:
    """
    Simulates real-time wearable data with predefined scenarios.
    Used for Phase 1 testing without real smartwatch data.
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
    def run_all_scenarios(brain: WearableContextBrain) -> List[Dict[str, Any]]:
        """
        Run all predefined scenarios through the system.
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
    def run_continuous_simulation(brain: WearableContextBrain, duration: int = 10, interval: float = 2.0):
        """
        Simulate real-time sensor stream continuously.
        
        Args:
            brain: WearableContextBrain instance
            duration: Total simulation duration in seconds
            interval: Time between sensor readings in seconds
        """
        print(f"\n{'='*80}")
        print("CONTINUOUS REAL-TIME SIMULATION")
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

            print(f"[{iteration}] Processing: {scenario_info['name']}")

            output = brain.process(scenario_info["data"])

            # Print compact output
            print(f"  State: {output['profile']['state']} | Urgency: {output['profile']['urgency']}/10")
            print(f"  Action: {output['decision']['action']}")
            print()

            time.sleep(interval)

        print(f"\n{'='*80}")
        print("SIMULATION COMPLETE")
        print(f"Processed: {len(brain.processing_history)} readings")
        print(f"{'='*80}\n")


def main():
    """Main execution"""
    print("\n" + "="*80)
    print("WEARABLE CONTEXT BRAIN - Multi-Agent Intelligence System")
    print("="*80)

    # Initialize system
    brain = WearableContextBrain()

    # Phase 1: Test all scenarios
    print("\nPhase 1: Scenario Testing")
    print("-" * 80)
    results = ScenarioSimulator.run_all_scenarios(brain)

    # Phase 2: Print system summary
    print("\n" + "="*80)
    print("SYSTEM SUMMARY")
    print("="*80)
    summary = brain.get_system_summary()
    print(json.dumps(summary, indent=2))

    # Phase 3: Continuous simulation
    print("\n" + "="*80)
    print("Phase 2: Continuous Simulation")
    print("-" * 80)
    brain.reset()  # Clear history for fresh simulation
    ScenarioSimulator.run_continuous_simulation(brain, duration=20, interval=1.5)

    # Final summary
    print("\n" + "="*80)
    print("FINAL SYSTEM SUMMARY")
    print("="*80)
    final_summary = brain.get_system_summary()
    print(json.dumps(final_summary, indent=2))

    print("\n✅ System completed successfully!")
    print("\nFor Phase 2 recommendations, see phase2_recommendations.md")


if __name__ == "__main__":
    main()
