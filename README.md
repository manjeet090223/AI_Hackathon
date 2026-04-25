# ◈ CONTEXT IQ — Wearable AI Context Engine

Context IQ is a premium, agent-powered wearable dashboard designed for high-stakes focus and health monitoring. It uses a multi-agent system to distinguish between high-stress situations that require intervention and focused states where interruptions must be suppressed.

## 🚀 Features

- **Multi-Brain Architecture**: Powered by Profiler and Action agents via the Groq API.
- **Cost-Benefit Reasoning**: Only interrupts the user when the benefit exceeds the social and situational cost.
- **Premium Dashboard**: Three distinct views (User, Advanced, Watch) with real-time telemetry and health diagnostics.
- **Meditation Paradox Handling**: Recognizes intentional states like meditation (high HR, low movement) to suppress false alerts.

## 🛠 Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**:
   - Copy `.env.example` to `.env`.
   - Add your `GROQ_API_KEY`.

3. **Run the Backend**:
   ```bash
   python api_server.py
   ```

4. **Launch the Frontend**:
   - Open `index.html` in your browser.

## 🧪 Testing

Run the system test to verify agent logic and API connectivity:
```bash
python test_system.py
```

## 🧠 System Scenarios

- **Scenario A (Silent Guardian)**: High HR during a presentation. The agent suppresses notifications.
- **Scenario B (Emergency Catch)**: High HR while sleeping/still at 2 AM. The agent triggers an emergency alert.
- **Scenario C (Battery Dilemma)**: Low battery during navigation. The agent prioritizes maps over non-critical alerts.
- **Scenario D (Meditation Paradox)**: High HR during meditation. The agent suppresses alerts to protect the user's flow state.
