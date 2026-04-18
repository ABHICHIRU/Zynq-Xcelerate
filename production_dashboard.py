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
    """Visualize the Training and Validation History."""
    if not os.path.exists("training_history.csv"):
        print("No training history found. Run train_final.py first.")
        return
    
    df = pd.read_csv("training_history.csv")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    ax1.plot(df['epoch'], df['train_loss'], label='Train Loss')
    ax1.plot(df['epoch'], df['val_loss'], label='Val Loss')
    ax1.set_title('Multi-Task Loss History')
    ax1.set_xlabel('Epoch'); ax1.set_ylabel('Loss'); ax1.legend()
    
    ax2.plot(df['epoch'], df['val_acc'], label='Type Accuracy', color='green')
    ax2.set_title('Validation Accuracy (Type Head)')
    ax2.set_xlabel('Epoch'); ax2.set_ylabel('Accuracy'); ax2.legend()
    
    plt.savefig("viz_metrics/training_graphs.png")
    print("Training graphs saved to viz_metrics/training_graphs.png")

def simulate_production_dashboard():
    """Inference on a Hidden Stream with Visualization."""
    print("\n--- INITIALIZING PRODUCTION DASHBOARD ---")
    
    # 1. Load the winning Residual-Lite v3.5 model
    backbone = SharedBackbone()
    threat_h = ThreatHead(64); type_h = TypeHead(64); jammer_h = JammerHead(64)
    backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
    threat_h.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
    type_h.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
    jammer_h.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
    backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()

    # 2. Load the Hidden Production Stream (No Cheating)
    X_stream = np.load("data/production/hidden_x.npy")
    ground_truth = np.load("data/production/verification_labels.npy")
    
    type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}
    os.makedirs("viz_metrics/live_inference", exist_ok=True)
    
    success_count = 0
    total_samples = 5 # Visualizing first 5 for the demo
    
    for i in range(total_samples):
        # A. Ingest Sample (Channelizer Simulation)
        iq_sample = X_stream[i]
        x_tensor = torch.tensor(iq_sample, dtype=torch.float32).unsqueeze(0)
        
        # B. Inference
        with torch.no_grad():
            feat = backbone(x_tensor)
            p_threat = (torch.sigmoid(threat_h(feat).squeeze()) > 0.5).item()
            p_type = torch.argmax(type_h(feat), dim=1).item()
            p_jammer = (torch.sigmoid(jammer_h(feat).squeeze()) > 0.5).item()
            
        # C. RTL Logic & Decision
        action_code, status = rtl_voting_logic(p_threat, p_type, p_jammer)
        
        # D. Visualization for Judges
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        ax1.plot(iq_sample[0], label='I', alpha=0.7); ax1.plot(iq_sample[1], label='Q', alpha=0.7)
        ax1.set_title(f"Sample #{i+1}: In-phase and Quadrature Waveform")
        ax1.legend()
        
        # Inference summary graph (Confidence Visualization)
        heads = ['Threat', 'Type (WiFi/DJI/Jam)', 'Jammer']
        confidences = [p_threat, p_type / 2.0, p_jammer] # Normalized for plotting
        ax2.bar(heads, confidences, color=['red', 'blue', 'orange'])
        ax2.set_title(f"Decision: {status}")
        ax2.set_ylim([0, 1.2])
        
        plt.savefig(f"viz_metrics/live_inference/sample_{i+1}_outcome.png")
        plt.close()
        
        # Verification (Cross-check with hidden labels)
        expected = ground_truth[i]
        result = "SUCCESS" if p_type == expected else "MISCLASSIFIED"
        if result == "SUCCESS": success_count += 1
        
        print(f"Sample #{i+1} | AI Prediction: {type_map[p_type]:<10} | True Identity: {type_map[expected]:<10} | {result}")
        print(f" -> SYSTEM ACTION: {status}")
        time.sleep(0.1)

    print(f"\nLive Stream Accuracy: {100.*success_count/total_samples:.1f}%")
    print("All live outcome graphs saved to viz_metrics/live_inference/")

if __name__ == "__main__":
    plot_training_metrics()
    simulate_production_dashboard()
