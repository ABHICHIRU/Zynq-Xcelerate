import torch
import numpy as np
import time
from train_final import OptimizedBackbone, OptimizedHead
from src.core.voting_logic import rtl_voting_logic
from src.data_pipeline.generator import generate_wifi_dsss, generate_dji_pulse, generate_jammer

def load_production_pipeline():
    backbone = OptimizedBackbone()
    threat_h = OptimizedHead(1)
    type_h = OptimizedHead(3)
    jammer_h = OptimizedHead(1)
    
    backbone.load_state_dict(torch.load("models/final_production/backbone.pth", weights_only=True))
    threat_h.load_state_dict(torch.load("models/final_production/threat_head.pth", weights_only=True))
    type_h.load_state_dict(torch.load("models/final_production/type_head.pth", weights_only=True))
    jammer_h.load_state_dict(torch.load("models/final_production/jammer_head.pth", weights_only=True))
    
    backbone.eval(); threat_h.eval(); type_h.eval(); jammer_h.eval()
    return backbone, threat_h, type_h, jammer_h

def run_realtime_stream_check(n_iterations=15):
    print("--- SKYSHIELD v3.0: LIVE STREAM PIPELINE AUDIT ---")
    models = load_production_pipeline()
    backbone, threat_h, type_h, jammer_h = models
    
    success_count = 0
    
    print(f"{'ITER':<5} | {'INTENDED CLASS':<15} | {'SYSTEM DECISION':<20} | {'RESULT'}")
    print("-" * 60)
    
    for i in range(n_iterations):
        # 1. Simulate Live Signal Intercept (Random Physics)
        target_id = np.random.randint(0, 3)
        snr = np.random.uniform(0, 15) # Testing in clear-ish conditions
        
        if target_id == 0:
            iq_sample = generate_wifi_dsss(snr)
            label = "WiFi"
            expected_action = 0 # STANDBY
        elif target_id == 1:
            iq_sample = generate_dji_pulse(snr)
            label = "DJI Drone"
            expected_action = 1 # ALERT_THREAT
        else:
            iq_sample = generate_jammer(snr)
            label = "Jammer"
            expected_action = 2 # ALERT_JAMMING
            
        # 2. Real-Time Inference (Single Sample Batching)
        x = torch.tensor(iq_sample, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            feat = backbone(x)
            p_threat = (torch.sigmoid(threat_h(feat).squeeze()) > 0.5).item()
            p_type = torch.argmax(type_h(feat), dim=1).item()
            p_jammer = (torch.sigmoid(jammer_h(feat).squeeze()) > 0.5).item()
            
        # 3. Deterministic Decision Logic
        action_code, status = rtl_voting_logic(p_threat, p_type, p_jammer)
        
        # 4. Verification
        decision_map = {0: "STANDBY", 1: "ALERT_DRONE", 2: "ALERT_JAMMING"}
        result = "PASS" if action_code == expected_action else "FAIL"
        if result == "PASS": success_count += 1
        
        print(f"{i+1:<5} | {label:<15} | {decision_map[action_code]:<20} | {result}")
        time.sleep(0.1) # Simulate hardware processing delay

    final_score = (success_count / n_iterations) * 100
    print("-" * 60)
    print(f"PIPELINE AUDIT COMPLETE. Accuracy: {final_score:.1f}%")
    
    if final_score >= 90:
        print("[STATUS: SYSTEM PRODUCTION READY]")
    else:
        print("[STATUS: PIPELINE DRIFT DETECTED - RE-CALIBRATE]")

if __name__ == "__main__":
    run_realtime_stream_check()
