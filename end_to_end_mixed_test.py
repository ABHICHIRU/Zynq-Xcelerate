import numpy as np
import torch
import time
import os
from src.utils.channelizer import apply_channelizer_2d
from src.data_pipeline.generator_2d import generate_wifi_dsss, generate_dji_pulse, generate_jammer
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d
from src.core.voting_logic import rtl_voting_logic

def test_mixed_signal_pipeline():
    print("\n" + "="*80)
    print("ULTIMATE END-TO-END MIXED SIGNAL STRESS TEST")
    print("="*80)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_dir = "models/production_2d_elite"
    
    # 1. Initialize Pipeline Components
    backbone = SharedBackbone2d().to(device)
    backbone.load_state_dict(torch.load(f"{model_dir}/backbone.pth", map_location=device, weights_only=True))
    
    t_h = ThreatHead2d(256).to(device)
    t_h.load_state_dict(torch.load(f"{model_dir}/threat_head.pth", map_location=device, weights_only=True))
    
    ty_h = TypeHead2d(256).to(device)
    ty_h.load_state_dict(torch.load(f"{model_dir}/type_head.pth", map_location=device, weights_only=True))
    
    j_h = JammerHead2d(256).to(device)
    j_h.load_state_dict(torch.load(f"{model_dir}/jammer_head.pth", map_location=device, weights_only=True))
    
    backbone.eval(); t_h.eval(); ty_h.eval(); j_h.eval()

    # 2. Create Mixed Signals
    print("\n[STEP 1] Generating Complex Mixed Signals...")
    np.random.seed(777)
    snr = 10
    
    # Scenario A: WiFi + Low-level Jammer (Hidden Threat)
    wifi = generate_wifi_dsss(snr)
    jammer_noise = generate_jammer(snr - 12) * 0.2
    mixed_a = wifi + jammer_noise
    
    # Scenario B: DJI Drone + Pulsed Interference
    dji = generate_dji_pulse(snr)
    interference = generate_jammer(snr - 5) * 0.5
    mixed_b = dji + interference

    test_cases = [
        ("WiFi + Hidden Jammer", mixed_a, "Jammer"),
        ("DJI + Interference", mixed_b, "DJI Drone")
    ]

    type_map = {0: "WiFi", 1: "DJI Drone", 2: "Jammer"}

    for name, signal, expected in test_cases:
        print(f"\n--- Testing Case: {name} ---")
        
        # 3. Preprocessing (1D -> 2D)
        start_pre = time.time()
        x_2d = apply_channelizer_2d(signal)
        input_tensor = torch.tensor(x_2d).unsqueeze(0).to(device)
        pre_time = (time.time() - start_pre) * 1000
        
        # 4. Inference
        start_inf = time.time()
        with torch.no_grad():
            feat = backbone(input_tensor)
            t_score = torch.sigmoid(t_h(feat)).item()
            ty_probs = torch.softmax(ty_h(feat), dim=1).cpu().numpy()[0]
            j_score = torch.sigmoid(j_h(feat)).item()
            
            t_p = t_score > 0.5
            ty_p = np.argmax(ty_probs)
            j_p = j_score > 0.5
        inf_time = (time.time() - start_inf) * 1000
        
        # 5. RTL Voting Decision
        action_code, status = rtl_voting_logic(t_p, ty_p, j_p)
        
        print(f"Preprocess Time: {pre_time:.2f}ms")
        print(f"Inference Time:  {inf_time:.2f}ms")
        print(f"Model Output:    Threat={t_p} ({t_score:.2f}), Type={type_map[ty_p]} ({ty_probs[ty_p]:.2f}), Jammer={j_p} ({j_score:.2f})")
        print(f"FINAL DECISION:  {status} (Code: {action_code})")
        
        # 6. Verification
        if type_map[ty_p] == expected or (expected == "Jammer" and j_p):
            print("VERDICT: SUCCESS - Correct Identification under noise.")
        else:
            print(f"VERDICT: FAILURE - Expected {expected}, got {type_map[ty_p]}")

if __name__ == "__main__":
    test_mixed_signal_pipeline()
