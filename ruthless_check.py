import numpy as np
import torch
from sklearn.metrics import confusion_matrix, classification_report
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d

def ruthless_verification():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data = np.load("data/realtime_2d/test_set.npz")
    X = torch.tensor(data['X']).to(device)
    
    # Target Labels
    Y_threat = data['Y_threat']
    Y_jammer = data['Y_jammer']
    Y_type = data['Y_type']
    
    # Load Models
    model_dir = "models/production_2d_elite"
    backbone = SharedBackbone2d().to(device)
    backbone.load_state_dict(torch.load(f"{model_dir}/backbone.pth", map_location=device, weights_only=True))
    
    t_h = ThreatHead2d(256).to(device)
    t_h.load_state_dict(torch.load(f"{model_dir}/threat_head.pth", map_location=device, weights_only=True))
    
    j_h = JammerHead2d(256).to(device)
    j_h.load_state_dict(torch.load(f"{model_dir}/jammer_head.pth", map_location=device, weights_only=True))
    
    ty_h = TypeHead2d(256).to(device)
    ty_h.load_state_dict(torch.load(f"{model_dir}/type_head.pth", map_location=device, weights_only=True))
    
    backbone.eval(); t_h.eval(); j_h.eval(); ty_h.eval()
    
    with torch.no_grad():
        feat = backbone(X)
        pred_t = (torch.sigmoid(t_h(feat).squeeze()) > 0.5).cpu().numpy()
        pred_j = (torch.sigmoid(j_h(feat).squeeze()) > 0.5).cpu().numpy()
        pred_ty = torch.argmax(ty_h(feat), dim=1).cpu().numpy()
        
    print("\n" + "="*50)
    print("RUTHLESS POSITIVE/NEGATIVE VERIFICATION")
    print("="*50)
    
    print("\n[THREAT DETECTION CONFUSION MATRIX]")
    # TN, FP, FN, TP
    cm_t = confusion_matrix(Y_threat, pred_t)
    print(f"True Negatives (WiFi): {cm_t[0,0]}")
    print(f"False Positives (WiFi as Threat): {cm_t[0,1]}")
    print(f"False Negatives (Threat missed): {cm_t[1,0]}")
    print(f"True Positives (Drone/Jammer found): {cm_t[1,1]}")
    
    print("\n[JAMMER ISOLATION CONFUSION MATRIX]")
    cm_j = confusion_matrix(Y_jammer, pred_j)
    print(f"True Negatives (WiFi/Drone): {cm_j[0,0]}")
    print(f"False Positives (WiFi/Drone as Jammer): {cm_j[0,1]}")
    print(f"False Negatives (Jammer missed): {cm_j[1,0]}")
    print(f"True Positives (Jammer found): {cm_j[1,1]}")
    
    print("\n[MULTI-CLASS CLASSIFICATION REPORT]")
    print(classification_report(Y_type, pred_ty, target_names=["WiFi (Neg)", "DJI (Pos)", "Jammer (Pos)"]))
    
if __name__ == "__main__":
    ruthless_verification()
