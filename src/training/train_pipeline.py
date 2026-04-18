import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

def train_head(backbone, head, dataset_path, num_epochs=5, is_multiclass=False):
    """
    Trains a specific head while keeping the backbone gradients isolated.
    In a real FPGA pipeline, we might freeze the backbone or train jointly.
    """
    data = np.load(dataset_path)
    X = torch.tensor(data['X'], dtype=torch.float32)
    Y = torch.tensor(data['Y'], dtype=torch.float32 if not is_multiclass else torch.long)
    
    dataset = TensorDataset(X, Y)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    optimizer = optim.Adam(list(backbone.parameters()) + list(head.parameters()), lr=0.001)
    criterion = nn.CrossEntropyLoss() if is_multiclass else nn.BCEWithLogitsLoss()
    
    backbone.train()
    head.train()
    
    for epoch in range(num_epochs):
        total_loss = 0
        for batch_x, batch_y in loader:
            optimizer.zero_grad()
            features = backbone(batch_x)
            outputs = head(features)
            
            if not is_multiclass:
                outputs = outputs.squeeze()
                
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        
        print(f"Epoch {epoch+1}/{num_epochs}, Loss: {total_loss/len(loader):.4f}")
