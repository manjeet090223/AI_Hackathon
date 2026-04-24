# Wearable Context Brain - Sample Outputs

## Scenario 1: Sleeping
**Input:**
```json
{
  "hr": 65,
  "movement": 0.05,
  "battery": 80,
  "app": "sleep"
}
```

**Output:**
```json
{
  "input": {
    "hr": 65,
    "movement": 0.05,
    "battery": 80,
    "app": "sleep"
  },
  "profile": {
    "state": "sleeping",
    "urgency": 1,
    "reason": "Sleep app detected with low movement and HR",
    "confidence": 0.95
  },
  "decision": {
    "action": "DO_NOT_DISTURB",
    "reason": "User is sleeping. Silencing all non-critical notifications.",
    "notification_text": "",
    "escalation_level": 0
  }
}
```

**System Reasoning:**
- All signals aligned: sleep app + HR 65 (baseline) + movement 0.05 (stationary)
- Urgency = 1/10 (minimal)
- Action: Complete silence, no vibrations, no sound
- Confidence: 95% (clear sleep state)

---

## Scenario 2: Navigation with Low Battery
**Input:**
```json
{
  "hr": 90,
  "movement": 0.3,
  "battery": 8,
  "app": "maps"
}
```

**Output:**
```json
{
  "input": {
    "hr": 90,
    "movement": 0.3,
    "battery": 8,
    "app": "maps"
  },
  "profile": {
    "state": "navigating_low_battery",
    "urgency": 7,
    "reason": "Actively navigating with critical battery (DO NOT DISTURB)",
    "confidence": 0.87
  },
  "decision": {
    "action": "DO_NOT_DISTURB",
    "reason": "User navigating with critical battery (8%). Avoiding distractions.",
    "notification_text": "",
    "escalation_level": 0
  }
}
```

**System Reasoning:**
- Critical battery (8%) during active navigation
- Urgency = 7/10 (high), but action is DO_NOT_DISTURB to avoid accidents
- Maps app at critical moment requires zero interruptions
- Confidence: 87% (clear navigation context with battery constraint)
- **Intelligent Trade-off**: Despite high urgency, system prioritizes user safety over immediate alerts

---

## Scenario 3: Emergency Alert
**Input:**
```json
{
  "hr": 130,
  "movement": 0.01,
  "battery": 50,
  "app": "idle"
}
```

**Output:**
```json
{
  "input": {
    "hr": 130,
    "movement": 0.01,
    "battery": 50,
    "app": "idle"
  },
  "profile": {
    "state": "emergency_alert",
    "urgency": 10,
    "reason": "Critical HR 130 BPM with minimal movement",
    "confidence": 0.92
  },
  "decision": {
    "action": "EMERGENCY_ALERT",
    "reason": "CRITICAL URGENCY (10/10): Critical HR 130 BPM with minimal movement",
    "notification_text": "⚠️ EMERGENCY: Heart rate critical at 130 BPM. Seek immediate help if experiencing chest pain or difficulty breathing.",
    "escalation_level": 4
  }
}
```

**System Reasoning:**
- Critical combination: HR 130 BPM (cardiac danger zone) + movement 0.01 (stationary/immobile)
- Urgency = 10/10 (maximum critical)
- Action: EMERGENCY_ALERT with immediate escalation
- Confidence: 92% (clear emergency indicators)
- **Escalation Path**: 
  - Vibration + Sound + Screen Flash
  - Display emergency notification
  - Potentially trigger emergency services contact
  - Log incident for medical professionals

---

## Scenario 4: Exercising
**Input:**
```json
{
  "hr": 140,
  "movement": 0.75,
  "battery": 60,
  "app": "fitness"
}
```

**Output:**
```json
{
  "input": {
    "hr": 140,
    "movement": 0.75,
    "battery": 60,
    "app": "fitness"
  },
  "profile": {
    "state": "exercising",
    "urgency": 2,
    "reason": "Physical activity detected (HR: 140, Movement: 0.75)",
    "confidence": 0.93
  },
  "decision": {
    "action": "SILENT_NOTIFICATION",
    "reason": "Moderate urgency (2/10). Logging to history without vibration/sound.",
    "notification_text": "💪 Great workout! Keep it up.",
    "escalation_level": 1
  }
}
```

**System Reasoning:**
- Signals aligned: Fitness app + high HR 140 + high movement 0.75
- Urgency = 2/10 (low - expected during exercise)
- Action: SILENT_NOTIFICATION (log only, no interruption)
- Confidence: 93% (signals clearly indicate exercise)
- **User Experience**: Motivational message logged but not interrupted during workout

---

## Scenario 5: Stress Detection
**Input:**
```json
{
  "hr": 115,
  "movement": 0.15,
  "battery": 45,
  "app": "work"
}
```

**Output:**
```json
{
  "input": {
    "hr": 115,
    "movement": 0.15,
    "battery": 45,
    "app": "work"
  },
  "profile": {
    "state": "stressed",
    "urgency": 6,
    "reason": "Elevated HR 115 with minimal movement",
    "confidence": 0.88
  },
  "decision": {
    "action": "URGENT_ALERT",
    "reason": "High urgency detected (Urgency: 6/10). Elevated HR 115 with minimal movement",
    "notification_text": "🔴 Your stress levels are elevated. Take a moment to breathe.",
    "escalation_level": 3
  }
}
```

**System Reasoning:**
- Stress indicators: Work app + HR 115 (elevated) + movement 0.15 (stationary/seated)
- Urgency = 6/10 (significant concern)
- Action: URGENT_ALERT (vibrate, show notification, but not critical)
- Confidence: 88% (stress pattern detected)
- **Wellness Feature**: Suggests breathing exercise to reduce stress

---

## Scenario 6: Normal Activity
**Input:**
```json
{
  "hr": 75,
  "movement": 0.25,
  "battery": 70,
  "app": "idle"
}
```

**Output:**
```json
{
  "input": {
    "hr": 75,
    "movement": 0.25,
    "battery": 70,
    "app": "idle"
  },
  "profile": {
    "state": "normal",
    "urgency": 1,
    "reason": "Normal state (HR: 75, Movement: 0.25, App: idle)",
    "confidence": 0.91
  },
  "decision": {
    "action": "NO_ACTION",
    "reason": "Low urgency (1/10). Normal operation.",
    "notification_text": "",
    "escalation_level": 0
  }
}
```

**System Reasoning:**
- All signals nominal: HR 75 (baseline) + movement 0.25 (light activity) + good battery
- Urgency = 1/10 (minimal)
- Action: NO_ACTION (system silent, no logs)
- Confidence: 91% (normal baseline state)
- **System Behavior**: Zero overhead, continue monitoring

---

## Decision Matrix Summary

| State | Urgency | Action | Escalation | User Experience |
|-------|---------|--------|------------|-----------------|
| Sleeping | 1 | DO_NOT_DISTURB | 0 | ✨ Silent mode |
| Navigation + Low Battery | 7 | DO_NOT_DISTURB | 0 | 🚗 No distractions |
| Emergency | 10 | EMERGENCY_ALERT | 4 | ⚠️ Full escalation |
| Exercising | 2 | SILENT_NOTIFICATION | 1 | 💪 Motivational log |
| Stressed | 6 | URGENT_ALERT | 3 | 🔴 Wellness check |
| Normal | 1 | NO_ACTION | 0 | ✅ Normal ops |

---

## Key Intelligence Patterns

### Pattern 1: Context Overrides Raw Thresholds
- HR 90 normally = no alert
- HR 90 while navigating + low battery = **DO NOT DISTURB** (avoid accident)

### Pattern 2: Signal Coherence
- HR 130 + movement 0.01 = emergency
- HR 140 + movement 0.75 = normal exercise
- Same HR, different meaning based on **context**

### Pattern 3: Temporal Wisdom
- System learns user patterns over time
- Can differentiate between:
  - Normal stress (work) vs abnormal stress (medical)
  - Sleep mode vs lying still (stress)
  - Exercise vs emergency

---

## Confidence Scoring

The system provides confidence scores (0-1) indicating how certain it is about state classification:

- **0.95+**: Signals perfectly aligned (sleeping)
- **0.90-0.95**: Strong signal agreement
- **0.85-0.90**: Good confidence with some ambiguity
- **<0.85**: Mixed signals (may need LLM for disambiguation)

Example: Confidence 0.87 for "navigating_low_battery" reflects:
- Strong maps app signal ✓
- Reasonable HR/movement for navigation ✓
- Low battery constraint detected ✓
- Minor: Could be stopped vs active navigation
