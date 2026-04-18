import os
import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
import pandas as pd

# Import Architectures (Copied from benchmark_pipeline.py for completeness)
from src.core.backbone import SharedBackbone as BackboneV1
from src.core.heads import ThreatHead as ThreatHeadV1, TypeHead as TypeHeadV1, JammerHead as JammerHeadV1
import torch.nn as nn

class BackboneV2(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(2, 32, kernel_size=7, stride=2, padding=3)
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(32, 64, kernel_size=5, stride=2, padding=2)
        self.relu2 = nn.ReLU()
        self.conv3 = nn.Conv1d(64, 128, kernel_size=3, stride=2, padding=1)
        self.relu3 = nn.ReLU()
        self.gap = nn.AdaptiveAvgPool1d(1)
    def forward(self, x):
        x = self.relu1(self.conv1(x)); x = self.relu2(self.conv2(x)); x = self.relu3(self.conv3(x)); x = self.gap(x)
        return x.view(x.size(0), -1)

class HeadV2(nn.Module):
    def __init__(self, input_dim=128, out_classes=1):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(input_dim, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, out_classes))
    def forward(self, x): return self.fc(x)

class BackboneV3(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv1d(2, 8, kernel_size=5, stride=4, padding=2); self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(8, 16, kernel_size=3, stride=2, padding=1); self.relu2 = nn.ReLU()
        self.gap = nn.AdaptiveAvgPool1d(1)
    def forward(self, x):
        x = self.relu1(self.conv1(x)); x = self.relu2(self.conv2(x)); x = self.gap(x)
        return x.view(x.size(0), -1)

class HeadV3(nn.Module):
    def __init__(self, input_dim=16, out_classes=1):
        super().__init__()
        self.fc = nn.Sequential(nn.Linear(input_dim, out_classes))
    def forward(self, x): return self.fc(x)

def load_model_variant(name):
    if name == "v1_baseline":
        b, t, y, j = BackboneV1(), ThreatHeadV1(), TypeHeadV1(), JammerHeadV1()
    elif name == "v2_wider":
        b, t, y, j = BackboneV2(), HeadV2(128, 1), HeadV2(128, 3), HeadV2(128, 1)
    elif name == "v3_lightweight":
        b, t, y, j = BackboneV3(), HeadV3(16, 1), HeadV3(16, 3), HeadV3(16, 1)
    
    b.load_state_dict(torch.load(f"models/{name}/backbone.pth", weights_only=True))
    t.load_state_dict(torch.load(f"models/{name}/threat_head.pth", weights_only=True))
    y.load_state_dict(torch.load(f"models/{name}/type_head.pth", weights_only=True))
    j.load_state_dict(torch.load(f"models/{name}/jammer_head.pth", weights_only=True))
    return b.eval(), t.eval(), y.eval(), j.eval()

def plot_confusion_matrix(y_true, y_pred, labels, title, filename):
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=labels, yticklabels=labels)
    plt.title(title)
    plt.ylabel('True label')
    plt.xlabel('Predicted label')
    plt.savefig(filename)
    plt.close()

def run_visualization():
    data = np.load("data/realtime/test_set.npz")
    X = torch.tensor(data['X'], dtype=torch.float32)
    Y_threat = data['Y_threat']
    Y_type = data['Y_type']
    Y_jammer = data['Y_jammer']
    
    variants = ["v1_baseline", "v2_wider", "v3_lightweight"]
    log_file = "DETAILED_METRICS.log"
    
    with open(log_file, "w") as f:
        f.write("=== SKYSHIELD v3.0 DETAILED CLASSIFICATION LOGS ===\n\n")
        
        for name in variants:
            f.write(f"\n--- Model Variant: {name} ---\n")
            b, t, y, j = load_model_variant(name)
            
            with torch.no_grad():
                features = b(X)
                p_threat = (torch.sigmoid(t(features).squeeze()) > 0.5).numpy()
                p_type = torch.argmax(y(features), dim=1).numpy()
                p_jammer = (torch.sigmoid(j(features).squeeze()) > 0.5).numpy()
            
            # Save Confusion Matrices
            os.makedirs(f"viz_metrics/{name}", exist_ok=True)
            plot_confusion_matrix(Y_threat, p_threat, ["Benign", "Threat"], f"{name} - Threat CM", f"viz_metrics/{name}/threat_cm.png")
            plot_confusion_matrix(Y_type, p_type, ["WiFi", "DJI", "Jammer"], f"{name} - Type CM", f"viz_metrics/{name}/type_cm.png")
            plot_confusion_matrix(Y_jammer, p_jammer, ["Clear", "Jammer"], f"{name} - Jammer CM", f"viz_metrics/{name}/jammer_cm.png")
            
            # Write classification reports
            f.write("\nTHREAT HEAD REPORT:\n")
            f.write(classification_report(Y_threat, p_threat, target_names=["Benign", "Threat"]))
            f.write("\nTYPE HEAD REPORT:\n")
            f.write(classification_report(Y_type, p_type, target_names=["WiFi", "DJI", "Jammer"]))
            f.write("\nJAMMER HEAD REPORT:\n")
            f.write(classification_report(Y_jammer, p_jammer, target_names=["Clear", "Jammer"]))
            f.write("-" * 50 + "\n")

    print(f"Detailed metrics and visualizations generated in viz_metrics/ and {log_file}")

if __name__ == "__main__":
    run_visualization()
