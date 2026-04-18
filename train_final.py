import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np
import pandas as pd
import os

from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead

def apply_balanced_augmentation(x):
    # Reduced jitter for stability, kept time roll
    shift = np.random.randint(-100, 100)
    x = torch.roll(x, shifts=shift, dims=-1)
    noise = torch.randn_like(x) * 0.01 
    return x + noise

def train_production_ready_model():
    print("--- SkyShield v4.2: Data-Driven Production Fine-Tuning ---")
    
    t_data = np.load("data/threat_dataset.npz")
    y_data = np.load("data/type_dataset.npz")
    j_data = np.load("data/jammer_dataset.npz")
    
    X = torch.tensor(t_data['X'], dtype=torch.float32)
    Y_t = torch.tensor(t_data['Y'], dtype=torch.float32)
    Y_y = torch.tensor(y_data['Y'], dtype=torch.long)
    Y_j = torch.tensor(j_data['Y'], dtype=torch.float32)
    
    full_ds = TensorDataset(X, Y_t, Y_y, Y_j)
    train_size = int(0.9 * len(full_ds))
    val_ds, train_ds = random_split(full_ds, [len(full_ds)-train_size, train_size])
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)
    
    backbone = SharedBackbone()
    threat_h = ThreatHead(64); type_h = TypeHead(64); jammer_h = JammerHead(64)
    
    # Lower weight decay, reduced dropout in Heads (implicitly via src.core.heads update)
    optimizer = optim.Adam(
        list(backbone.parameters()) + list(threat_h.parameters()) + 
        list(type_h.parameters()) + list(jammer_h.parameters()), 
        lr=0.001, weight_decay=1e-5
    )
    
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5)
    
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss(label_smoothing=0.05)
    
    history = []
    epochs = 100 # Maximum training depth
    
    best_val_acc = 0.0
    
    for epoch in range(epochs):
        backbone.train(); threat_h.train(); type_h.train(); jammer_h.train()
        train_loss = 0
        for bx, byt, byy, byj in train_loader:
            bx = apply_balanced_augmentation(bx)
            optimizer.zero_grad()
            feat = backbone(bx)
            loss = bce(threat_h(feat).squeeze(), byt) + ce(type_h(feat), byy) + bce(jammer_h(feat).squeeze(), byj)
            loss.backward(); optimizer.step()
            train_loss += loss.item()
        
        backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()
        val_loss = 0; correct = 0; total = 0
        with torch.no_grad():
            for bx, byt, byy, byj in val_loader:
                feat = backbone(bx)
                l = bce(threat_h(feat).squeeze(), byt) + ce(type_h(feat), byy) + bce(jammer_h(feat).squeeze(), byj)
                val_loss += l.item()
                pred = torch.argmax(type_h(feat), dim=1)
                correct += (pred == byy).sum().item(); total += byy.size(0)
        
        val_acc = correct/total
        scheduler.step(val_loss)
        
        if (epoch+1) % 10 == 0:
            print(f"Epoch {epoch+1:03d} | Loss: {train_loss/len(train_loader):.4f} | Val Acc: {val_acc:.4f} | LR: {optimizer.param_groups[0]['lr']}")
        
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(backbone.state_dict(), "models/final_production/backbone.pth")
            torch.save(threat_h.state_dict(), "models/final_production/threat_head.pth")
            torch.save(type_h.state_dict(), "models/final_production/type_head.pth")
            torch.save(jammer_h.state_dict(), "models/final_production/jammer_head.pth")
            
        history.append({"epoch": epoch+1, "val_acc": val_acc})

    pd.DataFrame(history).to_csv("training_history.csv", index=False)
    print(f"Final Best Val Acc: {best_val_acc:.4f}")

if __name__ == "__main__":
    train_production_ready_model()
