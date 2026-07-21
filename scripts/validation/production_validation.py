import torch
import numpy as np
import os
from sklearn.metrics import classification_report, accuracy_score
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.core.voting_logic import rtl_voting_logic

def run_production_validation():
    print("==================================================")
    print("   SKYSHIELD v3.5 - RESIDUAL VALIDATION AUDIT    ")
    print("==================================================")
    
    test_path = "data/realtime/test_set.npz"
    if not os.path.exists(test_path):
        print("Error: Realtime test set not found.")
        return
    
    data = np.load(test_path)
    X = torch.tensor(data['X'], dtype=torch.float32)
    Y_type_actual = data['Y_type']
    
    backbone = SharedBackbone()
    threat_h = ThreatHead(64)
    type_h = TypeHead(64)
    jammer_h = JammerHead(64)
    
    backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
    threat_h.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
    type_h.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
    jammer_h.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
    
    backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()
    
    with torch.no_grad():
        feat = backbone(X)
        p_threat = (torch.sigmoid(threat_h(feat).squeeze()) > 0.5).int().numpy()
        p_type = torch.argmax(type_h(feat), dim=1).numpy()
        p_jammer = (torch.sigmoid(jammer_h(feat).squeeze()) > 0.5).int().numpy()
    
    system_decisions = []
    expected_decisions = []
    
    for i in range(len(X)):
        actual_type = Y_type_actual[i]
        expected_dec = 0 if actual_type == 0 else (1 if actual_type == 1 else 2)
        expected_decisions.append(expected_dec)
        action_code, _ = rtl_voting_logic(bool(p_threat[i]), int(p_type[i]), bool(p_jammer[i]))
        system_decisions.append(action_code)
        
    system_decisions = np.array(system_decisions)
    expected_decisions = np.array(expected_decisions)
    
    print("\n--- RESIDUAL v3.5 SYSTEM DECISION AUDIT ---")
    decision_acc = accuracy_score(expected_decisions, system_decisions)
    print(f"Decision Consistency (AI + Logic vs. Reality): {decision_acc*100:.2f}%")
    
    target_names = ["STANDBY (WiFi)", "ALERT_DRONE (DJI)", "ALERT_JAMMING (Jammer)"]
    print(classification_report(expected_decisions, system_decisions, target_names=target_names))
    
    if decision_acc > 0.93:
        print("\n[VERIFICATION: PASSED (Residual v3.5)]")
    else:
        print("\n[VERIFICATION: FAILED]")

if __name__ == "__main__":
    run_production_validation()
