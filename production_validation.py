import torch
import numpy as np
import os
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
from train_final import OptimizedBackbone, OptimizedHead
from src.core.voting_logic import rtl_voting_logic

def run_production_validation():
    print("==================================================")
    print("   SKYSHIELD v3.0 - PRODUCTION VALIDATION AUDIT   ")
    print("==================================================")
    
    # 1. Load the "Realtime" Holdout Dataset (Ground Truth)
    test_path = "data/realtime/test_set.npz"
    if not os.path.exists(test_path):
        print("Error: Realtime test set not found. Run benchmark_pipeline.py first.")
        return
    
    data = np.load(test_path)
    X = torch.tensor(data['X'], dtype=torch.float32)
    Y_threat_actual = data['Y_threat']
    Y_type_actual = data['Y_type']
    Y_jammer_actual = data['Y_jammer']
    
    # 2. Load Production Model
    backbone = OptimizedBackbone()
    threat_h = OptimizedHead(1)
    type_h = OptimizedHead(3)
    jammer_h = OptimizedHead(1)
    
    backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
    threat_h.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
    type_h.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
    jammer_h.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
    
    backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()
    
    # 3. Perform Inference
    with torch.no_grad():
        feat = backbone(X)
        p_threat = (torch.sigmoid(threat_h(feat).squeeze()) > 0.5).int().numpy()
        p_type = torch.argmax(type_h(feat), dim=1).numpy()
        p_jammer = (torch.sigmoid(jammer_h(feat).squeeze()) > 0.5).int().numpy()
    
    # 4. Map to "Final System Decisions" using Voting Logic
    # Target Decisions:
    # WiFi (Type 0) -> Decision: STANDBY (0)
    # DJI (Type 1)  -> Decision: ALERT_THREAT (1)
    # Jammer (Type 2)-> Decision: ALERT_JAMMING (2)
    
    system_decisions = []
    expected_decisions = []
    
    for i in range(len(X)):
        # Expected based on Ground Truth Type
        actual_type = Y_type_actual[i]
        if actual_type == 0: expected_dec = 0 # WiFi -> Standby
        elif actual_type == 1: expected_dec = 1 # DJI -> Threat
        else: expected_dec = 2 # Jammer -> Jamming
        expected_decisions.append(expected_dec)
        
        # Predicted by System Logic
        action_code, _ = rtl_voting_logic(bool(p_threat[i]), int(p_type[i]), bool(p_jammer[i]))
        system_decisions.append(action_code)
        
    system_decisions = np.array(system_decisions)
    expected_decisions = np.array(expected_decisions)
    
    # 5. Final Audit Metrics
    print("\n--- FINAL SYSTEM DECISION AUDIT ---")
    decision_acc = accuracy_score(expected_decisions, system_decisions)
    print(f"Decision Consistency (AI + Logic vs. Reality): {decision_acc*100:.2f}%")
    
    print("\nDetailed Decision Matrix (Per Class):")
    target_names = ["STANDBY (WiFi)", "ALERT_DRONE (DJI)", "ALERT_JAMMING (Jammer)"]
    print(classification_report(expected_decisions, system_decisions, target_names=target_names))
    
    # 6. Safety Verification
    # Check for False Negatives on Threats (High risk for Defense)
    false_standby = np.where((expected_decisions > 0) & (system_decisions == 0))[0]
    leakage_rate = (len(false_standby) / np.sum(expected_decisions > 0)) * 100
    print(f"Threat Leakage Rate (False Negatives): {leakage_rate:.2f}%")
    
    if leakage_rate < 5.0 and decision_acc > 0.90:
        print("\n[VERIFICATION: PASSED]")
        print("Conclusion: Model decisions are statistically matched to target outcomes.")
    else:
        print("\n[VERIFICATION: FAILED]")
        print("Conclusion: Decision gap detected. Tuning required.")

if __name__ == "__main__":
    run_production_validation()
