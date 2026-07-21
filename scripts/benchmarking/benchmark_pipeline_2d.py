import os
import time
import torch
import torch.nn as nn
import numpy as np
from sklearn.metrics import accuracy_score, classification_report

# Import 2D Architectures
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d
from src.utils.channelizer import apply_channelizer_2d
from src.data_pipeline.generator_2d import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def generate_realtime_holdout_2d():
    print("\n--- Generating 2D Real-Time Holdout Set ---")
    np.random.seed(42)
    n_samples = 100 
    
    X_2d, y_t, y_ty, y_j = [], [], [], []
    
    for _ in range(n_samples):
        snr = np.random.uniform(-10, 15)
        # WiFi
        X_2d.append(apply_channelizer_2d(generate_wifi_dsss(snr)))
        y_t.append(0); y_ty.append(0); y_j.append(0)
        # DJI
        X_2d.append(apply_channelizer_2d(generate_dji_pulse(snr)))
        y_t.append(1); y_ty.append(1); y_j.append(0)
        # Jammer
        X_2d.append(apply_channelizer_2d(generate_jammer(snr)))
        y_t.append(1); y_ty.append(2); y_j.append(1)
        
    X_2d = np.array(X_2d).astype(np.float32)
    os.makedirs("data/realtime_2d", exist_ok=True)
    np.savez("data/realtime_2d/test_set.npz", 
             X=X_2d, Y_threat=np.array(y_t), Y_type=np.array(y_ty), Y_jammer=np.array(y_j))
    print("Holdout set generated.")

def benchmark_production_model():
    print("\n--- Benchmarking Production 2D Echelon (Best Available) ---")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    if not os.path.exists("data/realtime_2d/test_set.npz"):
        generate_realtime_holdout_2d()
    
    holdout = np.load("data/realtime_2d/test_set.npz")
    X_test = torch.tensor(holdout['X']).to(device)
    
    model_dir = "models/production_2d_elite"
    backbone = SharedBackbone2d().to(device)
    backbone.load_state_dict(torch.load(f"{model_dir}/backbone.pth", map_location=device, weights_only=True))
    
    t_h = ThreatHead2d(256).to(device)
    t_h.load_state_dict(torch.load(f"{model_dir}/threat_head.pth", map_location=device, weights_only=True))
    
    ty_h = TypeHead2d(256).to(device)
    ty_h.load_state_dict(torch.load(f"{model_dir}/type_head.pth", map_location=device, weights_only=True))
    
    j_h = JammerHead2d(256).to(device)
    j_h.load_state_dict(torch.load(f"{model_dir}/jammer_head.pth", map_location=device, weights_only=True))
    
    backbone.eval(); t_h.eval(); ty_h.eval(); j_h.eval()
    
    start = time.time()
    with torch.no_grad():
        feat = backbone(X_test)
        p_t = (torch.sigmoid(t_h(feat).squeeze()) > 0.5).cpu().numpy()
        p_ty = torch.argmax(ty_h(feat), dim=1).cpu().numpy()
        p_j = (torch.sigmoid(j_h(feat).squeeze()) > 0.5).cpu().numpy()
    latency = (time.time() - start) / len(X_test) * 1000
    
    print("\n[ACCURACY METRICS]")
    print(classification_report(holdout['Y_type'], p_ty, target_names=["WiFi", "DJI", "Jammer"]))
    
    acc_t = accuracy_score(holdout['Y_threat'], p_t)
    acc_ty = accuracy_score(holdout['Y_type'], p_ty)
    acc_j = accuracy_score(holdout['Y_jammer'], p_j)
    
    print(f"Threat Detection Accuracy: {acc_t:.4f}")
    print(f"Type Classification Accuracy: {acc_ty:.4f}")
    print(f"Jammer Isolation Accuracy: {acc_j:.4f}")
    print(f"Inference Latency: {latency:.4f} ms/sample")
    
    with open("BENCHMARK_REPORT_2D.md", "w") as f:
        f.write("# Final Production 2D Benchmark Report\n\n")
        f.write(f"| Task | Accuracy |\n|---|---|\n")
        f.write(f"| Threat | {acc_t:.4f} |\n")
        f.write(f"| Type | {acc_ty:.4f} |\n")
        f.write(f"| Jammer | {acc_j:.4f} |\n")
        f.write(f"\n**Latency:** {latency:.4f} ms/sample\n")

if __name__ == "__main__":
    benchmark_production_model()
