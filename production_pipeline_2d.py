import torch
import torch.nn as nn
import numpy as np
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d
from src.utils.channelizer import apply_channelizer_2d
import os

class SkyShield2DProduction:
    """
    Production-ready 2D inference pipeline.
    Process 1D raw IQ signals into 2D Time-Frequency representations for classification.
    """
    def __init__(self, model_dir="models/production_2d"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Load Backbone
        self.backbone = SharedBackbone2d().to(self.device)
        self.backbone.load_state_dict(torch.load(f"{model_dir}/threat/backbone.pth", map_location=self.device))
        self.backbone.eval()
        
        # Load Heads
        self.threat_head = ThreatHead2d().to(self.device)
        self.threat_head.load_state_dict(torch.load(f"{model_dir}/threat/head.pth", map_location=self.device))
        self.threat_head.eval()
        
        self.type_head = TypeHead2d().to(self.device)
        self.type_head.load_state_dict(torch.load(f"{model_dir}/type/head.pth", map_location=self.device))
        self.type_head.eval()
        
        self.jammer_head = JammerHead2d().to(self.device)
        self.jammer_head.load_state_dict(torch.load(f"{model_dir}/jammer/head.pth", map_location=self.device))
        self.jammer_head.eval()

    def process_signal(self, iq_complex):
        """
        Takes 1D complex IQ signal, converts to 2D, and runs inference.
        """
        # 1. 1D -> 2D via Polyphase Channelizer
        x_2d = apply_channelizer_2d(iq_complex)
        x_tensor = torch.tensor(x_2d).unsqueeze(0).to(self.device) # Batch dimension
        
        with torch.no_grad():
            features = self.backbone(x_tensor)
            
            # Heads
            threat_score = torch.sigmoid(self.threat_head(features)).item()
            type_probs = torch.softmax(self.type_head(features), dim=1).cpu().numpy()[0]
            jammer_score = torch.sigmoid(self.jammer_head(features)).item()
            
        results = {
            "is_threat": threat_score > 0.5,
            "threat_confidence": threat_score,
            "classification": ["WiFi", "DJI", "Jammer"][np.argmax(type_probs)],
            "class_probs": type_probs.tolist(),
            "jammer_detected": jammer_score > 0.5,
            "jammer_confidence": jammer_score
        }
        return results

if __name__ == "__main__":
    # Example usage (requires trained models)
    if os.path.exists("models/production_2d/threat/backbone.pth"):
        pipeline = SkyShield2DProduction()
        test_iq = np.random.randn(512) + 1j * np.random.randn(512)
        results = pipeline.process_signal(test_iq)
        print("Inference Results:", results)
    else:
        print("Models not found. Please run train_2d.py first.")
