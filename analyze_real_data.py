import pandas as pd
import numpy as np
import ast
import re

def parse_iq_string(iq_str):
    if not isinstance(iq_str, str) or iq_str.strip() == "":
        return None
    try:
        # The string looks like "[(-0.7204...-0.1315j), ...]"
        # Clean the string to be compatible with ast.literal_eval or just use regex
        # Using regex to find all complex numbers
        matches = re.findall(r'\(([^)]+)\)', iq_str)
        complex_nums = [complex(m) for m in matches]
        return np.array(complex_nums)
    except Exception as e:
        return None

def analyze_patterns(file_path, num_rows=500):
    print(f"Analyzing first {num_rows} rows of {file_path} for I/Q patterns...")
    
    # Read first chunk
    df = pd.read_csv(file_path, nrows=num_rows)
    
    iq_data_list = []
    for idx, row in df.iterrows():
        iq_array = parse_iq_string(row['I/Q Data'])
        if iq_array is not None:
            iq_data_list.append(iq_array)
    
    if not iq_data_list:
        print("No valid I/Q data found in the sample.")
        return
    
    # Calculate statistics across all samples
    all_iq = np.concatenate(iq_data_list)
    
    stats = {
        "mean_i": np.mean(all_iq.real),
        "mean_q": np.mean(all_iq.imag),
        "std_i": np.std(all_iq.real),
        "std_q": np.std(all_iq.imag),
        "abs_mean": np.mean(np.abs(all_iq)),
        "abs_std": np.std(np.abs(all_iq)),
        "phase_mean": np.mean(np.angle(all_iq)),
        "phase_std": np.std(np.angle(all_iq)),
        "max_val": np.max(np.abs(all_iq)),
        "min_val": np.min(np.abs(all_iq))
    }
    
    print("\n--- Extracted Real-World I/Q Patterns ---")
    for k, v in stats.items():
        print(f"{k}: {v:.6f}")
    
    # Save these for the generator
    import json
    with open("real_world_stats.json", "w") as f:
        json.dump(stats, f)
    print("\nPatterns saved to real_world_stats.json")

if __name__ == "__main__":
    analyze_patterns("logged_data.csv")
