import pytest
import pandas as pd
import numpy as np
import os
from dashboard import load_data, calculate_metrics

# --- Mock Data for Testing ---
@pytest.fixture
def sample_data():
    data = {
        'cycle': range(1, 11),
        'test_scenario_name': ['Scenario_A']*5 + ['Scenario_B']*5,
        'rf_i': np.random.randn(10),
        'rf_q': np.random.randn(10),
        'raw_energy': [10, 20, 30, 40, 50, 15, 25, 35, 45, 55],
        'smooth_energy': [12, 22, 32, 42, 52, 17, 27, 37, 47, 57],
        'signal_detected': [0, 0, 1, 1, 1, 0, 1, 1, 0, 1],
        'final_result':    [0, 1, 1, 1, 0, 0, 1, 1, 1, 1], # 1 mismatch at index 1, 4, 8
        'confidence_level': [5, 15, 25, 35, 45, 10, 20, 30, 40, 50],
        'detection_status': ['Pass', 'Fail', 'Pass', 'Pass', 'Pass', 'Pass', 'Fail', 'Pass', 'Pass', 'Pass'],
        'threat_type_detected': ['DJI', 'Unknown', 'DJI', 'DJI', 'Unknown', 'None', 'DJI', 'None', 'DJI', 'Unknown'],
        'top1_confidence': [0.8, 0.2, 0.9, 0.85, 0.3, 0.1, 0.7, 0.05, 0.95, 0.4],
        'top2_confidence': [0.1, 0.1, 0.05, 0.1, 0.2, 0.05, 0.2, 0.02, 0.03, 0.1]
    }
    return pd.DataFrame(data)

# --- 1. Data Validation Tests ---
def test_load_data_integrity(tmp_path):
    # Create a temp CSV
    d = tmp_path / "test.csv"
    df_orig = pd.DataFrame({'test_scenario_name': ['A'], 'threat_type_detected': [np.nan]})
    df_orig.to_csv(d, index=False)
    
    df = load_data(str(d))
    assert df is not None
    assert 'threat_type_detected' in df.columns
    assert df['threat_type_detected'].iloc[0] == 'None' # Missing value handling

def test_required_columns(sample_data):
    required_cols = [
        'cycle', 'test_scenario_name', 'rf_i', 'rf_q', 'raw_energy', 
        'smooth_energy', 'signal_detected', 'confidence_level', 
        'final_result', 'threat_type_detected'
    ]
    for col in required_cols:
        assert col in sample_data.columns

# --- 2. KPI Calculation Tests ---
def test_kpi_formulas(sample_data):
    metrics = calculate_metrics(sample_data, sample_data)
    
    # Detection Accuracy: (7 matches out of 10) -> 70%
    # Matches: [T, F, T, T, F, T, T, T, F, T] -> 7/10
    assert metrics['accuracy'] == 70.0
    
    # Avg Confidence: (5+15+25+35+45+10+20+30+40+50)/10 = 275/10 = 27.5
    assert metrics['avg_confidence'] == 27.5
    
    # FPR: final_result=1 when signal_detected=0
    # signal_detected=0 at indices [0, 1, 5, 8]
    # final_result at those indices: [0, 1, 0, 1]
    # FPR = 2 / 4 = 50%
    assert metrics['fpr'] == 50.0
    
    # Scenario Coverage: A and B -> 2
    assert metrics['scenario_coverage'] == 2
    
    # Pass Rate: 8 'Pass' out of 10 -> 80%
    assert metrics['pass_rate'] == 80.0
    
    # Top-1 Confidence Average
    expected_top1 = sample_data['top1_confidence'].mean()
    assert metrics['top1_avg'] == pytest.approx(expected_top1)

def test_kpi_empty_data(sample_data):
    empty_df = sample_data.iloc[0:0]
    metrics = calculate_metrics(sample_data, empty_df)
    assert metrics['accuracy'] == 0.0
    assert metrics['fpr'] == 0.0
    assert metrics['scenario_coverage'] == 2

# --- 3. Functional / Filter Tests ---
def test_filtering_logic(sample_data):
    # Simulate Sidebar Filter
    selected_scenarios = ['Scenario_A']
    filtered = sample_data[sample_data['test_scenario_name'].isin(selected_scenarios)]
    assert len(filtered) == 5
    assert all(filtered['test_scenario_name'] == 'Scenario_A')

def test_threat_distribution_counts(sample_data):
    counts = sample_data['threat_type_detected'].value_counts()
    assert counts['DJI'] == 5
    assert counts['Unknown'] == 3
    assert counts['None'] == 2

# --- 4. Visualization Data Prep Tests ---
def test_correlation_heatmap_computation(sample_data):
    cols = ['raw_energy', 'smooth_energy', 'confidence_level', 'final_result']
    corr = sample_data[cols].corr()
    assert corr.shape == (4, 4)
    assert not corr.isnull().values.any()

def test_top_confidence_comparison_prep(sample_data):
    # Only cycle vs top1/top2
    conf_df = sample_data[sample_data['top1_confidence'] > 0]
    assert len(conf_df) == 10
    assert (conf_df['top1_confidence'] >= conf_df['top2_confidence']).all()

# --- 5. Edge Cases ---
def test_zero_division_fpr():
    # Scenario with NO zeros in signal_detected (everything is a signal)
    df = pd.DataFrame({
        'test_scenario_name': ['S1', 'S1'],
        'signal_detected': [1, 1],
        'final_result': [1, 1],
        'confidence_level': [10, 10],
        'detection_status': ['Pass', 'Pass'],
        'top1_confidence': [0.5, 0.5]
    })
    metrics = calculate_metrics(df, df)
    assert metrics['fpr'] == 0.0 # Should not crash

def test_missing_data_file():
    df = load_data("non_existent_file.csv")
    assert df is None

if __name__ == "__main__":
    pytest.main([__file__])
