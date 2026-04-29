#!/usr/bin/env python3
"""
SkyShield AI v3.0 - Conv1D CSV Results Analyzer
Parses simulation CSV dumps and generates analysis reports
"""

import csv
import sys
import os
from pathlib import Path
from collections import defaultdict

def parse_csv_results(csv_file):
    """Parse CSV testbench results and extract key metrics"""
    
    print(f"\n[INFO] Analyzing CSV file: {csv_file}")
    print("=" * 60)
    
    data = []
    try:
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    except FileNotFoundError:
        print(f"[ERROR] File not found: {csv_file}")
        return None
    
    if not data:
        print("[WARNING] No data rows found in CSV")
        return None
    
    # Extract key statistics
    total_cycles = len(data)
    header = data[0].keys()
    
    print(f"Total Cycles:     {total_cycles}")
    print(f"Columns:          {', '.join(header)}")
    
    # Count valid outputs
    valid_outputs = 0
    reset_cycles = 0
    enabled_cycles = 0
    
    for row in data:
        try:
            if row.get('Out_Valid', '0') == '1' or row.get('m_axis_tvalid', '0') == '1':
                valid_outputs += 1
            if row.get('Reset_n', '0') == '0':
                reset_cycles += 1
            if row.get('Enable', '0') == '1':
                enabled_cycles += 1
        except (KeyError, ValueError):
            pass
    
    # Analyze kernel selections if present
    kernel_distribution = defaultdict(int)
    output_range = {'min': None, 'max': None}
    
    for row in data:
        try:
            # Kernel distribution
            if 'Kernel_Sel' in row:
                kernel_distribution[row['Kernel_Sel']] += 1
            
            # Output value range
            if 'Out_Data' in row and row['Out_Data'].strip():
                val = int(row['Out_Data'])
                if output_range['min'] is None or val < output_range['min']:
                    output_range['min'] = val
                if output_range['max'] is None or val > output_range['max']:
                    output_range['max'] = val
        except (KeyError, ValueError):
            pass
    
    print(f"\nStatistics:")
    print(f"  Valid Outputs:   {valid_outputs}")
    print(f"  Reset Cycles:    {reset_cycles}")
    print(f"  Enabled Cycles:  {enabled_cycles}")
    
    if kernel_distribution:
        print(f"\nKernel Distribution:")
        for kernel, count in sorted(kernel_distribution.items()):
            print(f"  Kernel {kernel}: {count} cycles")
    
    if output_range['min'] is not None:
        print(f"\nOutput Value Range:")
        print(f"  Min: {output_range['min']:6d} (0x{output_range['min']:04x})")
        print(f"  Max: {output_range['max']:6d} (0x{output_range['max']:04x})")
    
    print("\n[SUCCESS] Analysis Complete")
    print("=" * 60)
    
    return {
        'total_cycles': total_cycles,
        'valid_outputs': valid_outputs,
        'output_range': output_range,
        'kernel_dist': kernel_distribution
    }

def main():
    results_dir = Path(__file__).parent.parent / "results"
    
    if not results_dir.exists():
        print(f"[ERROR] Results directory not found: {results_dir}")
        sys.exit(1)
    
    csv_files = sorted(results_dir.glob("*.csv"))
    
    if not csv_files:
        print(f"[WARNING] No CSV files found in: {results_dir}")
        sys.exit(0)
    
    print("\n" + "=" * 60)
    print("SkyShield Conv1D - CSV Results Analysis")
    print("=" * 60)
    
    for csv_file in csv_files:
        parse_csv_results(str(csv_file))
    
    print("\n[INFO] Analysis Summary generated successfully")

if __name__ == "__main__":
    main()
