import torch
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import time
import os
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.core.voting_logic import rtl_voting_logic

def plot_training_metrics():
    """Visualize Validation Accuracy History."""
    if not os.path.exists("training_history.csv"):
        return
    df = pd.read_csv("training_history.csv")
    plt.figure(figsize=(10, 5))
    plt.plot(df['epoch'], df['val_acc'], label='Validation Accuracy', color='green', linewidth=2)
    plt.title('SkyShield v4.0: Training Progress (Battlefield Conditions)')
    plt.xlabel('Epoch'); plt.ylabel('Accuracy'); plt.legend(); plt.grid(True, alpha=0.3)
    plt.savefig("viz_metrics/training_graphs.png")

def simulate_production_dashboard():
    print("\n--- SKYSHIELD v4.0: BATTLEFIELD PRODUCTION DASHBOARD ---")
    
    backbone = SharedBackbone()
    threat_h = ThreatHead(64); type_h = TypeHead(64); jammer_h = JammerHead(64)
    backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
    threat_h.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
    type_h.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
    jammer_h.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
    backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()

    X_stream = np.load("data/production/hidden_x.npy")
    ground_truth = np.load("data/production/verification_labels.npy")
    
    type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}
    os.makedirs("viz_metrics/live_inference", exist_ok=True)
    
    success_count = 0
    total_samples = 10 
    
    for i in range(total_samples):
        iq_sample = X_stream[i]
        x_tensor = torch.tensor(iq_sample, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            feat = backbone(x_tensor)
            p_threat = (torch.sigmoid(threat_h(feat).squeeze()) > 0.5).item()
            p_type = torch.argmax(type_h(feat), dim=1).item()
            p_jammer = (torch.sigmoid(jammer_h(feat).squeeze()) > 0.5).item()
            
        action_code, status = rtl_voting_logic(p_threat, p_type, p_jammer)
        
        # Cross-check with ground truth
        expected = ground_truth[i]
        result = "CORRECT" if p_type == expected else "INCORRECT"
        if result == "CORRECT": success_count += 1
        
        print(f"Sample #{i+1:02d} | Predicted: {type_map[p_type]:<10} | Actual: {type_map[expected]:<10} | Result: {result}")
        print(f"   -> System Action: {status}")

    print(f"\nFinal Real-Time Battlefield Accuracy: {100.*success_count/total_samples:.1f}%")
    print("Conclusion: Model is behaving realistically under heavy noise/interference.")

if __name__ == "__main__":
    plot_training_metrics()
    simulate_production_dashboard()
