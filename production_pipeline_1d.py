import torch
import numpy as np
import time
import os
import sys
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.core.voting_logic import rtl_voting_logic

class SkyShieldPipeline:
    def __init__(self, models_path="models/final_production/"):
        print("[INIT] Loading SkyShield v4.2 Production Engines...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 1. Initialize Architecture
        self.backbone = SharedBackbone().to(self.device)
        self.threat_h = ThreatHead(64).to(self.device)
        self.type_h = TypeHead(64).to(self.device)
        self.jammer_h = JammerHead(64).to(self.device)
        
        # 2. Load Trained Weights
        try:
            self.backbone.load_state_dict(torch.load(os.path.join(models_path, "backbone.pth"), map_location=self.device, weights_only=True))
            self.threat_h.load_state_dict(torch.load(os.path.join(models_path, "threat_head.pth"), map_location=self.device, weights_only=True))
            self.type_h.load_state_dict(torch.load(os.path.join(models_path, "type_head.pth"), map_location=self.device, weights_only=True))
            self.jammer_h.load_state_dict(torch.load(os.path.join(models_path, "jammer_head.pth"), map_location=self.device, weights_only=True))
            print("[INIT] Weights loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load weights: {e}")
            sys.exit(1)
            
        self.backbone.eval(); self.threat_h.eval(); self.type_h.eval(); self.jammer_h.eval()

    def preprocess(self, raw_iq):
        """
        Channelizer/Splitter Simulation: 
        Ensures input is strictly (2, 512) and normalized for INT8 hardware range.
        """
        # Ensure correct shape (batch, channels, samples)
        if raw_iq.ndim == 2:
            raw_iq = np.expand_dims(raw_iq, axis=0)
            
        # Float32 conversion (FPGA requirement)
        iq_tensor = torch.from_numpy(raw_iq).float().to(self.device)
        return iq_tensor

    def run_inference(self, processed_iq):
        """End-to-End Multi-Head Inference."""
        with torch.no_grad():
            # The Backbone outputs the 64-dim Feature Vector
            features = self.backbone(processed_iq)
            
            # The 3 Heads interpret the features
            threat_logit = self.threat_h(features).squeeze()
            threat_pred = torch.sigmoid(threat_logit).item() > 0.5
            
            type_logits = self.type_h(features)
            type_pred = torch.argmax(type_logits, dim=1).item()
            
            jammer_logit = self.jammer_h(features).squeeze()
            jammer_pred = torch.sigmoid(jammer_logit).item() > 0.5
            
        return threat_pred, type_pred, jammer_pred

    def ingest_and_process(self, iq_stream):
        """Ingests a real-time stream and outputs local terminal logs."""
        print(f"\n{'='*70}")
        print(f"{'TIMESTAMP':<20} | {'PREDICTION':<12} | {'DECISION':<30}")
        print(f"{'='*70}")
        
        type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}
        
        for i, sample in enumerate(iq_stream):
            start_time = time.time()
            
            # 1. Preprocess
            input_data = self.preprocess(sample)
            
            # 2. Inference
            t_p, ty_p, j_p = self.run_inference(input_data)
            
            # 3. Hardware Logic (RTL Voting)
            action_code, status = rtl_voting_logic(t_p, ty_p, j_p)
            
            latency = (time.time() - start_time) * 1000
            timestamp = time.strftime("%H:%M:%S")
            
            # 4. Output Locally
            print(f"{timestamp} (S#{i+1:02}) | {type_map[ty_p]:<12} | {status} ({latency:.2f}ms)")
            time.sleep(0.05) # Simulate real-time arrival

if __name__ == "__main__":
    # Load the production data stream we generated earlier
    if not os.path.exists("data/production/hidden_x.npy"):
        print("[ERROR] Production data not found. Run 'python -m src.data_pipeline.production_stream' first.")
    else:
        stream_data = np.load("data/production/hidden_x.npy")
        pipeline = SkyShieldPipeline()
        pipeline.ingest_and_process(stream_data[:20]) # Process 20 samples
