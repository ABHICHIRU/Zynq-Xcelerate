import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split
import numpy as np
import pandas as pd

from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d

def hardware_preprocessing_sim_2d(x):
    x_fixed = torch.clamp(torch.round(x * 127), -128, 127)
    return x_fixed / 127.0

def apply_hardened_augmentation_2d(x):
    # 1. Random Time/Freq Shift
    t_shift = np.random.randint(-20, 20)
    f_shift = np.random.randint(-10, 10)
    x = torch.roll(x, shifts=(f_shift, t_shift), dims=(-2, -1))
    
    # 2. Aggressive Frequency Masking
    if np.random.rand() > 0.5:
        h = x.shape[-2]
        f_start = np.random.randint(0, h-15)
        x[..., f_start:f_start+15, :] = -1.0
        
    # 3. Gaussian Noise + Dropout
    x = x + torch.randn_like(x) * 0.04
    return hardware_preprocessing_sim_2d(x)

def train_ultra_model_2d():
    print("--- SkyShield v7.1 Echelon-X (Hardened): Ultra-Elite Training ---")
    
    if not os.path.exists("data/production_2d/dataset_2d.npz"):
        print("[ERROR] Massive Dataset not found. Run 'python src/data_pipeline/generator_2d.py' first.")
        return

    data = np.load("data/production_2d/dataset_2d.npz")
    X = torch.tensor(data['X'], dtype=torch.float32)
    Y_t = torch.tensor(data['threat_y'], dtype=torch.float32)
    Y_y = torch.tensor(data['type_y'], dtype=torch.long)
    Y_j = torch.tensor(data['jammer_y'], dtype=torch.float32)
    
    full_ds = TensorDataset(X, Y_t, Y_y, Y_j)
    train_size = int(0.9 * len(full_ds)) # 90/10 split
    val_ds, train_ds = random_split(full_ds, [len(full_ds)-train_size, train_size])
    
    train_loader = DataLoader(train_ds, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    backbone = SharedBackbone2d().to(device)
    threat_h = ThreatHead2d(384).to(device)
    type_h = TypeHead2d(384).to(device)
    jammer_h = JammerHead2d(384).to(device)
    
    # Stronger Weight Decay (0.05) and smaller Learning Rate
    optimizer = optim.AdamW(
        list(backbone.parameters()) + list(threat_h.parameters()) + 
        list(type_h.parameters()) + list(jammer_h.parameters()), 
        lr=0.0005, weight_decay=0.05
    )
    
    scheduler = optim.lr_scheduler.CosineAnnealingWarmRestarts(optimizer, T_0=10, T_mult=2)
    
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss(label_smoothing=0.15) # Increased label smoothing
    
    history = []
    epochs = 70
    best_val_acc = 0.0
    
    for epoch in range(epochs):
        backbone.train(); threat_h.train(); type_h.train(); jammer_h.train()
        train_loss = 0
        for bx, byt, byy, byj in train_loader:
            bx, byt, byy, byj = bx.to(device), byt.to(device), byy.to(device), byj.to(device)
            bx = apply_hardened_augmentation_2d(bx)
            
            optimizer.zero_grad()
            feat = backbone(bx)
            loss = bce(threat_h(feat).squeeze(), byt) + ce(type_h(feat), byy) + bce(jammer_h(feat).squeeze(), byj)
            loss.backward(); optimizer.step()
            train_loss += loss.item()
        
        scheduler.step()
        
        backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()
        val_loss = 0; correct = 0; total = 0
        with torch.no_grad():
            for bx, byt, byy, byj in val_loader:
                bx, byt, byy, byj = bx.to(device), byt.to(device), byy.to(device), byj.to(device)
                bx = hardware_preprocessing_sim_2d(bx)
                feat = backbone(bx)
                pred = torch.argmax(type_h(feat), dim=1)
                correct += (pred == byy).sum().item(); total += byy.size(0)
                val_loss += (bce(threat_h(feat).squeeze(), byt) + ce(type_h(feat), byy) + bce(jammer_h(feat).squeeze(), byj)).item()
        
        val_acc = correct/total
        avg_train_loss = train_loss/len(train_loader)
        avg_val_loss = val_loss/len(val_loader)
        
        if (epoch+1) % 1 == 0:
            print(f"Epoch {epoch+1:03d} | T-Loss: {avg_train_loss:.4f} | V-Acc: {val_acc:.4f}")
            
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            save_dir = "models/production_2d_elite"
            os.makedirs(save_dir, exist_ok=True)
            torch.save(backbone.state_dict(), f"{save_dir}/backbone.pth")
            torch.save(threat_h.state_dict(), f"{save_dir}/threat_head.pth")
            torch.save(type_h.state_dict(), f"{save_dir}/type_head.pth")
            torch.save(jammer_h.state_dict(), f"{save_dir}/jammer_head.pth")
            
        history.append({"epoch": epoch+1, "train_loss": avg_train_loss, "val_loss": avg_val_loss, "val_acc": val_acc})

    pd.DataFrame(history).to_csv("training_history_2d.csv", index=False)
    print(f"SkyShield v7.1 Hardened Complete. Best Val Acc: {best_val_acc:.4f}")

if __name__ == "__main__":
    train_ultra_model_2d()
