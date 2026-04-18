import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

# Import components from existing files
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead

# Best Params from AutoML: {'f1': 16, 'f2': 32, 'k': 11, 'h': 16, 'drop': 0.2, 'lr': 0.005}
class OptimizedBackbone(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(2, 16, kernel_size=11, stride=2, padding=5)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(16, 32, kernel_size=3, stride=2, padding=1)
        self.relu2 = nn.ReLU()
        self.gap = nn.AdaptiveAvgPool1d(1)
    def forward(self, x):
        x = self.relu1(self.conv1(x))
        x = self.relu2(self.conv2(x))
        x = self.gap(x)
        return x.view(x.size(0), -1)

class OptimizedHead(nn.Module):
    def __init__(self, out_classes, dropout=0.2):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, out_classes)
        )
    def forward(self, x):
        return self.fc(x)

def train_to_completion():
    print("--- SkyShield v3.0: Final Production Training ---")
    
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
    
    # Init Optimized Models
    backbone = OptimizedBackbone()
    threat_head = OptimizedHead(1)
    type_head = OptimizedHead(3)
    jammer_head = OptimizedHead(1)
    
    optimizer = optim.Adam(
        list(backbone.parameters()) + list(threat_head.parameters()) + 
        list(type_head.parameters()) + list(jammer_head.parameters()), 
        lr=0.005
    )
    
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss()
    
    # Training Loop
    epochs = 50
    for epoch in range(epochs):
        backbone.train(); threat_head.train(); type_head.train(); jammer_head.train()
        epoch_loss = 0
        for bx, byt, byy, byj in loader:
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

    # Final Save
    os.makedirs("models/final_production", exist_ok=True)
    torch.save(backbone.state_dict(), "models/final_production/backbone.pth")
    torch.save(threat_head.state_dict(), "models/final_production/threat_head.pth")
    torch.save(type_head.state_dict(), "models/final_production/type_head.pth")
    torch.save(jammer_head.state_dict(), "models/final_production/jammer_head.pth")
    
    # Copy to 'best' for the demo script
    os.makedirs("models/best", exist_ok=True)
    import shutil
    shutil.copy("models/final_production/backbone.pth", "models/best/backbone.pth")
    shutil.copy("models/final_production/threat_head.pth", "models/best/threat_head.pth")
    shutil.copy("models/final_production/type_head.pth", "models/best/type_head.pth")
    shutil.copy("models/final_production/jammer_head.pth", "models/best/jammer_head.pth")
    
    print("\nTraining Finished. Production weights saved to models/final_production/")

if __name__ == "__main__":
    train_to_completion()
