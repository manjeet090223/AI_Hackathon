import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from wearable_brain_v2 import WearableContextBrainV2
from dotenv import load_dotenv

# Load .env for GROQ_API_KEY
load_dotenv()

app = FastAPI(title="Wearable AI Bridge")

# Enable CORS for local index.html
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the Brain
# It will automatically pick up GROQ_API_KEY from environment
brain = WearableContextBrainV2(use_llm=True)

class TelemetryData(BaseModel):
    hr: int
    movement: float
    app: str = "idle"
    battery: int = 100

@app.post("/analyze")
async def analyze_telemetry(data: TelemetryData):
    try:
        # Prepare sensor data for the brain
        sensor_data = {
            "hr": data.hr,
            "movement": data.movement,
            "app": data.app,
            "battery": data.battery
        }
        
        # Process through hybrid agents
        output = brain.process(sensor_data)
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    return brain.get_system_summary()

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Wearable AI Bridge on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
