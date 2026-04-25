import os
import torch
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.core.voting_logic import rtl_voting_logic

app = FastAPI(title="SkyShield 1D API", description="GCP-ready RF Threat Detection API")

# Load models at startup
MODEL_DIR = os.getenv("MODEL_DIR", "models")
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

backbone = SharedBackbone().to(device)
threat_head = ThreatHead().to(device)
type_head = TypeHead().to(device)
jammer_head = JammerHead().to(device)

def load_weights():
    try:
        backbone.load_state_dict(torch.load(os.path.join(MODEL_DIR, "backbone.pth"), map_location=device, weights_only=True))
        threat_head.load_state_dict(torch.load(os.path.join(MODEL_DIR, "threat_head.pth"), map_location=device, weights_only=True))
        type_head.load_state_dict(torch.load(os.path.join(MODEL_DIR, "type_head.pth"), map_location=device, weights_only=True))
        jammer_head.load_state_dict(torch.load(os.path.join(MODEL_DIR, "jammer_head.pth"), map_location=device, weights_only=True))
        print(f"Models loaded successfully from {MODEL_DIR}")
    except Exception as e:
        print(f"Error loading models: {e}")

load_weights()

backbone.eval()
threat_head.eval()
type_head.eval()
jammer_head.eval()

class IQSample(BaseModel):
    data: List[List[float]] # Expected shape [2, 512]

@app.get("/")
async def root():
    return {"status": "online", "system": "SkyShield 1D", "version": "3.5"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/predict")
async def predict(sample: IQSample):
    try:
        x = torch.tensor(sample.data, dtype=torch.float32).unsqueeze(0).to(device)
        
        if x.shape != (1, 2, 512):
            raise HTTPException(status_code=400, detail=f"Invalid input shape: {x.shape}. Expected (1, 2, 512)")

        with torch.no_grad():
            features = backbone(x)
            
            threat_out = torch.sigmoid(threat_head(features)).item()
            type_out = torch.argmax(type_head(features), dim=1).item()
            jammer_out = torch.sigmoid(jammer_head(features)).item()

        p_threat = threat_out > 0.5
        p_jammer = jammer_out > 0.5
        
        action_code, status = rtl_voting_logic(p_threat, type_out, p_jammer)
        
        type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}
        
        return {
            "threat_detected": p_threat,
            "threat_confidence": threat_out,
            "classification": type_map.get(type_out, "Unknown"),
            "jammer_detected": p_jammer,
            "jammer_confidence": jammer_out,
            "system_action": status,
            "action_code": action_code
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
