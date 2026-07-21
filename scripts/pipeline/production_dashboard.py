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
    """Visualize Loss and Accuracy History for technical documentation."""
    if not os.path.exists("training_history.csv"):
        print("No training history found.")
        return
    
    df = pd.read_csv("training_history.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Training and Validation Loss
    ax1.plot(df['epoch'], df['train_loss'], label='Training Loss', color='blue', linewidth=2)
    ax1.plot(df['epoch'], df['val_loss'], label='Validation Loss', color='orange', linestyle='--', linewidth=2)
    ax1.set_title('SkyShield v5.0 Pro: Multi-Task Loss Curve', fontsize=12)
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss Value')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Validation Accuracy
    ax2.plot(df['epoch'], df['val_acc'], label='Validation Accuracy', color='green', linewidth=2)
    ax2.set_title('SkyShield v5.0 Pro: Accuracy Evolution', fontsize=12)
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("viz_metrics/training_loss_accuracy.png")
    print("Documented Metrics Graph saved to viz_metrics/training_loss_accuracy.png")

def simulate_production_dashboard():
    print("\n--- SKYSHIELD v5.0 PRO: PRODUCTION DASHBOARD ---")
    
    backbone = SharedBackbone()
    threat_h = ThreatHead(192); type_h = TypeHead(192); jammer_h = JammerHead(192)
    
    try:
        backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
        threat_h.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
        type_h.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
        jammer_h.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
        print("[INIT] Pro Models Loaded Successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to load Pro models: {e}")
        return

    backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()

    X_stream = np.load("data/production/hidden_x.npy")
    ground_truth = np.load("data/production/verification_labels.npy")
    
    type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}
    os.makedirs("viz_metrics/live_inference", exist_ok=True)
    
    success_count = 0
    total_samples = 10 
    
    for i in range(total_samples):
        iq_sample = X_stream[i]
        iq_fixed = np.clip(np.round(iq_sample * 127), -128, 127)
        iq_fpga = iq_fixed / 127.0
        
        x_tensor = torch.tensor(iq_fpga, dtype=torch.float32).unsqueeze(0)
        
        with torch.no_grad():
            feat = backbone(x_tensor)
            p_threat = (torch.sigmoid(threat_h(feat).squeeze()) > 0.5).item()
            p_type = torch.argmax(type_h(feat), dim=1).item()
            p_jammer = (torch.sigmoid(jammer_h(feat).squeeze()) > 0.5).item()
            
        action_code, status = rtl_voting_logic(p_threat, p_type, p_jammer)
        expected = ground_truth[i]
        result = "CORRECT" if p_type == expected else "INCORRECT"
        if result == "CORRECT": success_count += 1
        
        print(f"Sample #{i+1:02d} | Predicted: {type_map[p_type]:<10} | Actual: {type_map[expected]:<10} | Result: {result}")

    print(f"\nFinal Real-Time Pro Accuracy: {100.*success_count/total_samples:.1f}%")

if __name__ == "__main__":
    plot_training_metrics()
    simulate_production_dashboard()
