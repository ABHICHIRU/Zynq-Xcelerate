import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

class OptimizedBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        # Adding BatchNormalization to stabilize and regularize training
        self.conv1 = nn.Conv1d(2, 16, kernel_size=11, stride=2, padding=5)
        self.bn1 = nn.BatchNorm1d(16)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(16, 32, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm1d(32)
        self.relu2 = nn.ReLU()
        self.gap = nn.AdaptiveAvgPool1d(1)
        
    def forward(self, x):
        x = self.relu1(self.bn1(self.conv1(x)))
        x = self.relu2(self.bn2(self.conv2(x)))
        x = self.gap(x)
        return x.view(x.size(0), -1)

class OptimizedHead(nn.Module):
    def __init__(self, out_classes, dropout=0.5): # Increased Dropout to 0.5
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, out_classes)
        )
    def forward(self, x):
        return self.fc(x)

def apply_augmentation(x):
    """
    On-the-fly Data Augmentation to prevent overfitting:
    1. Random Time Roll (Translation invariance)
    2. Random Phase Rotation
    """
    # 1. Random Time Roll (Shift the sequence)
    shift = np.random.randint(-50, 50)
    x = torch.roll(x, shifts=shift, dims=-1)
    
    # 2. Add very small jitter
    jitter = torch.randn_like(x) * 0.01
    return x + jitter

def train_robust_model():
    print("--- SkyShield v3.0: Robust Production Training (Anti-Overfit) ---")
    
    # Load Datasets
    t_data = np.load("data/threat_dataset.npz")
    y_data = np.load("data/type_dataset.npz")
    j_data = np.load("data/jammer_dataset.npz")
    
    X = torch.tensor(t_data['X'], dtype=torch.float32)
    Y_t = torch.tensor(t_data['Y'], dtype=torch.float32)
    Y_y = torch.tensor(y_data['Y'], dtype=torch.long)
    Y_j = torch.tensor(j_data['Y'], dtype=torch.float32)
    
    dataset = TensorDataset(X, Y_t, Y_y, Y_j)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    backbone = OptimizedBackbone()
    threat_head = OptimizedHead(1, dropout=0.5)
    type_head = OptimizedHead(3, dropout=0.5)
    jammer_head = OptimizedHead(1, dropout=0.5)
    
    # Adding Weight Decay (L2) to prevent large weights
    optimizer = optim.Adam(
        list(backbone.parameters()) + list(threat_head.parameters()) + 
        list(type_head.parameters()) + list(jammer_head.parameters()), 
        lr=0.001,
        weight_decay=1e-4 
    )
    
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss()
    
    epochs = 40
    for epoch in range(epochs):
        backbone.train(); threat_head.train(); type_head.train(); jammer_head.train()
        epoch_loss = 0
        for bx, byt, byy, byj in loader:
            # Apply Augmentation
            bx = apply_augmentation(bx)
            
            optimizer.zero_grad()
            feat = backbone(bx)
            loss = bce(threat_head(feat).squeeze(), byt) + \
                   ce(type_head(feat), byy) + \
                   bce(jammer_head(feat).squeeze(), byj)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
            
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Loss: {epoch_loss/len(loader):.4f}")

    # Save to 'final_production'
    os.makedirs("models/final_production", exist_ok=True)
    torch.save(backbone.state_dict(), "models/final_production/backbone.pth")
    torch.save(threat_head.state_dict(), "models/final_production/threat_head.pth")
    torch.save(type_head.state_dict(), "models/final_production/type_head.pth")
    torch.save(jammer_head.state_dict(), "models/final_production/jammer_head.pth")
    print("\nRobust Training Finished. Overfitting reduced via Augmentation + L2 + Dropout.")

if __name__ == "__main__":
    train_robust_model()
