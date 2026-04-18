import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import os
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d

def train_model(model_name, backbone, head, X, Y, epochs=10, batch_size=32, is_multiclass=False):
    print(f"--- Training {model_name} ---")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    backbone.to(device)
    head.to(device)
    
    criterion = nn.CrossEntropyLoss() if is_multiclass else nn.BCEWithLogitsLoss()
    optimizer = optim.Adam(list(backbone.parameters()) + list(head.parameters()), lr=0.001)
    
    dataset = TensorDataset(torch.tensor(X), torch.tensor(Y))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    
    for epoch in range(epochs):
        backbone.train()
        head.train()
        total_loss = 0
        for batch_x, batch_y in loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            features = backbone(batch_x)
            outputs = head(features)
            
            if is_multiclass:
                loss = criterion(outputs, batch_y.long())
            else:
                loss = criterion(outputs.view(-1), batch_y.float())
                
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(loader):.4f}")
    
    os.makedirs(f"models/production_2d/{model_name}", exist_ok=True)
    torch.save(backbone.state_dict(), f"models/production_2d/{model_name}/backbone.pth")
    torch.save(head.state_dict(), f"models/production_2d/{model_name}/head.pth")

def main():
    data = np.load("data/production_2d/dataset_2d.npz")
    X = data['X']
    
    # Common backbone for all tasks
    shared_backbone = SharedBackbone2d()
    
    # 1. Threat Detection
    threat_head = ThreatHead2d()
    train_model("threat", shared_backbone, threat_head, X, data['threat_y'], epochs=15)
    
    # 2. Type Classification
    type_head = TypeHead2d()
    train_model("type", shared_backbone, type_head, X, data['type_y'], epochs=15, is_multiclass=True)
    
    # 3. Jammer Isolation
    jammer_head = JammerHead2d()
    train_model("jammer", shared_backbone, jammer_head, X, data['jammer_y'], epochs=15)

if __name__ == "__main__":
    main()
