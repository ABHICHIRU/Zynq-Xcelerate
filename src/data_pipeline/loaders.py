import torch
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

def get_dataloader(dataset_path, batch_size=32, shuffle=True, is_multiclass=False):
    """
    Standardized loader for SkyShield RF datasets.
    Ensures float32 precision for I/Q samples and correct label typing.
    """
    data = np.load(dataset_path)
    X = torch.tensor(data['X'], dtype=torch.float32)
    
    # CrossEntropyLoss expects Long for multiclass, BCEWithLogitsLoss expects Float for binary
    label_dtype = torch.long if is_multiclass else torch.float32
    Y = torch.tensor(data['Y'], dtype=label_dtype)
    
    dataset = TensorDataset(X, Y)
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)

def verify_normalization(loader):
    """Verifies that all samples in the loader are within the [-1.0, 1.0] INT8 range."""
    for x, _ in loader:
        if x.min() < -1.0001 or x.max() > 1.0001:
            return False
    return True
