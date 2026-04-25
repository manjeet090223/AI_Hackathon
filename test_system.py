import time
from dotenv import load_dotenv
load_dotenv()
from pure_agents import WearableAgentBrain

def test_system():
    print("\n🚀 STARTING CONTEXT IQ SYSTEM TEST (PURE AGENTS)")
    print("═════════════════════════════════════════════════")
    
    try:
        brain = WearableAgentBrain()
        if not brain.llm_enabled:
            print("❌ Groq API key not found. Ensure .env is loaded.")
            return
            
        print("✅ Brain initialized. Pure LLM Agents enabled.")
        
        # SCENARIO 1 — The False Positive Trap
        print("\n--- SCENARIO 1: The False Positive Trap ---")
        brain.reset()
        sensor_s1 = {"hr": 118, "accel": 0.02, "app": "bead_counter", "time": "20:15", "battery": 80, "spo2": 98.0, "gsr": 2.0, "temp": 36.5}
        brain.telemetry_window.append(sensor_s1)
        brain.telemetry_window.append(sensor_s1)
        res_s1 = brain.ingest(sensor_s1)
        
        p_state = res_s1["profiler"]["primary_state"]
        a_action = res_s1["decision"]["action"]
        supp_reasons = res_s1["profiler"].get("suppression_reasons", [])
        
        print(f"Profiler State: {p_state}")
        print(f"Action Agent: {a_action}")
        if p_state == "meditating" and "STAY_SILENT" in a_action:
            print("✅ PASSED: False Positive Trap handled correctly.")
        else:
            print("❌ FAILED: Expected meditating and STAY_SILENT.")
            
        # SCENARIO 2 — The Real Emergency
        print("\n--- SCENARIO 2: The Real Emergency ---")
        brain.reset()
        sensor_s2 = {"hr": 134, "accel": 0.01, "app": "sleep", "time": "02:17", "spo2": 93.5, "battery": 90, "gsr": 5.0, "temp": 36.5}
        brain.telemetry_window.append(sensor_s2)
        brain.telemetry_window.append(sensor_s2)
        res_s2 = brain.ingest(sensor_s2)
        
        p_state = res_s2["profiler"]["primary_state"]
        a_action = res_s2["decision"]["action"]
        
        print(f"Profiler State: {p_state}")
        print(f"Action Agent: {a_action}")
        if a_action == "EMERGENCY_ALERT":
            print("✅ PASSED: Real Emergency triggered appropriately.")
        else:
            print("❌ FAILED: Expected EMERGENCY_ALERT.")

        # SCENARIO 3 — The Navigation Dilemma
        print("\n--- SCENARIO 3: The Navigation Dilemma ---")
        brain.reset()
        sensor_s3 = {"hr": 78, "accel": 0.7, "app": "maps", "time": "14:00", "battery": 5, "gps_familiarity": "unfamiliar", "spo2": 98.0, "gsr": 3.0, "temp": 36.5}
        brain.telemetry_window.append(sensor_s3)
        brain.telemetry_window.append(sensor_s3)
        res_s3 = brain.ingest(sensor_s3)
        
        p_state = res_s3["profiler"]["primary_state"]
        a_action = res_s3["decision"]["action"]
        
        print(f"Profiler State: {p_state}")
        print(f"Action Agent: {a_action}")
        if p_state == "navigating" and a_action in ["STAY_SILENT", "LOG_ONLY"]:
            print("✅ PASSED: Navigation Dilemma suppressed correctly.")
        else:
            print("❌ FAILED: Expected navigating and STAY_SILENT.")

        # SCENARIO 4 — The Escalating Stress
        print("\n--- SCENARIO 4: The Escalating Stress ---")
        brain.reset()
        hr_sequence = [80, 82, 85, 88, 92, 95, 99, 103, 107, 112]
        for hr in hr_sequence[:-1]:
            s4 = {"hr": hr, "accel": 0.1, "app": "work", "time": "10:30", "battery": 60, "spo2": 98.0, "gsr": 8.0, "temp": 37.0}
            brain.telemetry_window.append(s4)
        
        last_s4 = {"hr": hr_sequence[-1], "accel": 0.1, "app": "work", "time": "10:30", "battery": 60, "spo2": 98.0, "gsr": 8.0, "temp": 37.0}
        res_s4 = brain.ingest(last_s4)
        
        p_trend = res_s4["profiler"]["hr_trend"]
        p_state = res_s4["profiler"]["primary_state"]
        a_action = res_s4["decision"]["action"]
        
        print(f"Profiler Trend: {p_trend}, State: {p_state}")
        print(f"Action Agent: {a_action}")
        if p_trend == "rising" and a_action in ["GENTLE_NOTIFY", "URGENT_NOTIFY"]:
            print("✅ PASSED: Escalating Stress identified and notified.")
        else:
            print("❌ FAILED: Expected rising trend and NOTIFY action.")

        # SCENARIO 5 — The Exercise False Alarm
        print("\n--- SCENARIO 5: The Exercise False Alarm ---")
        brain.reset()
        sensor_s5 = {"hr": 155, "accel": 1.4, "app": "fitness", "time": "07:30", "battery": 80, "spo2": 97.0, "gsr": 16.0, "temp": 38.2}
        brain.telemetry_window.append(sensor_s5)
        brain.telemetry_window.append(sensor_s5)
        res_s5 = brain.ingest(sensor_s5)
        
        p_state = res_s5["profiler"]["primary_state"]
        a_action = res_s5["decision"]["action"]
        
        print(f"Profiler State: {p_state}")
        print(f"Action Agent: {a_action}")
        if p_state == "exercising" and a_action in ["STAY_SILENT", "LOG_ONLY"]:
            print("✅ PASSED: Exercise handled silently.")
        else:
            print("❌ FAILED: Expected exercising and STAY_SILENT.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    test_system()
