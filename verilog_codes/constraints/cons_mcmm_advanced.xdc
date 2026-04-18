# =============================================================================
# SkyShield Elite AXI - Advanced Timing Constraints (MCMM Ready)
# Vivado uses XDC (SDC-compatible Tcl constraints).
#
# Goal:
# - Clean constraints for implementation
# - Accurate cross-domain timing intent
# - Ready for best/typical/worst corner reporting
# =============================================================================

# -----------------------------------------------------------------------------
# Clock Definitions
# -----------------------------------------------------------------------------
create_clock -name fclk_clk0 -period 20.000 -waveform {0.000 10.000} [get_ports fclk_clk0]
create_clock -name cfg_clk   -period 20.000 -waveform {0.000 10.000} [get_ports cfg_clk]

# Clock quality / margining (realistic signoff-style guardbands)
set_input_jitter [get_clocks fclk_clk0] 0.080
set_input_jitter [get_clocks cfg_clk]   0.050
set_clock_uncertainty -setup 0.250 [get_clocks fclk_clk0]
set_clock_uncertainty -hold  0.080 [get_clocks fclk_clk0]
set_clock_uncertainty -setup 0.200 [get_clocks cfg_clk]
set_clock_uncertainty -hold  0.060 [get_clocks cfg_clk]

# NOTE:
# set_clock_transition is not supported in this Vivado flow/context, so it is
# intentionally omitted to avoid CRITICAL WARNINGs during implementation.

# -----------------------------------------------------------------------------
# I/O Standards
# -----------------------------------------------------------------------------
set_property IOSTANDARD LVCMOS33 [get_ports fclk_clk0]
set_property IOSTANDARD LVCMOS33 [get_ports fclk_reset0_n]
set_property IOSTANDARD LVCMOS33 [get_ports cfg_clk]
set_property IOSTANDARD LVCMOS33 [get_ports cfg_resetn]
set_property IOSTANDARD LVCMOS33 [get_ports cfg_valid]
set_property IOSTANDARD LVCMOS33 [get_ports cfg_ready]
set_property IOSTANDARD LVCMOS33 [get_ports {cfg_addr[*]}]
set_property IOSTANDARD LVCMOS33 [get_ports {cfg_data[*]}]
set_property IOSTANDARD LVCMOS33 [get_ports {leds[*]}]
set_property IOSTANDARD LVCMOS25 [get_ports {rf_i[*]}]
set_property IOSTANDARD LVCMOS25 [get_ports {rf_q[*]}]
set_property IOSTANDARD LVCMOS33 [get_ports {dbg_bus[*]}]

# -----------------------------------------------------------------------------
# I/O Delays
# -----------------------------------------------------------------------------
# Control/config interface
set_input_delay  -clock cfg_clk   -max 4.000 [get_ports {cfg_valid cfg_addr[*] cfg_data[*]}]
set_input_delay  -clock cfg_clk   -min 0.500 [get_ports {cfg_valid cfg_addr[*] cfg_data[*]}]
set_output_delay -clock cfg_clk   -max 4.000 [get_ports cfg_ready]
set_output_delay -clock cfg_clk   -min 0.000 [get_ports cfg_ready]

# RF sampled interface
set_input_delay  -clock fclk_clk0 -max 5.000 [get_ports {rf_i[*] rf_q[*]}]
set_input_delay  -clock fclk_clk0 -min 1.000 [get_ports {rf_i[*] rf_q[*]}]

# Outputs
set_output_delay -clock fclk_clk0 -max 7.000  [get_ports {leds[*]}]
set_output_delay -clock fclk_clk0 -min 0.000  [get_ports {leds[*]}]

# dbg_bus is diagnostic/telemetry-only and not a timing signoff interface.
# Exclude it from timing closure so implementation focuses on functional paths.
set_false_path -to [get_ports {dbg_bus[*]}]

# -----------------------------------------------------------------------------
# CDC + Reset Exceptions
# -----------------------------------------------------------------------------
# Asynchronous clock domains
set_clock_groups -asynchronous -group [get_clocks cfg_clk] -group [get_clocks fclk_clk0]

# Asynchronous reset release (not timed as data path)
set_false_path -from [get_ports cfg_resetn]
set_false_path -from [get_ports fclk_reset0_n]

# Optional hackathon/prototyping setting:
# allow bitstream generation without package pin LOC assignment.
# Replace this with proper LOC constraints for board deployment.
set_property SEVERITY {Warning} [get_drc_checks UCIO-1]

# -----------------------------------------------------------------------------
# Notes for multi-corner signoff
# -----------------------------------------------------------------------------
# Use this file with analysis/report_mcmm_advanced.tcl to generate:
# - typical corner reports
# - worst corner reports
# - best corner reports
# - worst_with_ocv derated reports
