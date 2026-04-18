import os
import torch
from src.data_pipeline.generator import save_datasets
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.training.train_pipeline import train_head

def main():
    print("--- SkyShield v3.0: FPGA RF Defense System ---")
    
    # 1. Dataset Generation
    if not os.path.exists("data/threat_dataset.npz"):
        print("Generating datasets...")
        save_datasets("data")
    else:
        print("Datasets already exist in data/")

    # 2. Model Initialization
    print("Initializing models...")
    backbone = SharedBackbone()
    threat_head = ThreatHead()
    type_head = TypeHead()
    jammer_head = JammerHead()

    # 3. Training Heads (Gradient Isolation)
    # Head A: Threat
    print("\nTraining Head A: THREAT (Binary)...")
    train_head(backbone, threat_head, "data/threat_dataset.npz")

    # Head B: Type
    print("\nTraining Head B: TYPE (Multi-class)...")
    train_head(backbone, type_head, "data/type_dataset.npz", is_multiclass=True)

    # Head C: Jammer
    print("\nTraining Head C: JAMMER (Binary)...")
    train_head(backbone, jammer_head, "data/jammer_dataset.npz")

    # 4. Save Weights
    print("\nSaving models to weights/ directory...")
    os.makedirs("models", exist_ok=True)
    torch.save(backbone.state_dict(), "models/backbone.pth")
    torch.save(threat_head.state_dict(), "models/threat_head.pth")
    torch.save(type_head.state_dict(), "models/type_head.pth")
    torch.save(jammer_head.state_dict(), "models/jammer_head.pth")

    print("\nSkyShield v3.0 Pipeline Complete.")

if __name__ == "__main__":
    main()
