import torch
import torch.nn as nn
import numpy as np
import os
import time

from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d
from src.utils.channelizer import apply_channelizer_2d
from src.core.voting_logic import rtl_voting_logic

class SkyShield2DProduction:
    """
    Production-ready 2D inference pipeline.
    Bridges 1D IQ streams to 2D Spectrograms and runs the Echelon v6.0 Balanced model.
    """
    def __init__(self, model_dir="models/production_2d_elite"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"[INIT] Loading SkyShield 2D Echelon Balanced (Device: {self.device})...")
        
        # 1. Initialize Architecture (256-dim features for v6.0)
        self.backbone = SharedBackbone2d().to(self.device)
        self.threat_h = ThreatHead2d(256).to(self.device)
        self.type_h = TypeHead2d(256).to(self.device)
        self.jammer_h = JammerHead2d(256).to(self.device)
        
        # 2. Load Weights
        try:
            self.backbone.load_state_dict(torch.load(os.path.join(model_dir, "backbone.pth"), map_location=self.device, weights_only=True))
            self.threat_h.load_state_dict(torch.load(os.path.join(model_dir, "threat_head.pth"), map_location=self.device, weights_only=True))
            self.type_h.load_state_dict(torch.load(os.path.join(model_dir, "type_head.pth"), map_location=self.device, weights_only=True))
            self.jammer_h.load_state_dict(torch.load(os.path.join(model_dir, "jammer_head.pth"), map_location=self.device, weights_only=True))
            print("[INIT] Production 2D weights loaded successfully.")
        except Exception as e:
            print(f"[ERROR] Failed to load 2D weights: {e}")
            
        self.backbone.eval(); self.threat_h.eval(); self.type_h.eval(); self.jammer_h.eval()

    def preprocess_1d_to_2d(self, raw_iq_complex):
        """Mathematical Bridge: 1D Complex -> 2D Spectrogram (128x128)."""
        x_2d = apply_channelizer_2d(raw_iq_complex)
        return torch.tensor(x_2d).unsqueeze(0).to(self.device)

    def process_sample(self, raw_iq_complex):
        """Processes a single 1D complex signal and returns tactical results."""
        input_tensor = self.preprocess_1d_to_2d(raw_iq_complex)
        with torch.no_grad():
            feat = self.backbone(input_tensor)
            t_p = torch.sigmoid(self.threat_h(feat)).item() > 0.5
            ty_p = torch.argmax(self.type_h(feat), dim=1).item()
            j_p = torch.sigmoid(self.jammer_h(feat)).item() > 0.5
            
        action_code, status = rtl_voting_logic(t_p, ty_p, j_p)
        return {
            "threat": t_p,
            "type": ["WiFi", "DJI Drone", "Jammer"][ty_p],
            "jammer": j_p,
            "action": status,
            "code": action_code
        }

    def process_stream(self, iq_stream):
        print(f"\n{'='*80}")
        print(f"{'TIMESTAMP':<15} | {'CLASSIFICATION':<15} | {'HARDWARE ACTION':<35}")
        print(f"{'='*80}")
        
        type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}
        
        for i, sample_1d in enumerate(iq_stream):
            start_time = time.time()
            input_tensor = self.preprocess_1d_to_2d(sample_1d)
            
            with torch.no_grad():
                feat = self.backbone(input_tensor)
                t_p = torch.sigmoid(self.threat_h(feat)).item() > 0.5
                ty_p = torch.argmax(self.type_h(feat), dim=1).item()
                j_p = torch.sigmoid(self.jammer_h(feat)).item() > 0.5
            
            action_code, status = rtl_voting_logic(t_p, ty_p, j_p)
            latency = (time.time() - start_time) * 1000
            timestamp = time.strftime("%H:%M:%S")
            print(f"{timestamp} | {type_map[ty_p]:<15} | {status} ({latency:.2f}ms)")
            time.sleep(0.01)

if __name__ == "__main__":
    # Test on random samples
    dummy_stream = [np.random.randn(512) + 1j * np.random.randn(512) for _ in range(5)]
    pipeline = SkyShield2DProduction()
    pipeline.process_stream(dummy_stream)
