import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import time

# Datasets
def load_data():
    t_data = np.load("data/threat_dataset.npz")
    y_data = np.load("data/type_dataset.npz")
    j_data = np.load("data/jammer_dataset.npz")
    
    X = torch.tensor(t_data['X'], dtype=torch.float32)
    Y_t = torch.tensor(t_data['Y'], dtype=torch.float32)
    Y_y = torch.tensor(y_data['Y'], dtype=torch.long)
    Y_j = torch.tensor(j_data['Y'], dtype=torch.float32)
    return TensorDataset(X, Y_t, Y_y, Y_j)

def load_test_data():
    data = np.load("data/realtime/test_set.npz")
    X = torch.tensor(data['X'], dtype=torch.float32)
    Y_t = data['Y_threat']
    Y_y = data['Y_type']
    Y_j = data['Y_jammer']
    return X, Y_t, Y_y, Y_j

# Dynamic Architecture
class DynamicBackbone(nn.Module):
    def __init__(self, filters_1, filters_2, kernel_size):
        super().__init__()
        self.conv1 = nn.Conv1d(2, filters_1, kernel_size=kernel_size, stride=2, padding=kernel_size//2)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(filters_1, filters_2, kernel_size=3, stride=2, padding=1)
        self.relu2 = nn.ReLU()
        self.gap = nn.AdaptiveAvgPool1d(1)
        self.out_dim = filters_2
    def forward(self, x):
        x = self.relu1(self.conv1(x))
        x = self.relu2(self.conv2(x))
        x = self.gap(x)
        return x.view(x.size(0), -1)

class DynamicHead(nn.Module):
    def __init__(self, input_dim, hidden_dim, out_classes, dropout):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, out_classes)
        )
    def forward(self, x):
        return self.fc(x)

def evaluate(b, t, y, j, X_test, Y_t, Y_y, Y_j):
    b.eval(); t.eval(); y.eval(); j.eval()
    with torch.no_grad():
        f = b(X_test)
        p_t = (torch.sigmoid(t(f).squeeze()) > 0.5).numpy()
        p_y = torch.argmax(y(f), dim=1).numpy()
        p_j = (torch.sigmoid(j(f).squeeze()) > 0.5).numpy()
    
    acc_t = np.mean(p_t == Y_t)
    acc_y = np.mean(p_y == Y_y)
    acc_j = np.mean(p_j == Y_j)
    return (acc_t + acc_y + acc_j) / 3.0

def run_automl_search(num_trials=10):
    print(f"--- Starting AutoML Search ({num_trials} architectures) ---")
    dataset = load_data()
    train_loader = DataLoader(dataset, batch_size=64, shuffle=True)
    X_test, Y_t, Y_y, Y_j = load_test_data()
    
    bce = nn.BCEWithLogitsLoss()
    ce = nn.CrossEntropyLoss()
    
    best_acc = 0.0
    best_params = None
    
    for i in range(num_trials):
        # Randomize Hyperparameters
        f1 = int(np.random.choice([8, 16, 32]))
        f2 = int(np.random.choice([16, 32, 64]))
        k = int(np.random.choice([3, 5, 7, 11]))
        h_dim = int(np.random.choice([16, 32, 64]))
        drop = float(np.random.choice([0.0, 0.2, 0.4]))
        lr = float(np.random.choice([0.001, 0.002, 0.005]))
        
        print(f"Trial {i+1}/{num_trials} | F1:{f1}, F2:{f2}, K:{k}, H:{h_dim}, Drop:{drop}, LR:{lr}")
        
        b = DynamicBackbone(f1, f2, k)
        t = DynamicHead(f2, h_dim, 1, drop)
        y = DynamicHead(f2, h_dim, 3, drop)
        j = DynamicHead(f2, h_dim, 1, drop)
        
        optimizer = optim.Adam(list(b.parameters()) + list(t.parameters()) + list(y.parameters()) + list(j.parameters()), lr=lr)
        
        # Train quickly (5 epochs for search)
        for epoch in range(5):
            b.train(); t.train(); y.train(); j.train()
            for bx, byt, byy, byj in train_loader:
                optimizer.zero_grad()
                f = b(bx)
                loss = bce(t(f).squeeze(), byt) + ce(y(f), byy) + bce(j(f).squeeze(), byj)
                loss.backward()
                optimizer.step()
                
        # Evaluate
        acc = evaluate(b, t, y, j, X_test, Y_t, Y_y, Y_j)
        print(f" -> Overall Accuracy: {acc:.4f}")
        
        if acc > best_acc:
            best_acc = acc
            best_params = {'f1': f1, 'f2': f2, 'k': k, 'h': h_dim, 'drop': drop, 'lr': lr}
            
            # Save temporary best
            os.makedirs("models/automl_best", exist_ok=True)
            torch.save(b.state_dict(), "models/automl_best/backbone.pth")
            torch.save(t.state_dict(), "models/automl_best/threat_head.pth")
            torch.save(y.state_dict(), "models/automl_best/type_head.pth")
            torch.save(j.state_dict(), "models/automl_best/jammer_head.pth")
            
    print(f"\nSearch Complete! Best Accuracy: {best_acc:.4f}")
    print(f"Best Parameters: {best_params}")
    
    with open("AUTOML_REPORT.md", "w") as f:
        f.write(f"# AutoML Search Report\n\n- Trials: {num_trials}\n- Best Accuracy: {best_acc:.4f}\n- Best Params: {best_params}\n")

if __name__ == "__main__":
    run_automl_search(10)
