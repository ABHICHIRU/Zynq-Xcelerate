import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np
import pandas as pd
import os

from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead

def apply_heavy_augmentation(x):
    """Battlefield Augmentation to break overfitting."""
    # 1. Random Flip (I/Q swap)
    if np.random.rand() > 0.5:
        x = torch.flip(x, [1])
    
    # 2. Random Time Roll
    shift = np.random.randint(-150, 150)
    x = torch.roll(x, shifts=shift, dims=-1)
    
    # 3. Dynamic Gaussian Noise Injection
    noise = torch.randn_like(x) * np.random.uniform(0.01, 0.05)
    return x + noise

def train_battlefield_model():
    print("--- SkyShield v4.0: Battlefield Edition Training ---")
    print("Hardening: Rayleigh Fading + CFO + Heavy Augmentation + L2")
    
    # 1. Regenerate Hardened Data
    from src.data_pipeline.generator import save_datasets
    save_datasets()
    
    t_data = np.load("data/threat_dataset.npz")
    y_data = np.load("data/type_dataset.npz")
    j_data = np.load("data/jammer_dataset.npz")
    
    X = torch.tensor(t_data['X'], dtype=torch.float32)
    Y_t = torch.tensor(t_data['Y'], dtype=torch.float32)
    Y_y = torch.tensor(y_data['Y'], dtype=torch.long)
    Y_j = torch.tensor(j_data['Y'], dtype=torch.float32)
    
    full_ds = TensorDataset(X, Y_t, Y_y, Y_j)
    train_size = int(0.85 * len(full_ds))
    val_size = len(full_ds) - train_size
    train_ds, val_ds = random_split(full_ds, [train_size, val_size])
    
    train_loader = DataLoader(train_ds, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)
    
    backbone = SharedBackbone()
    threat_h = ThreatHead(64); type_h = TypeHead(64); jammer_h = JammerHead(64)
    
    # Heavy L2 Regularization (Weight Decay 1e-3)
    optimizer = optim.Adam(
        list(backbone.parameters()) + list(threat_h.parameters()) + 
        list(type_h.parameters()) + list(jammer_h.parameters()), 
        lr=0.001, weight_decay=1e-3 
    )
    
    # Use Label Smoothing in Loss (Prevents 100% certainty overfitting)
    bce = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([1.2])) # Slight bias for threats
    ce = nn.CrossEntropyLoss(label_smoothing=0.1) 
    
    history = []
    epochs = 75 # Longer training for harder physics
    
    for epoch in range(epochs):
        backbone.train(); threat_h.train(); type_h.train(); jammer_h.train()
        train_loss = 0
        for bx, byt, byy, byj in train_loader:
            bx = apply_heavy_augmentation(bx)
            optimizer.zero_grad()
            feat = backbone(bx)
            loss = bce(threat_h(feat).squeeze(), byt) + ce(type_h(feat), byy) + bce(jammer_h(feat).squeeze(), byj)
            loss.backward(); optimizer.step()
            train_loss += loss.item()
        
        # Validation (No Augmentation)
        backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()
        val_loss = 0; correct = 0; total = 0
        with torch.no_grad():
            for bx, byt, byy, byj in val_loader:
                feat = backbone(bx)
                l = bce(threat_h(feat).squeeze(), byt) + ce(type_h(feat), byy) + bce(jammer_h(feat).squeeze(), byj)
                val_loss += l.item()
                pred = torch.argmax(type_h(feat), dim=1)
                correct += (pred == byy).sum().item(); total += byy.size(0)
        
        acc = correct/total
        if (epoch+1) % 15 == 0:
            print(f"Epoch {epoch+1:02d} | Loss: {train_loss/len(train_loader):.4f} | Val Acc: {acc:.4f}")
        history.append({"epoch": epoch+1, "val_acc": acc})

    os.makedirs("models/final_production", exist_ok=True)
    torch.save(backbone.state_dict(), "models/final_production/backbone.pth")
    torch.save(threat_h.state_dict(), "models/final_production/threat_head.pth")
    torch.save(type_h.state_dict(), "models/final_production/type_head.pth")
    torch.save(jammer_h.state_dict(), "models/final_production/jammer_head.pth")
    pd.DataFrame(history).to_csv("training_history.csv", index=False)
    print("V4.0 Battlefield Model Trained and Saved.")

if __name__ == "__main__":
    train_battlefield_model()
