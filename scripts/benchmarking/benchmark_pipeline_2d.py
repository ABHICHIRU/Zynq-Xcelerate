import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.metrics import accuracy_score

# Import 2D Architectures
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d
from src.utils.channelizer import apply_channelizer_2d
from src.data_pipeline.generator_2d import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def generate_2d_realtime_holdout():
    print("\n--- Generating 2D Real-Time Holdout Set ---")
    np.random.seed(42)
    n_samples = 100 # Balanced benchmark
    
    X_2d = []
    y_threat, y_type, y_jammer = [], [], []
    
    for _ in range(n_samples):
        snr = np.random.uniform(-10, 15)
        # WiFi
        X_2d.append(apply_channelizer_2d(generate_wifi_dsss(snr)))
        y_threat.append(0); y_type.append(0); y_jammer.append(0)
        # DJI
        X_2d.append(apply_channelizer_2d(generate_dji_pulse(snr)))
        y_threat.append(1); y_type.append(1); y_jammer.append(0)
        # Jammer
        X_2d.append(apply_channelizer_2d(generate_jammer(snr)))
        y_threat.append(1); y_type.append(2); y_jammer.append(1)
        
    X_2d = np.array(X_2d)
    os.makedirs("data/realtime_2d", exist_ok=True)
    np.savez("data/realtime_2d/test_set.npz", 
             X=X_2d, 
             Y_threat=np.array(y_threat), 
             Y_type=np.array(y_type), 
             Y_jammer=np.array(y_jammer))
    print(f"2D Holdout set saved.")

def benchmark_production_model_2d():
    print("\n--- Benchmarking Production 2D Echelon Elite ---")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # 1. Load Real-Time Holdout
    if not os.path.exists("data/realtime_2d/test_set.npz"):
        generate_2d_realtime_holdout()
    
    holdout = np.load("data/realtime_2d/test_set.npz")
    X_test = torch.tensor(holdout['X'], dtype=torch.float32).to(device)
    Y_t = holdout['Y_threat']
    Y_ty = holdout['Y_type']
    Y_j = holdout['Y_jammer']
    
    # 2. Load Production Elite Weights
    model_dir = "models/production_2d_elite"
    if not os.path.exists(os.path.join(model_dir, "backbone.pth")):
        print("[ERROR] Production weights not found. Run 'python train_final_2d.py' first.")
        return

    backbone = SharedBackbone2d().to(device)
    backbone.load_state_dict(torch.load(f"{model_dir}/backbone.pth", map_location=device))
    
    t_h = ThreatHead2d(192).to(device)
    t_h.load_state_dict(torch.load(f"{model_dir}/threat_head.pth", map_location=device))
    
    ty_h = TypeHead2d(192).to(device)
    ty_h.load_state_dict(torch.load(f"{model_dir}/type_head.pth", map_location=device))
    
    j_h = JammerHead2d(192).to(device)
    j_h.load_state_dict(torch.load(f"{model_dir}/jammer_head.pth", map_location=device))
    
    backbone.eval(); t_h.eval(); ty_h.eval(); j_h.eval()
    
    # 3. Execution & Metrics
    start = time.time()
    with torch.no_grad():
        feat = backbone(X_test)
        p_t = (torch.sigmoid(t_h(feat).squeeze()) > 0.5).cpu().numpy()
        p_ty = torch.argmax(ty_h(feat), dim=1).cpu().numpy()
        p_j = (torch.sigmoid(j_h(feat).squeeze()) > 0.5).cpu().numpy()
    latency = (time.time() - start) / len(X_test) * 1000
    
    acc_t = accuracy_score(Y_t, p_t)
    acc_ty = accuracy_score(Y_ty, p_ty)
    acc_j = accuracy_score(Y_j, p_j)
    
    print(f"\n[BENCHMARK RESULTS]")
    print(f"Overall Accuracy: {(acc_t + acc_ty + acc_j)/3.0:.4f}")
    print(f"Threat Detection Acc: {acc_t:.4f}")
    print(f"Type Classification Acc: {acc_ty:.4f}")
    print(f"Jammer Isolation Acc: {acc_j:.4f}")
    print(f"Average Latency: {latency:.4f} ms/sample")
    
    # Report
    with open("BENCHMARK_REPORT_2D.md", "w") as f:
        f.write("# 2D Elite Pipeline Benchmark Report\n\n")
        f.write(f"| Task | Accuracy |\n|---|---|\n")
        f.write(f"| Threat | {acc_t:.4f} |\n")
        f.write(f"| Type | {acc_ty:.4f} |\n")
        f.write(f"| Jammer | {acc_j:.4f} |\n")
        f.write(f"\n**Latency:** {latency:.4f} ms/sample\n")

if __name__ == "__main__":
    benchmark_production_model_2d()
