from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import numpy as np
import torch
import os
import io
import base64
import matplotlib.pyplot as plt
from production_pipeline_2d import SkyShield2DProduction
from src.utils.channelizer import apply_channelizer_2d

app = FastAPI()

# Setup paths
TEMPLATES_DIR = "templates"
os.makedirs(TEMPLATES_DIR, exist_ok=True)
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize Inference Engine
# Uses the stabilized v6.0 Balanced model from models/production_2d_elite
pipeline = SkyShield2DProduction(model_dir="models/production_2d_elite")

def get_spectrogram_base64(iq_complex):
    """Generates a visual spectrogram for the HUD."""
    x_2d = apply_channelizer_2d(iq_complex)
    mag = x_2d[0] # Magnitude channel
    
    plt.figure(figsize=(4, 4))
    plt.imshow(mag, aspect='auto', cmap='magma', origin='lower')
    plt.axis('off')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, transparent=True)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_signal(file: UploadFile = File(...)):
    # 1. Load the dropped file
    contents = await file.read()
    iq_complex = np.load(io.BytesIO(contents))
    
    # 2. Decoding Logic (Sliding Window / Channelization)
    # If the signal is large, we decode it into multiple 512-sample segments
    results = []
    window_size = 512
    step = 256 # Overlap for better "decoding" coverage
    
    if len(iq_complex) <= window_size:
        # Process single signal
        res = pipeline.process_sample(iq_complex)
        results.append({
            "name": file.filename,
            "prediction": res,
            "visual": get_spectrogram_base64(iq_complex)
        })
    else:
        # DECODE: Multiple signals in one capture
        for i in range(0, len(iq_complex) - window_size + 1, step):
            segment = iq_complex[i:i+window_size]
            res = pipeline.process_sample(segment)
            
            # For the demo, only show segments that contain a detectable signal (not pure noise)
            # Detections of 'WiFi' with very low confidence are usually noise floor.
            # But we want to show 'Decoding' so we show anything with a prediction.
            results.append({
                "name": f"DECODED_SCAN_CH_{i//step + 1:02d}",
                "prediction": res,
                "visual": get_spectrogram_base64(segment)
            })
            
    # 3. Return Tactical Decision Batch
    return {
        "status": "SUCCESS",
        "batch_results": results
    }

@app.get("/health")
async def health():
    return {"status": "ALIVE"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8080)
