import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

# Import existing generators
from src.data_pipeline.generator import generate_wifi_dsss, generate_dji_pulse, generate_jammer

# Import existing architecture as Baseline
from src.core.backbone import SharedBackbone as BackboneV1
from src.core.heads import ThreatHead as ThreatHeadV1, TypeHead as TypeHeadV1, JammerHead as JammerHeadV1
from src.core.voting_logic import rtl_voting_logic

# ==========================================
# 1. NEW ARCHITECTURES (EXPERIMENTS)
# ==========================================

class BackboneV2(nn.Module):
    """Wider, deeper architecture. Higher accuracy, potentially higher latency."""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(2, 32, kernel_size=7, stride=2, padding=3)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, stride=2, padding=2)
        self.relu2 = nn.ReLU()
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, stride=2, padding=1)
        self.relu3 = nn.ReLU()
        self.gap = nn.AdaptiveAvgPool1d(1)
        
    def forward(self, x):
        x = self.relu1(self.conv1(x))
        x = self.relu2(self.conv2(x))
        x = self.relu3(self.conv3(x))
        x = self.gap(x)
        return x.view(x.size(0), -1) # 128 dim

class HeadV2(nn.Module):
    def __init__(self, input_dim=128, out_classes=1):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, out_classes)
        )
    def forward(self, x):
        return self.fc(x)

class BackboneV3(nn.Module):
    """Ultra-lightweight architecture for minimal latency on FPGA."""
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(2, 8, kernel_size=5, stride=4, padding=2)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(8, 16, kernel_size=3, stride=2, padding=1)
        self.relu2 = nn.ReLU()
        self.gap = nn.AdaptiveAvgPool1d(1)
        
    def forward(self, x):
        x = self.relu1(self.conv1(x))
        x = self.relu2(self.conv2(x))
        x = self.gap(x)
        return x.view(x.size(0), -1) # 16 dim

class HeadV3(nn.Module):
    def __init__(self, input_dim=16, out_classes=1):
        super().__init__()
        self.fc = nn.Sequential(
            nn.Linear(input_dim, out_classes) # Direct mapping
        )
    def forward(self, x):
        return self.fc(x)

# ==========================================
# 2. DATASET GENERATION (REALTIME HOLDOUT)
# ==========================================

def generate_realtime_dataset():
    print("\n--- Generating Realtime Test Dataset (Simulated Live Intercepts) ---")
    np.random.seed(999) # Different seed for holdout set
    n_samples = 500 # 500 per class = 1500 total
    
    wifi = np.array([generate_wifi_dsss(np.random.uniform(-10, 15)) for _ in range(n_samples)])
    dji = np.array([generate_dji_pulse(np.random.uniform(-10, 15)) for _ in range(n_samples)])
    jammer = np.array([generate_jammer(np.random.uniform(-10, 15)) for _ in range(n_samples)])
    
    X = np.concatenate([wifi, dji, jammer])
    
    # Y Threat: 0=WiFi, 1=DJI+Jammer
    Y_threat = np.concatenate([np.zeros(n_samples), np.ones(2*n_samples)])
    # Y Type: 0=WiFi, 1=DJI, 2=Jammer
    Y_type = np.concatenate([np.zeros(n_samples), np.ones(n_samples), np.ones(n_samples)*2])
    # Y Jammer: 0=WiFi+DJI, 1=Jammer
    Y_jammer = np.concatenate([np.zeros(2*n_samples), np.ones(n_samples)])
    
    os.makedirs("data/realtime", exist_ok=True)
    np.savez("data/realtime/test_set.npz", X=X, Y_threat=Y_threat, Y_type=Y_type, Y_jammer=Y_jammer)
    print("Realtime test set generated and saved to data/realtime/test_set.npz")

# ==========================================
# 3. TRAINING ENGINE
# ==========================================

def train_experiment(name, backbone, threat_head, type_head, jammer_head, epochs=10, lr=0.002):
    print(f"\n--- Training Experiment: {name} ---")
    
    # Load training data
    threat_data = np.load("data/threat_dataset.npz")
    type_data = np.load("data/type_dataset.npz")
    jammer_data = np.load("data/jammer_dataset.npz")
    
    X = torch.tensor(threat_data['X'], dtype=torch.float32)
    Y_threat = torch.tensor(threat_data['Y'], dtype=torch.float32)
    Y_type = torch.tensor(type_data['Y'], dtype=torch.long)
    Y_jammer = torch.tensor(jammer_data['Y'], dtype=torch.float32)
    
    dataset = TensorDataset(X, Y_threat, Y_type, Y_jammer)
    train_loader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    optimizer = optim.Adam(
        list(backbone.parameters()) + list(threat_head.parameters()) + 
        list(type_head.parameters()) + list(jammer_head.parameters()), lr=lr)
    
    bce_loss = nn.BCEWithLogitsLoss()
    ce_loss = nn.CrossEntropyLoss()
    
    for epoch in range(epochs):
        backbone.train(); threat_head.train(); type_head.train(); jammer_head.train()
        train_loss = 0
        for batch_x, batch_y_threat, batch_y_type, batch_y_jammer in train_loader:
            optimizer.zero_grad()
            features = backbone(batch_x)
            loss = bce_loss(threat_head(features).squeeze(), batch_y_threat) + \
                   ce_loss(type_head(features), batch_y_type) + \
                   bce_loss(jammer_head(features).squeeze(), batch_y_jammer)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        print(f"Epoch {epoch+1}/{epochs}, Loss: {train_loss/len(train_loader):.4f}")
        
    # Save model
    out_dir = f"models/{name}"
    os.makedirs(out_dir, exist_ok=True)
    torch.save(backbone.state_dict(), f"{out_dir}/backbone.pth")
    torch.save(threat_head.state_dict(), f"{out_dir}/threat_head.pth")
    torch.save(type_head.state_dict(), f"{out_dir}/type_head.pth")
    torch.save(jammer_head.state_dict(), f"{out_dir}/jammer_head.pth")
    print(f"Saved {name} models to {out_dir}/")

# ==========================================
# 4. BENCHMARKING ENGINE
# ==========================================

def evaluate_model(name, backbone, threat_head, type_head, jammer_head):
    data = np.load("data/realtime/test_set.npz")
    X = torch.tensor(data['X'], dtype=torch.float32)
    Y_threat = data['Y_threat']
    Y_type = data['Y_type']
    Y_jammer = data['Y_jammer']
    
    # Load weights
    backbone.load_state_dict(torch.load(f"models/{name}/backbone.pth", weights_only=True))
    threat_head.load_state_dict(torch.load(f"models/{name}/threat_head.pth", weights_only=True))
    type_head.load_state_dict(torch.load(f"models/{name}/type_head.pth", weights_only=True))
    jammer_head.load_state_dict(torch.load(f"models/{name}/jammer_head.pth", weights_only=True))
    
    backbone.eval(); threat_head.eval(); type_head.eval(); jammer_head.eval()
    
    # Measure latency
    start_time = time.time()
    with torch.no_grad():
        features = backbone(X)
        pred_threat = (torch.sigmoid(threat_head(features).squeeze()) > 0.5).numpy()
        pred_type = torch.argmax(type_head(features), dim=1).numpy()
        pred_jammer = (torch.sigmoid(jammer_head(features).squeeze()) > 0.5).numpy()
    end_time = time.time()
    
    latency_ms = ((end_time - start_time) / len(X)) * 1000
    
    # Metrics
    acc_threat = accuracy_score(Y_threat, pred_threat)
    acc_type = accuracy_score(Y_type, pred_type)
    acc_jammer = accuracy_score(Y_jammer, pred_jammer)
    
    overall_acc = (acc_threat + acc_type + acc_jammer) / 3.0
    
    return {
        "name": name,
        "acc_threat": acc_threat,
        "acc_type": acc_type,
        "acc_jammer": acc_jammer,
        "overall_acc": overall_acc,
        "latency_ms": latency_ms
    }

def run_benchmarks():
    print("\n--- Running Benchmarks on Realtime Dataset ---")
    results = []
    
    # Eval V1 (Baseline)
    results.append(evaluate_model("v1_baseline", BackboneV1(), ThreatHeadV1(), TypeHeadV1(), JammerHeadV1()))
    
    # Eval V2 (Wider)
    results.append(evaluate_model("v2_wider", BackboneV2(), HeadV2(128, 1), HeadV2(128, 3), HeadV2(128, 1)))
    
    # Eval V3 (Lightweight)
    results.append(evaluate_model("v3_lightweight", BackboneV3(), HeadV3(16, 1), HeadV3(16, 3), HeadV3(16, 1)))
    
    # Sort by overall accuracy
    results.sort(key=lambda x: x['overall_acc'], reverse=True)
    
    # Generate Report
    report = "# Realtime Dataset Benchmark Report\n\n"
    report += "| Model | Overall Acc | Threat Acc | Type Acc | Jammer Acc | Latency/Sample |\n"
    report += "|---|---|---|---|---|---|\n"
    
    for r in results:
        report += f"| {r['name']} | {r['overall_acc']:.4f} | {r['acc_threat']:.4f} | {r['acc_type']:.4f} | {r['acc_jammer']:.4f} | {r['latency_ms']:.4f} ms |\n"
        
    report += "\n## Analysis\n"
    report += f"The **{results[0]['name']}** model performed the best in terms of overall accuracy ({results[0]['overall_acc']:.4f}).\n"
    
    with open("BENCHMARK_REPORT.md", "w") as f:
        f.write(report)
        
    print("Benchmarking complete. See BENCHMARK_REPORT.md for details.")
    return results[0] # Best model

if __name__ == "__main__":
    # 1. Generate Holdout Set
    generate_realtime_dataset()
    
    # 2. Train V1 (Baseline)
    train_experiment("v1_baseline", BackboneV1(), ThreatHeadV1(), TypeHeadV1(), JammerHeadV1(), epochs=15)
    
    # 3. Train V2 (Wider)
    train_experiment("v2_wider", BackboneV2(), HeadV2(128, 1), HeadV2(128, 3), HeadV2(128, 1), epochs=15)
    
    # 4. Train V3 (Lightweight)
    train_experiment("v3_lightweight", BackboneV3(), HeadV3(16, 1), HeadV3(16, 3), HeadV3(16, 1), epochs=15)
    
    # 5. Benchmark and Output Report
    best_model = run_benchmarks()
    
    # Optional: Copy best model to models/best/
    import shutil
    os.makedirs("models/best", exist_ok=True)
    src_dir = f"models/{best_model['name']}"
    for file in os.listdir(src_dir):
        shutil.copy(os.path.join(src_dir, file), os.path.join("models/best", file))
    print(f"Copied best model weights ({best_model['name']}) to models/best/")
