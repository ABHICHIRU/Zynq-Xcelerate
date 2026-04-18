import torch
import numpy as np
import time
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.core.voting_logic import rtl_voting_logic
from src.data_pipeline.generator import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def load_production_pipeline():
    backbone = SharedBackbone()
    threat_h = ThreatHead(64)
    type_h = TypeHead(64)
    jammer_h = JammerHead(64)
    
    backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
    threat_h.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
    type_h.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
    jammer_h.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
    
    backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()
    return backbone, threat_h, type_h, jammer_h

def run_stress_test(n_iterations=20):
    print("--- SKYSHIELD v3.5: STRESS TEST AUDIT (Residual-Lite) ---")
    print("Conditions: Harsh Noise (-15dB to -5dB) + Random Time Shifts")
    print("-" * 75)
    
    models = load_production_pipeline()
    backbone, threat_h, type_h, jammer_h = models
    
    success_count = 0
    
    print(f"{'ITER':<5} | {'CLASS':<12} | {'SNR':<7} | {'DECISION':<18} | {'RESULT'}")
    print("-" * 75)
    
    for i in range(n_iterations):
        target_id = np.random.randint(0, 3)
        snr = np.random.uniform(-15, -5)
        
        if target_id == 0:
            iq_sample = generate_wifi_dsss(snr)
            expected_action = 0; label = "WiFi"
        elif target_id == 1:
            iq_sample = generate_dji_pulse(snr)
            expected_action = 1; label = "DJI Drone"
        else:
            iq_sample = generate_jammer(snr)
            expected_action = 2; label = "Jammer"
            
        iq_sample = np.roll(iq_sample, np.random.randint(-100, 100), axis=-1)
            
        x = torch.tensor(iq_sample, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            feat = backbone(x)
            p_threat = (torch.sigmoid(threat_h(feat).squeeze()) > 0.5).item()
            p_type = torch.argmax(type_h(feat), dim=1).item()
            p_jammer = (torch.sigmoid(jammer_h(feat).squeeze()) > 0.5).item()
            
        action_code, _ = rtl_voting_logic(p_threat, p_type, p_jammer)
        decision_map = {0: "STANDBY", 1: "ALERT_DRONE", 2: "ALERT_JAMMING"}
        result = "PASS" if action_code == expected_action else "FAIL"
        if result == "PASS": success_count += 1
        print(f"{i+1:<5} | {label:<12} | {snr:<7.1f} | {decision_map[action_code]:<18} | {result}")

    final_score = (success_count / n_iterations) * 100
    print("-" * 75)
    print(f"STRESS TEST COMPLETE. Robustness Score: {final_score:.1f}%")

if __name__ == "__main__":
    run_stress_test()
