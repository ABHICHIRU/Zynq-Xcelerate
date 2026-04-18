import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

# Import the NEW SkyShield v3.5 Architecture
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead

def apply_augmentation(x):
    """
    On-the-fly Data Augmentation for Robustness:
    - Time Roll (Phase Invariance)
    - Add jitter (Noise robustness)
    """
    shift = np.random.randint(-100, 100)
    x = torch.roll(x, shifts=shift, dims=-1)
    jitter = torch.randn_like(x) * 0.02 # Increased jitter for robustness
    return x + jitter

def train_robust_production_model():
    print("--- SkyShield v3.5: Residual Production Training ---")
    
    # Load Datasets
    t_data = np.load("data/threat_dataset.npz")
    y_data = np.load("data/type_dataset.npz")
    j_data = np.load("data/jammer_dataset.npz")
    
    X = torch.tensor(t_data['X'], dtype=torch.float32)
    Y_t = torch.tensor(t_data['Y'], dtype=torch.float32)
    Y_y = torch.tensor(y_data['Y'], dtype=torch.long)
    Y_j = torch.tensor(j_data['Y'], dtype=torch.float32)
    
    dataset = TensorDataset(X, Y_t, Y_y, Y_j)
    loader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    backbone = SharedBackbone()
    threat_h = ThreatHead(in_features=64)
    type_h = TypeHead(in_features=64)
    jammer_h = JammerHead(in_features=64)
    
    # Use Weight Decay for Regularization
    optimizer = optim.Adam(
        list(backbone.parameters()) + list(threat_h.parameters()) + 
        list(type_h.parameters()) + list(jammer_h.parameters()), 
        lr=0.001,
        weight_decay=1e-4
    )
    
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss()
    
    epochs = 60 # More epochs for complex model to converge
    for epoch in range(epochs):
        backbone.train(); threat_h.train(); type_h.train(); jammer_h.train()
        epoch_loss = 0
        for bx, byt, byy, byj in loader:
            bx = apply_augmentation(bx)
            optimizer.zero_grad()
            feat = backbone(bx)
            loss = bce(threat_h(feat).squeeze(), byt) + \
                   ce(type_h(feat), byy) + \
                   bce(jammer_h(feat).squeeze(), byj)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1:02d}/{epochs} | Loss: {epoch_loss/len(loader):.4f}")

    # Save Final Production Weights
    os.makedirs("models/final_production", exist_ok=True)
    torch.save(backbone.state_dict(), "models/final_production/backbone.pth")
    torch.save(threat_h.state_dict(), "models/final_production/threat_head.pth")
    torch.save(type_h.state_dict(), "models/final_production/type_head.pth")
    torch.save(jammer_h.state_dict(), "models/final_production/jammer_head.pth")
    print("\nRobust SkyShield v3.5 Training Finished.")

if __name__ == "__main__":
    train_robust_production_model()
