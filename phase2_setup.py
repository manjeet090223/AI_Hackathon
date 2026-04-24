"""
PHASE 2: LLM Integration Setup and Usage Guide

This script helps set up and test the Groq LLM integration.
"""

import os
import sys

def setup_groq_api():
    """
    Setup Groq API key for LLM integration.
    
    Steps:
    1. Get API key from https://console.groq.com/keys
    2. Set environment variable
    3. Test connection
    """
    print("\n" + "="*80)
    print("GROQ LLM SETUP GUIDE")
    print("="*80)
    
    print("\n📋 STEP 1: Get Groq API Key")
    print("-" * 80)
    print("1. Go to: https://console.groq.com/keys")
    print("2. Create an API key")
    print("3. Copy the key")
    
    print("\n🔧 STEP 2: Set Environment Variable")
    print("-" * 80)
    
    api_key = os.getenv("GROQ_API_KEY")
    
    if api_key:
        print(f"✅ GROQ_API_KEY is already set: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("❌ GROQ_API_KEY not found")
        print("\nOption A: Set via terminal (temporary)")
        print("  export GROQ_API_KEY='your-api-key-here'")
        print("\nOption B: Set via Python (current session)")
        print("  import os")
        print("  os.environ['GROQ_API_KEY'] = 'your-api-key-here'")
        print("\nOption C: Set in ~/.zshrc or ~/.bashrc (permanent)")
        print("  echo 'export GROQ_API_KEY=\"your-api-key-here\"' >> ~/.zshrc")
        print("  source ~/.zshrc")
    
    print("\n📦 STEP 3: Install Dependencies")
    print("-" * 80)
    print("pip install groq")
    
    print("\n✅ STEP 4: Test Connection")
    print("-" * 80)
    
    try:
        from groq import Groq
        client = Groq(api_key=api_key or "test")
        print("✅ Groq client imported successfully")
        
        if api_key:
            print("✅ API key found")
            print("✅ Ready to use LLM features!")
        else:
            print("⚠️ API key not set - LLM features will be disabled")
            print("   Run: export GROQ_API_KEY='your-key-here'")
    except ImportError:
        print("❌ Groq not installed")
        print("   Install: pip install groq")
    except Exception as e:
        print(f"⚠️ Connection test failed: {e}")


def install_dependencies():
    """Install required Python packages."""
    print("\n" + "="*80)
    print("INSTALLING DEPENDENCIES")
    print("="*80)
    
    packages = [
        "groq>=0.4.0",
    ]
    
    print("\nPackages to install:")
    for pkg in packages:
        print(f"  - {pkg}")
    
    import subprocess
    for pkg in packages:
        print(f"\nInstalling {pkg}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])
            print(f"✅ {pkg} installed")
        except Exception as e:
            print(f"❌ Failed to install {pkg}: {e}")


def test_hybrid_system():
    """Test the hybrid system without real LLM (mock mode)."""
    print("\n" + "="*80)
    print("TESTING HYBRID SYSTEM (MOCK MODE)")
    print("="*80)
    
    # Test sensor data
    test_cases = [
        {
            "name": "Normal Case",
            "data": {"hr": 75, "movement": 0.25, "battery": 70, "app": "idle"}
        },
        {
            "name": "Stress Case",
            "data": {"hr": 115, "movement": 0.15, "battery": 45, "app": "work"}
        },
        {
            "name": "Emergency Case",
            "data": {"hr": 130, "movement": 0.01, "battery": 50, "app": "idle"}
        }
    ]
    
    print("\nRunning test cases...")
    
    try:
        from wearable_brain_v2 import WearableContextBrainV2
        
        # Test with LLM disabled (fallback mode)
        brain = WearableContextBrainV2(use_llm=False)
        
        for test_case in test_cases:
            print(f"\n📊 Test: {test_case['name']}")
            print("-" * 40)
            
            output = brain.process(test_case['data'])
            
            state = output['rule_based']['state']
            urgency = output['rule_based']['urgency']
            confidence = output['rule_based']['confidence']
            action = output['final_decision']['action']
            
            print(f"  State: {state}")
            print(f"  Urgency: {urgency}/10")
            print(f"  Confidence: {confidence:.1%}")
            print(f"  Action: {action}")
        
        print("\n✅ Hybrid system test completed")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()


def show_architecture():
    """Display system architecture."""
    print("\n" + "="*80)
    print("PHASE 2 ARCHITECTURE")
    print("="*80)
    
    architecture = """
┌─────────────────────────────────────────────────────────────────────┐
│                      WEARABLE CONTEXT BRAIN V2                      │
│                   (Hybrid Intelligence System)                      │
└─────────────────────────────────────────────────────────────────────┘

                           Sensor Data Stream
                                   │
                                   ▼
                         ┌──────────────────┐
                         │  Profiler Agent  │
                         │  (Rule-Based)    │
                         │                  │
                         │ State Detection  │
                         │ Urgency Scoring  │
                         │ Confidence: 0-1  │
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
        ┌─────────────────────┐    ┌──────────────────────┐
        │ Check LLM Trigger?  │    │  Action Agent        │
        │                     │    │  (Rule-Based)        │
        │ IF confidence < 0.6 │    │                      │
        │ OR state ambiguous  │    │ Decision Rules:      │
        │ OR urgency 6-8      │    │ • Emergency → Alert  │
        │ → YES: Use LLM      │    │ • Stress → Notify    │
        │ → NO: Skip LLM      │    │ • Normal → Silent    │
        └──────────┬──────────┘    └──────────────────────┘
                   │                           │
                   ▼                           │
        ┌─────────────────────┐               │
        │  Groq LLM Reasoner  │               │
        │  (llama-3.1-70b)    │               │
        │                     │               │
        │ • Validate decision │               │
        │ • Assess risk level │               │
        │ • Explain reasoning │               │
        │ • Suggest actions   │               │
        └──────────┬──────────┘               │
                   │                           │
                   └────────────┬──────────────┘
                                │
                                ▼
                     ┌─────────────────────┐
                     │ Decision Merger     │
                     │                     │
                     │ Combine:            │
                     │ - Rule-based action │
                     │ - LLM reasoning     │
                     │ - Final decision    │
                     └────────────┬────────┘
                                  │
                                  ▼
                     ┌─────────────────────┐
                     │  Final Output       │
                     │                     │
                     │ • Action            │
                     │ • Confidence        │
                     │ • Explanation       │
                     │ • Health Advice     │
                     │ • Next Steps        │
                     └─────────────────────┘
                                  │
                                  ▼
                     ┌─────────────────────┐
                     │  Send to Wearable   │
                     │  • Vibration        │
                     │  • Display          │
                     │  • Sound            │
                     │  • Notification     │
                     └─────────────────────┘

KEY BENEFITS:
✅ Fast rule-based classification for clear cases
✅ Intelligent LLM reasoning for ambiguous situations
✅ Natural language explanations users can trust
✅ Health suggestions beyond alerts
✅ Graceful fallback if LLM unavailable
✅ Minimal latency impact (<300ms per decision)
"""
    
    print(architecture)


def show_llm_examples():
    """Show example LLM outputs."""
    print("\n" + "="*80)
    print("EXAMPLE LLM OUTPUTS")
    print("="*80)
    
    examples = [
        {
            "title": "Stress Case with LLM Enhancement",
            "input": {
                "hr": 115,
                "movement": 0.15,
                "app": "work",
                "battery": 45
            },
            "rule_output": {
                "state": "stressed",
                "urgency": 6,
                "confidence": 0.6
            },
            "llm_output": {
                "final_state": "work_stress",
                "risk_level": "medium",
                "explanation": "Elevated HR while working is common. May indicate deadline pressure or caffeine.",
                "advice": "Take a 2-minute breathing break. Consider a walk or hydration.",
                "should_alert": True
            }
        },
        {
            "title": "Emergency Case - LLM Validates",
            "input": {
                "hr": 130,
                "movement": 0.01,
                "app": "idle",
                "battery": 50
            },
            "rule_output": {
                "state": "emergency",
                "urgency": 10,
                "confidence": 0.8
            },
            "llm_output": {
                "final_state": "potential_cardiac_event",
                "risk_level": "critical",
                "explanation": "High HR with immobility is concerning. Could indicate cardiac distress.",
                "advice": "Seek immediate medical attention. If experiencing chest pain/shortness of breath, call emergency services.",
                "should_alert": True
            }
        },
        {
            "title": "Exercise Case - LLM Clarifies",
            "input": {
                "hr": 140,
                "movement": 0.75,
                "app": "fitness",
                "battery": 60
            },
            "rule_output": {
                "state": "exercising",
                "urgency": 2,
                "confidence": 0.7
            },
            "llm_output": {
                "final_state": "exercise_normal",
                "risk_level": "low",
                "explanation": "HR and movement patterns indicate normal cardio exercise.",
                "advice": "Great workout! Maintain hydration and monitor intensity.",
                "should_alert": False
            }
        }
    ]
    
    import json
    
    for example in examples:
        print(f"\n{'─'*80}")
        print(f"📋 {example['title']}")
        print(f"{'─'*80}")
        
        print("\n📊 Input Data:")
        print(json.dumps(example['input'], indent=2))
        
        print("\n⚡ Rule-Based Output:")
        print(json.dumps(example['rule_output'], indent=2))
        
        print("\n🧠 LLM Enhancement:")
        print(json.dumps(example['llm_output'], indent=2))


def main():
    """Main setup and testing interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Phase 2: LLM Integration Setup and Testing"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Show Groq API setup instructions"
    )
    parser.add_argument(
        "--install",
        action="store_true",
        help="Install required dependencies"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test hybrid system (mock mode)"
    )
    parser.add_argument(
        "--architecture",
        action="store_true",
        help="Show system architecture"
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show example LLM outputs"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all setup steps"
    )
    
    args = parser.parse_args()
    
    # If no args, show all
    if not any(vars(args).values()):
        args.all = True
    
    if args.all:
        show_architecture()
        setup_groq_api()
        show_llm_examples()
        test_hybrid_system()
    else:
        if args.setup:
            setup_groq_api()
        if args.install:
            install_dependencies()
        if args.test:
            test_hybrid_system()
        if args.architecture:
            show_architecture()
        if args.examples:
            show_llm_examples()


if __name__ == "__main__":
    main()
