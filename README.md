# ◈ Watch Brain — Wearable AI Intelligence Engine

Watch Brain is a state-of-the-art wearable AI context engine designed to minimize digital interruptions while ensuring user safety. By analyzing real-time sensor data (Heart Rate, SpO2, GSR, Accelerometer), it determines the user's current activity and social context to intelligently suppress notifications or trigger emergency protocols.

## Features

- **Dual-Agent Architecture**: 
  - **Profiler Agent**: Analyzes multi-modal sensor telemetry to determine high-level state (Working, Meditating, Exercising).
  - **Action Agent**: Makes executive decisions (SUPPRESS, GENTLE_NOTIFY, EMERGENCY) based on context and interruption cost.
- **Ultra-Fast Inference**: Powered by **Groq (Llama 3.1)** for near-instant reasoning.
- **Dynamic Watch UI**: A dedicated "Watch View" that simulates the wearable device's behavior.
- **Polite Notifications**: AI-driven advisory messages that feel like a companion rather than an alert.
- **Robust Reliability**: Seamless fallback to local scenarios when connectivity is limited.

## Tech Stack

- **Frontend**: Vanilla JS, HTML5, CSS3 (Modern Aesthetics)
- **Backend**: FastAPI (Python)
- **AI Brain**: Groq Cloud SDK (Llama 3.1 8B/70B)
- **Data Simulation**: Real-time sensor telemetry generator

## Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/manjeet090223/AI_Hackathon.git
cd AI_Hackathon
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### 4. Run the Backend
```bash
python api_server.py
```

### 5. Launch the Dashboard
Simply open `index.html` in your browser or serve it using a local server.

##  System Architecture

The engine operates on a feedback loop:
1. **Telemetry**: Raw sensor data is streamed from the wearable.
2. **Contextualization**: The **Profiler Agent** builds a situational map (Stress levels, Physical movement, Social context).
3. **Decisioning**: The **Action Agent** evaluates the "Interruption Cost" vs the "Notification Urgency".
4. **Execution**: The UI reflects the AI's choice via silent logging or polite advisory notifications.

##  Security & Privacy
Watch Brain processes sensor data locally or via encrypted API calls. In a production environment, all biometric data is anonymized before reaching the LLM layer.

##  License
This project is licensed under the MIT License.