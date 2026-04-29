# ============================================================================
# SkyShield AI v3.0 - Conv1D FPGA Constraints
# Target Device: Xilinx Zynq-7000 (xc7z020clg484-1)
# ============================================================================

# Clock Constraints
create_clock -period 10.0 -name sys_clk [get_ports sys_clk]
create_clock -period 10.0 -name ml_clk [get_ports ml_clk]
create_clock -period 10.0 -name s_axi_aclk [get_ports s_axi_aclk]

# Clock Domain Crossing (CDC) Constraints
set_max_delay -datapath_only -from [get_clocks sys_clk] -to [get_clocks ml_clk] 20.0
set_max_delay -datapath_only -from [get_clocks ml_clk] -to [get_clocks sys_clk] 20.0

# I/O Pin Constraints (Single-Ended, No LVDS)
set_property PACKAGE_PIN E18 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]

set_property PACKAGE_PIN D19 [get_ports rst_n]
set_property IOSTANDARD LVCMOS33 [get_ports rst_n]

# RF Frontend Data Pins (I-Channel)
set_property PACKAGE_PIN A17 [get_ports {rf_i_data[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {rf_i_data[*]}]

# RF Frontend Data Pins (Q-Channel)
set_property PACKAGE_PIN B17 [get_ports {rf_q_data[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {rf_q_data[*]}]

# Status LED Output Pins (Single-ended GPIO)
set_property PACKAGE_PIN M14 [get_ports {status_led[0]}]
set_property IOSTANDARD LVCMOS33 [get_ports {status_led[*]}]
set_property DRIVE 12 [get_ports {status_led[*]}]
set_property SLEW SLOW [get_ports {status_led[*]}]

# Power Control Pins
set_property PACKAGE_PIN L18 [get_ports pwr_enable]
set_property IOSTANDARD LVCMOS33 [get_ports pwr_enable]

set_property PACKAGE_PIN M18 [get_ports pwr_lna_en]
set_property IOSTANDARD LVCMOS33 [get_ports pwr_lna_en]

set_property PACKAGE_PIN N17 [get_ports pwr_adc_en]
set_property IOSTANDARD LVCMOS33 [get_ports pwr_adc_en]

set_property PACKAGE_PIN P18 [get_ports pwr_ml_en]
set_property IOSTANDARD LVCMOS33 [get_ports pwr_ml_en]

set_property PACKAGE_PIN R17 [get_ports pwr_ddr_en]
set_property IOSTANDARD LVCMOS33 [get_ports pwr_ddr_en]

set_property PACKAGE_PIN T18 [get_ports pwr_mgt_en]
set_property IOSTANDARD LVCMOS33 [get_ports pwr_mgt_en]

# Thermal Sensor Input
set_property PACKAGE_PIN U18 [get_ports thermal_shutdown]
set_property IOSTANDARD LVCMOS33 [get_ports thermal_shutdown]
set_property PULLUP true [get_ports thermal_shutdown]

# AXI Slave Timing Constraints
set_property ASYNC_REG TRUE [get_cells -hier -filter {NAME =~ */axi_*}]
set_max_delay -datapath_only -from [get_clocks s_axi_aclk] -to [get_clocks sys_clk] 15.0

# DSP48 Utilization Hints
set_property KEEP_HIERARCHY YES [get_cells -hier -filter {NAME =~ */uut_*}]

# ============================================================================
# End of Constraints
# ============================================================================
