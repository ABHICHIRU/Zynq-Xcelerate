#!/bin/bash
# ============================================================================
# SkyShield AI v3.0 - Conv1D Exhaustive Testbench Simulation Runner
# Runs all verification tests and captures results to CSV
# ============================================================================

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
RTL_DIR="${PROJECT_ROOT}/verilog_imp/rtl"
TB_DIR="${PROJECT_ROOT}/verilog_imp/testbench"
RESULTS_DIR="${PROJECT_ROOT}/verilog_imp/results"

VIVADO_BIN="/c/AMDDesignTools/2025.2/Vivado/bin"

echo "=========================================="
echo "SkyShield Conv1D Exhaustive Test Suite"
echo "=========================================="
echo "RTL Directory:     ${RTL_DIR}"
echo "Testbench Dir:     ${TB_DIR}"
echo "Results Directory: ${RESULTS_DIR}"
echo "=========================================="

# Create results directory if not present
mkdir -p "${RESULTS_DIR}"

# Function to run a single testbench
run_testbench() {
    local tb_name=$1
    local snapshot_name=$2
    
    echo ""
    echo "[INFO] Compiling ${tb_name}..."
    cd "${TB_DIR}"
    
    # Compile RTL and testbench
    ${VIVADO_BIN}/xvlog "${RTL_DIR}/conv1d.v" "${TB_DIR}/${tb_name}.v"
    
    # Elaborate
    echo "[INFO] Elaborating ${snapshot_name}..."
    ${VIVADO_BIN}/xelab -debug typical -top ${tb_name} -snapshot ${snapshot_name}
    
    # Simulate
    echo "[INFO] Running simulation for ${snapshot_name}..."
    ${VIVADO_BIN}/xsim ${snapshot_name} -R
    
    echo "[INFO] ${tb_name} simulation complete"
}

# Run all testbenches
echo ""
echo "[TEST 1] Running basic structural testbench..."
run_testbench "tb_conv1d" "tb_conv1d_snap"

echo ""
echo "[TEST 2] Running exhaustive single-channel testbench..."
run_testbench "tb_conv1d_exhaustive" "tb_exhaustive_snap"

echo ""
echo "[TEST 3] Running exhaustive dual-channel I/Q testbench..."
run_testbench "tb_conv1d_iq_exhaustive" "iq_snap"

# Generate summary report
echo ""
echo "=========================================="
echo "SIMULATION SUMMARY"
echo "=========================================="
echo "CSV Results generated:"
ls -lh "${RESULTS_DIR}"/*.csv 2>/dev/null || echo "[WARNING] No CSV files found in results directory"

echo ""
echo "[SUCCESS] All testbenches completed!"
echo "Results are stored in: ${RESULTS_DIR}"
echo "=========================================="
