import torch
import numpy as np
import matplotlib.pyplot as plt
import os
from src.core.backbone_2d import SharedBackbone2d
from src.core.heads_2d import ThreatHead2d, TypeHead2d, JammerHead2d

def visualize_inference(model_dir="models/production_2d", dataset_path="data/production_2d/dataset_2d.npz"):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load Backbone
    backbone = SharedBackbone2d().to(device)
    backbone.load_state_dict(torch.load(f"{model_dir}/threat/backbone.pth", map_location=device))
    backbone.eval()
    
    # Load Heads
    threat_head = ThreatHead2d().to(device)
    threat_head.load_state_dict(torch.load(f"{model_dir}/threat/head.pth", map_location=device))
    threat_head.eval()
    
    type_head = TypeHead2d().to(device)
    type_head.load_state_dict(torch.load(f"{model_dir}/type/head.pth", map_location=device))
    type_head.eval()
    
    # Load Dataset
    data = np.load(dataset_path)
    X = data['X']
    type_y = data['type_y']
    
    classes = ['WiFi', 'DJI', 'Jammer']
    
    plt.figure(figsize=(15, 10))
    for i in range(3):
        idx = np.random.choice(np.where(type_y == i)[0])
        sample = X[idx]
        sample_tensor = torch.tensor(sample).unsqueeze(0).to(device)
        
        with torch.no_grad():
            feats = backbone(sample_tensor)
            threat_score = torch.sigmoid(threat_head(feats)).item()
            type_probs = torch.softmax(type_head(feats), dim=1).cpu().numpy()[0]
            
        plt.subplot(2, 3, i+1)
        plt.imshow(sample[0], aspect='auto', origin='lower', cmap='viridis')
        plt.title(f"Input: {classes[i]}\nThreat Conf: {threat_score:.2f}")
        
        plt.subplot(2, 3, i+4)
        plt.bar(classes, type_probs, color=['blue', 'green', 'red'])
        plt.ylim(0, 1)
        plt.title(f"Class Probabilities")
        
    plt.tight_layout()
    plt.savefig("viz_heads_2d.png")
    print("Inference visualization saved to viz_heads_2d.png")

if __name__ == "__main__":
    if os.path.exists("models/production_2d/threat/backbone.pth"):
        visualize_inference()
    else:
        print("Models not found. Please run train_2d.py first.")
