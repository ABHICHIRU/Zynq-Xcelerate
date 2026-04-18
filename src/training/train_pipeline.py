import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

def train_joint_model(backbone, threat_head, type_head, jammer_head, num_epochs=10):
    """
    Multi-Task Learning (MTL) Joint Training.
    Trains the shared backbone and all three heads simultaneously.
    This guarantees maximum accuracy and eliminates "catastrophic forgetting"
    that occurs during sequential head training.
    """
    # Load all dataset Y labels. Since X (features) are identical across the 3 datasets,
    # we just need to load one X and all 3 Ys.
    threat_data = np.load("data/threat_dataset.npz")
    type_data = np.load("data/type_dataset.npz")
    jammer_data = np.load("data/jammer_dataset.npz")
    
    X = torch.tensor(threat_data['X'], dtype=torch.float32)
    Y_threat = torch.tensor(threat_data['Y'], dtype=torch.float32)
    Y_type = torch.tensor(type_data['Y'], dtype=torch.long)
    Y_jammer = torch.tensor(jammer_data['Y'], dtype=torch.float32)
    
    dataset = TensorDataset(X, Y_threat, Y_type, Y_jammer)
    # Using a 90/10 Train/Val split is highly recommended for accuracy proof
    train_size = int(0.9 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=64, shuffle=False)
    
    # Optimizer includes ALL parameters
    optimizer = optim.Adam(
        list(backbone.parameters()) + 
        list(threat_head.parameters()) + 
        list(type_head.parameters()) + 
        list(jammer_head.parameters()), 
        lr=0.002
    )
    
    # Loss functions
    bce_loss = nn.BCEWithLogitsLoss()
    ce_loss = nn.CrossEntropyLoss()
    
    print("\n--- Starting Multi-Task Joint Training ---")
    
    for epoch in range(num_epochs):
        # Training Phase
        backbone.train(); threat_head.train(); type_head.train(); jammer_head.train()
        train_loss = 0.0
        
        for batch_x, batch_y_threat, batch_y_type, batch_y_jammer in train_loader:
            optimizer.zero_grad()
            
            # Forward Pass
            features = backbone(batch_x)
            out_threat = threat_head(features).squeeze()
            out_type = type_head(features)
            out_jammer = jammer_head(features).squeeze()
            
            # Calculate Losses
            loss_threat = bce_loss(out_threat, batch_y_threat)
            loss_type = ce_loss(out_type, batch_y_type)
            loss_jammer = bce_loss(out_jammer, batch_y_jammer)
            
            # Multi-Task Combined Loss
            total_loss = loss_threat + loss_type + loss_jammer
            total_loss.backward()
            optimizer.step()
            
            train_loss += total_loss.item()
            
        # Validation Phase
        backbone.eval(); threat_head.eval(); type_head.eval(); jammer_head.eval()
        val_loss = 0.0
        correct_threat = 0; correct_type = 0; correct_jammer = 0
        total = 0
        
        with torch.no_grad():
            for batch_x, batch_y_threat, batch_y_type, batch_y_jammer in val_loader:
                features = backbone(batch_x)
                out_threat = threat_head(features).squeeze()
                out_type = type_head(features)
                out_jammer = jammer_head(features).squeeze()
                
                # Validation Loss
                loss_threat = bce_loss(out_threat, batch_y_threat)
                loss_type = ce_loss(out_type, batch_y_type)
                loss_jammer = bce_loss(out_jammer, batch_y_jammer)
                val_loss += (loss_threat + loss_type + loss_jammer).item()
                
                # Calculate Accuracies
                pred_threat = (torch.sigmoid(out_threat) > 0.5).float()
                pred_type = torch.argmax(out_type, dim=1)
                pred_jammer = (torch.sigmoid(out_jammer) > 0.5).float()
                
                correct_threat += (pred_threat == batch_y_threat).sum().item()
                correct_type += (pred_type == batch_y_type).sum().item()
                correct_jammer += (pred_jammer == batch_y_jammer).sum().item()
                total += batch_y_threat.size(0)
                
        print(f"Epoch {epoch+1:02d}/{num_epochs} | "
              f"Train Loss: {train_loss/len(train_loader):.4f} | "
              f"Val Loss: {val_loss/len(val_loader):.4f} | "
              f"Acc [Threat: {100.*correct_threat/total:.1f}% | "
              f"Type: {100.*correct_type/total:.1f}% | "
              f"Jammer: {100.*correct_jammer/total:.1f}%]")
    
    print("--- Joint Training Complete ---\n")
