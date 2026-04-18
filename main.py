import os
import torch
from src.data_pipeline.generator import save_datasets
from src.core.backbone import SharedBackbone
from src.core.heads import ThreatHead, TypeHead, JammerHead
from src.training.train_pipeline import train_joint_model

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

    # 3. Joint Training (Multi-Task Learning for Max Efficiency and Accuracy)
    print("\nTraining Heads Jointly (Gradient Shared)...")
    train_joint_model(backbone, threat_head, type_head, jammer_head, num_epochs=15)

    # 4. Save Weights
    print("Saving models to models/ directory...")
    os.makedirs("models", exist_ok=True)
    torch.save(backbone.state_dict(), "models/backbone.pth")
    torch.save(threat_head.state_dict(), "models/threat_head.pth")
    torch.save(type_head.state_dict(), "models/type_head.pth")
    torch.save(jammer_head.state_dict(), "models/jammer_head.pth")

    print("SkyShield v3.0 Pipeline Complete.")

if __name__ == "__main__":
    main()
