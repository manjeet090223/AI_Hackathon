#!/usr/bin/env python3
"""
Test Groq LLM Integration with Wearable Brain
"""

import os
import sys
import json
from typing import Dict, Any

# Set API key
os.environ['GROQ_API_KEY'] = 'REMOVED'

def test_groq_connection():
    """Test basic Groq connection."""
    print("\n" + "="*80)
    print("TEST 1: Groq API Connection")
    print("="*80)
    
    try:
        from groq import Groq
        
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        print("✅ Groq client initialized")
        
        # Quick test call
        message = client.messages.create(
            model="llama-3.1-70b-versatile",
            max_tokens=50,
            temperature=0.2,
            messages=[
                {"role": "user", "content": "Say 'Hello' in one word."}
            ]
        )
        
        response = message.content[0].text
        print(f"✅ LLM Response: {response[:100]}")
        print("✅ Groq API Connection Successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_llm_reasoner():
    """Test LLM Reasoner Agent."""
    print("\n" + "="*80)
    print("TEST 2: LLM Reasoner Agent")
    print("="*80)
    
    try:
        from llm_reasoner import LLMReasonerAgent
        
        reasoner = LLMReasonerAgent(
            api_key=os.getenv("GROQ_API_KEY"),
            model="llama-3.1-70b-versatile"
        )
        
        print("✅ LLM Reasoner initialized")
        
        # Test stress case
        sensor_data = {
            "hr": 115,
            "movement": 0.15,
            "app": "work",
            "battery": 45
        }
        
        profile = {
            "state": "stressed",
            "urgency": 6,
            "confidence": 0.6,
            "reason": "Elevated HR with minimal movement"
        }
        
        print("\n📊 Input:")
        print(f"  HR: {sensor_data['hr']} BPM")
        print(f"  Movement: {sensor_data['movement']}")
        print(f"  App: {sensor_data['app']}")
        print(f"  State: {profile['state']}")
        print(f"  Urgency: {profile['urgency']}/10")
        print(f"  Confidence: {profile['confidence']:.1%}")
        
        response = reasoner.reason(sensor_data, profile)
        
        if response:
            print("\n🧠 LLM Reasoning Output:")
            print(f"  Final State: {response.final_state}")
            print(f"  Risk Level: {response.risk_level}")
            print(f"  Explanation: {response.explanation}")
            print(f"  Advice: {response.advice}")
            print(f"  Should Alert: {response.should_alert}")
            print(f"  Reasoning Time: {response.reasoning_time:.3f}s")
            print("\n✅ LLM Reasoner Test Successful!")
            return True
        else:
            print("❌ No LLM response")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_hybrid_system():
    """Test complete hybrid system."""
    print("\n" + "="*80)
    print("TEST 3: Hybrid Intelligence System")
    print("="*80)
    
    try:
        from wearable_brain_v2 import WearableContextBrainV2, ScenarioSimulator
        
        # Initialize hybrid system
        brain = WearableContextBrainV2(use_llm=True, groq_api_key=os.getenv("GROQ_API_KEY"))
        
        if brain.llm_enabled:
            print("✅ Hybrid system with LLM enabled")
        else:
            print("⚠️ LLM not available, fallback to rule-based")
        
        # Test stress case
        print("\n📋 Processing: Stress Case")
        print("-" * 80)
        
        stress_data = {
            "hr": 115,
            "movement": 0.15,
            "app": "work",
            "battery": 45
        }
        
        output = brain.process(stress_data)
        
        print(f"Rule-Based State: {output['rule_based']['state']}")
        print(f"Rule-Based Urgency: {output['rule_based']['urgency']}/10")
        print(f"Rule-Based Confidence: {output['rule_based']['confidence']:.1%}")
        
        if output.get('llm_enhanced'):
            print(f"\n🧠 LLM Enhanced:")
            print(f"  Risk Level: {output['llm_enhanced']['risk_level']}")
            print(f"  Explanation: {output['llm_enhanced']['explanation']}")
            print(f"  Advice: {output['llm_enhanced']['advice']}")
            print(f"  Reasoning Time: {output['llm_enhanced']['reasoning_time']:.3f}s")
        
        print(f"\n✅ Final Decision: {output['final_decision']['action']}")
        print(f"   Reason: {output['final_decision']['reason'][:80]}...")
        
        # Test emergency case
        print("\n📋 Processing: Emergency Case")
        print("-" * 80)
        
        emergency_data = {
            "hr": 130,
            "movement": 0.01,
            "app": "idle",
            "battery": 50
        }
        
        output2 = brain.process(emergency_data)
        
        print(f"Rule-Based State: {output2['rule_based']['state']}")
        print(f"Rule-Based Urgency: {output2['rule_based']['urgency']}/10")
        
        if output2.get('llm_enhanced'):
            print(f"\n🧠 LLM Enhanced:")
            print(f"  Risk Level: {output2['llm_enhanced']['risk_level']}")
            print(f"  Explanation: {output2['llm_enhanced']['explanation']}")
        
        print(f"\n🚨 Final Decision: {output2['final_decision']['action']}")
        
        print("\n✅ Hybrid System Test Successful!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_full_simulation():
    """Run full simulation with all scenarios."""
    print("\n" + "="*80)
    print("TEST 4: Full Simulation with All Scenarios")
    print("="*80)
    
    try:
        from wearable_brain_v2 import WearableContextBrainV2, ScenarioSimulator
        
        brain = WearableContextBrainV2(use_llm=True, groq_api_key=os.getenv("GROQ_API_KEY"))
        
        print(f"\nLLM Enabled: {brain.llm_enabled}")
        print("\nRunning all 6 scenarios...\n")
        
        results = ScenarioSimulator.run_all_scenarios(brain)
        
        # Summary
        print("\n" + "="*80)
        print("SIMULATION SUMMARY")
        print("="*80)
        
        summary = brain.get_system_summary()
        print(json.dumps(summary, indent=2))
        
        print("\n✅ Full Simulation Completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("GROQ LLM INTEGRATION TEST SUITE")
    print("="*80)
    
    results = []
    
    # Test 1: Connection
    results.append(("Groq Connection", test_groq_connection()))
    
    # Test 2: LLM Reasoner
    results.append(("LLM Reasoner", test_llm_reasoner()))
    
    # Test 3: Hybrid System
    results.append(("Hybrid System", test_hybrid_system()))
    
    # Test 4: Full Simulation
    results.append(("Full Simulation", run_full_simulation()))
    
    # Final summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    total_passed = sum(1 for _, p in results if p)
    total_tests = len(results)
    
    print(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        print("\n🎉 All tests passed! LLM integration is working perfectly!")
    else:
        print(f"\n⚠️ {total_tests - total_passed} test(s) failed. Check the output above.")


if __name__ == "__main__":
    main()
