import torch
import numpy as np
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.core.voting_logic import rtl_voting_logic

def load_models():
    """Loads the trained SkyShield v3.5 Residual models."""
    backbone = SharedBackbone()
    threat_head = ThreatHead(in_features=64)
    type_head = TypeHead(in_features=64)
    jammer_head = JammerHead(in_features=64)

    try:
        backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
        threat_head.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
        type_head.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
        jammer_head.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
    except Exception as e:
        print(f"Error loading v3.5 models: {e}")
        exit(1)

    backbone.eval(); threat_head.eval(); type_head.eval(); jammer_head.eval()
    return backbone, threat_head, type_head, jammer_head

def predict_signal(iq_sample, models):
    backbone, threat_head, type_head, jammer_head = models
    x_tensor = torch.tensor(iq_sample, dtype=torch.float32).unsqueeze(0)
    
    with torch.no_grad():
        features = backbone(x_tensor)
        threat_logit = threat_head(features).squeeze()
        threat_pred = torch.sigmoid(threat_logit).item() > 0.5
        type_logits = type_head(features)
        type_pred = torch.argmax(type_logits, dim=1).item()
        jammer_logit = jammer_head(features).squeeze()
        jammer_pred = torch.sigmoid(jammer_logit).item() > 0.5
        
    return threat_pred, type_pred, jammer_pred

def run_judge_verification():
    print("==================================================")
    print("   SKYSHIELD v3.5 - RESIDUAL PRODUCTION DEMO     ")
    print("==================================================")
    models = load_models()
    data = np.load("data/threat_dataset.npz")
    X = data['X']
    
    scenarios = [
        {"name": "WiFi User", "idx": np.random.randint(0, 1000), "true_class": "WiFi"},
        {"name": "Drone Pulse", "idx": np.random.randint(1000, 2000), "true_class": "DJI Drone"},
        {"name": "Wiener Jammer", "idx": np.random.randint(2000, 3000), "true_class": "Jammer"}
    ]
    
    for i, scenario in enumerate(scenarios):
        print(f"\n[Test Case {i+1}] Processing Intercepted Signal...")
        iq_sample = X[scenario["idx"]]
        threat_pred, type_pred, jammer_pred = predict_signal(iq_sample, models)
        action_code, status_msg = rtl_voting_logic(threat_pred, type_pred, jammer_pred)
        
        print(f"-> Predicted: {['WiFi','DJI','Jammer'][type_pred]} | Ground Truth: {scenario['true_class']}")
        print(f"-> RTL DECISION: {status_msg}")
            
    print("\n==================================================")

if __name__ == "__main__":
    run_judge_verification()
