import torch
import numpy as np
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.core.voting_logic import rtl_voting_logic

def load_models():
    """Loads the trained models from the models/ directory."""
    backbone = SharedBackbone()
    threat_head = ThreatHead()
    type_head = TypeHead()
    jammer_head = JammerHead()

    try:
        backbone.load_state_dict(torch.load("models/backbone.pth", weights_only=True))
        threat_head.load_state_dict(torch.load("models/threat_head.pth", weights_only=True))
        type_head.load_state_dict(torch.load("models/type_head.pth", weights_only=True))
        jammer_head.load_state_dict(torch.load("models/jammer_head.pth", weights_only=True))
    except Exception as e:
        print(f"Error loading models. Have you run main.py? {e}")
        exit(1)

    backbone.eval()
    threat_head.eval()
    type_head.eval()
    jammer_head.eval()
    
    return backbone, threat_head, type_head, jammer_head

def predict_signal(iq_sample, models):
    """Runs a single I/Q sample through the inference pipeline."""
    backbone, threat_head, type_head, jammer_head = models
    
    # Add batch dimension: (2, 512) -> (1, 2, 512)
    x_tensor = torch.tensor(iq_sample, dtype=torch.float32).unsqueeze(0)
    
    with torch.no_grad():
        features = backbone(x_tensor)
        
        # Threat: Binary (0=Benign, 1=Threat)
        threat_logit = threat_head(features).squeeze()
        threat_pred = torch.sigmoid(threat_logit).item() > 0.5
        
        # Type: Multiclass (0=WiFi, 1=DJI, 2=Jammer)
        type_logits = type_head(features)
        type_pred = torch.argmax(type_logits, dim=1).item()
        
        # Jammer: Binary (0=Clear, 1=Jamming)
        jammer_logit = jammer_head(features).squeeze()
        jammer_pred = torch.sigmoid(jammer_logit).item() > 0.5
        
    return threat_pred, type_pred, jammer_pred

def run_judge_verification():
    """
    Simulates a live test for the Hackathon Judges.
    Takes 3 unknown signals, feeds them to the models, applies Voting Logic,
    and prints the system's final deterministic response.
    """
    print("==================================================")
    print("      SKYSHIELD v3.0 - JUDGE VERIFICATION DEMO    ")
    print("==================================================")
    print("Loading INT8-ready trained models from Flash...")
    models = load_models()
    
    # Load datasets to fetch some "live" samples
    data = np.load("data/threat_dataset.npz")
    X = data['X']
    
    # Indices based on our dataset generator:
    # 0-999: WiFi, 1000-1999: DJI, 2000-2999: Jammer
    scenarios = [
        {"name": "Benign User (802.11b DSSS)", "idx": np.random.randint(0, 1000), "true_class": "WiFi"},
        {"name": "Drone Intrusion (Pulse Edge)", "idx": np.random.randint(1000, 2000), "true_class": "DJI Drone"},
        {"name": "Electronic Warfare (Wiener Noise)", "idx": np.random.randint(2000, 3000), "true_class": "Jammer"}
    ]
    
    for i, scenario in enumerate(scenarios):
        print(f"\n[Test Case {i+1}] Processing Intercepted Signal...")
        print(f"-> True Identity: {scenario['true_class']} (Unknown to System)")
        
        iq_sample = X[scenario["idx"]]
        
        # 1. Neural Network Inference
        threat_pred, type_pred, jammer_pred = predict_signal(iq_sample, models)
        
        type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}
        print("-> Neural Network Raw Outputs:")
        print(f"     Head A (Threat) : {threat_pred}")
        print(f"     Head B (Type)   : {type_map[type_pred]} ({type_pred})")
        print(f"     Head C (Jammer) : {jammer_pred}")
        
        # 2. RTL Deterministic Voting Logic (Hardware Gate)
        action_code, status_msg = rtl_voting_logic(threat_pred, type_pred, jammer_pred)
        
        print("-> RTL Voting Logic Decision:")
        if action_code == 0:
            print(f"     [GREEN] {status_msg}")
        elif action_code == 1:
            print(f"     [YELLOW] {status_msg}")
        elif action_code == 2:
            print(f"     [RED] {status_msg}")
            
    print("\n==================================================")
    print("                  DEMO COMPLETE                   ")
    print("==================================================")

if __name__ == "__main__":
    run_judge_verification()
