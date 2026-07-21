import torch
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import os
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d
from src.utils.channelizer import apply_channelizer_2d

def evaluate_2d_on_realtime(model_dir="models/production_2d", test_path="data/realtime/test_set.npz"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluating 2D Models on Real-Time 1D Data (Device: {device})")
    print("-" * 50)
    
    # 1. Load Data
    data = np.load(test_path)
    X_1d = data['X'] # (1500, 2, 512)
    Y_threat = data['Y_threat']
    Y_type = data['Y_type']
    Y_jammer = data['Y_jammer']
    
    # 2. Bridge 1D to 2D (Channelizer)
    print("Converting 1D Real-Time Data to 2D Spectrograms...")
    X_2d = []
    for i in range(len(X_1d)):
        # Convert 1D (2, 512) to complex
        iq_complex = X_1d[i, 0] + 1j * X_1d[i, 1]
        X_2d.append(apply_channelizer_2d(iq_complex))
    X_2d = np.array(X_2d) # (1500, 2, 64, 64)
    print(f"Conversion Complete: {X_2d.shape}")
    
    # 3. Load 2D Models
    backbone = SharedBackbone2d().to(device)
    backbone.load_state_dict(torch.load(f"{model_dir}/threat/backbone.pth", map_location=device))
    backbone.eval()
    
    threat_head = ThreatHead2d().to(device)
    threat_head.load_state_dict(torch.load(f"{model_dir}/threat/head.pth", map_location=device))
    threat_head.eval()
    
    type_head = TypeHead2d().to(device)
    type_head.load_state_dict(torch.load(f"{model_dir}/type/head.pth", map_location=device))
    type_head.eval()
    
    jammer_head = JammerHead2d().to(device)
    jammer_head.load_state_dict(torch.load(f"{model_dir}/jammer/head.pth", map_location=device))
    jammer_head.eval()
    
    # 4. Inference
    batch_size = 64
    preds_threat, preds_type, preds_jammer = [], [], []
    
    with torch.no_grad():
        for i in range(0, len(X_2d), batch_size):
            batch_x = torch.tensor(X_2d[i : i+batch_size]).to(device)
            feats = backbone(batch_x)
            
            p_threat = (torch.sigmoid(threat_head(feats)) > 0.5).float().cpu().numpy()
            p_type = torch.argmax(type_head(feats), dim=1).cpu().numpy()
            p_jammer = (torch.sigmoid(jammer_head(feats)) > 0.5).float().cpu().numpy()
            
            preds_threat.extend(p_threat)
            preds_type.extend(p_type)
            preds_jammer.extend(p_jammer)
            
    # 5. RUTHLESS Analysis
    print("\n[RUTHLESS ANALYSIS: THREAT DETECTION]")
    print(classification_report(Y_threat, preds_threat, target_names=["Clear (WiFi)", "Threat (DJI/Jammer)"]))
    
    print("\n[RUTHLESS ANALYSIS: TYPE CLASSIFICATION]")
    print(classification_report(Y_type, preds_type, target_names=["WiFi", "DJI", "Jammer"]))
    
    print("\n[RUTHLESS ANALYSIS: JAMMER ISOLATION]")
    print(classification_report(Y_jammer, preds_jammer, target_names=["No Jammer", "Jammer Detected"]))
    
    # 6. Overfitting / Underperformance Check
    # Load training metrics for comparison
    # (In a real scenario, we'd compare training accuracy vs these results)
    # If training was ~99% and this is ~70%, it's OVERFITTING.
    # If both are low, it's UNDERPERFORMING.
    
    print("-" * 50)
    print("Final Verdict:")
    threat_acc = accuracy_score(Y_threat, preds_threat)
    type_acc = accuracy_score(Y_type, preds_type)
    
    if threat_acc < 0.85 or type_acc < 0.85:
        print("VERDICT: CRITICAL UNDERPERFORMANCE OR GENERALIZATION FAILURE.")
        print("The 2D model fails to generalize to real-time 1D distributions.")
    elif threat_acc > 0.98 and type_acc > 0.98:
        print("VERDICT: POTENTIAL OVERFITTING ON SYNTHETIC MANIFOLDS.")
        print("If training loss was near zero, the model might be memorizing synthetic signatures.")
    else:
        print("VERDICT: BALANCED PRODUCTION PERFORMANCE.")
        print("Model demonstrates robustness on the real-time evaluation set.")

if __name__ == "__main__":
    evaluate_2d_on_realtime()
