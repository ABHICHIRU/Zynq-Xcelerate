`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Top Level Integration
// Complete SkyShield AI v3.0 System
// ============================================================================

module top_skyshield_ai_v3 #(
    parameter BASE_ADDR = 32'h40000000
)(
    // Clock and Reset
    input  wire              sys_clk_p,
    input  wire              sys_clk_n,
    input  wire              ml_clk,
    input  wire              rst_n,
    
    // AXI Clock Domain
    input  wire              s_axi_aclk,
    input  wire              s_axi_aresetn,
    
    // AXI Slave Interface (from ARM)
    input  wire [31:0]      s_axi_awaddr,
    input  wire [2:0]       s_axi_awprot,
    input  wire             s_axi_awvalid,
    output wire             s_axi_awready,
    input  wire [31:0]      s_axi_wdata,
    input  wire [3:0]       s_axi_wstrb,
    input  wire             s_axi_wvalid,
    output wire             s_axi_wready,
    output wire [1:0]       s_axi_bresp,
    output wire             s_axi_bvalid,
    input  wire             s_axi_bready,
    input  wire [31:0]      s_axi_araddr,
    input  wire [2:0]       s_axi_arprot,
    input  wire             s_axi_arvalid,
    output wire             s_axi_arready,
    output wire [31:0]      s_axi_rdata,
    output wire [1:0]       s_axi_rresp,
    output wire             s_axi_rvalid,
    input  wire             s_axi_rready,
    
    // RF Frontend Interface
    input  wire [15:0]      rf_i_data,
    input  wire [15:0]      rf_q_data,
    input  wire              rf_valid,
    output wire              rf_ready,
    
    // Result Output
    output wire [31:0]      result_data,
    output wire              result_valid,
    input  wire              result_ready,
    
    // Status LEDs
    output wire [3:0]       status_led,
    
    // Power Control
    output wire              pwr_enable,
    input  wire              thermal_shutdown,
    output wire              pwr_lna_en,
    output wire              pwr_adc_en,
    output wire              pwr_ml_en,
    output wire              pwr_ddr_en
);

// ============================================================================
// Internal Clock
// ============================================================================
wire sys_clk = sys_clk_p;

(* keep = "true" *) wire unused_top_ports;
assign unused_top_ports = sys_clk_n | (|rf_q_data[15:8]) | result_ready;

// ============================================================================
// Control Registers
// ============================================================================
wire [31:0] control_reg;
wire [31:0] status_reg;
wire [31:0] threshold_reg;
wire [3:0]  pwr_status;
wire        pwr_ready;
wire        pwr_fault;
wire        pwr_enable_req;

control_registers u_control_registers (
    .s_axi_aclk(s_axi_aclk),
    .s_axi_aresetn(s_axi_aresetn),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_awprot(s_axi_awprot),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_bresp(s_axi_bresp),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),
    .s_axi_araddr(s_axi_araddr),
    .s_axi_arprot(s_axi_arprot),
    .s_axi_arvalid(s_axi_arvalid),
    .s_axi_arready(s_axi_arready),
    .s_axi_rdata(s_axi_rdata),
    .s_axi_rresp(s_axi_rresp),
    .s_axi_rvalid(s_axi_rvalid),
    .s_axi_rready(s_axi_rready),
    .control_reg(control_reg),
    .status_reg(status_reg),
    .model_addr_reg(),
    .threshold_reg(threshold_reg)
);

// ============================================================================
// Power Control
// ============================================================================
assign pwr_enable_req = control_reg[0];

power_control u_power_control (
    .clk(sys_clk),
    .rst_n(rst_n),
    .pwr_enable(pwr_enable_req),
    .pwr_lna_req(control_reg[4]),
    .pwr_adc_req(control_reg[5]),
    .pwr_ml_req(control_reg[6]),
    .pwr_ddr_req(control_reg[7]),
    .thermal_shutdown(thermal_shutdown),
    .pwr_lna_en(pwr_lna_en),
    .pwr_adc_en(pwr_adc_en),
    .pwr_ml_en(pwr_ml_en),
    .pwr_ddr_en(pwr_ddr_en),
    .pwr_lna_pgood(1'b1),
    .pwr_adc_pgood(1'b1),
    .pwr_ml_pgood(1'b1),
    .pwr_ddr_pgood(1'b1),
    .pwr_status(pwr_status),
    .pwr_ready(pwr_ready),
    .pwr_fault(pwr_fault)
);

assign pwr_enable = pwr_ready;

// ============================================================================
// Input Buffer
// ============================================================================
wire [10:0] input_wr_addr;
wire input_full;
wire input_empty;
wire [15:0] input_sample = {rf_i_data[15:8], rf_q_data[7:0]};

input_buffer_ram u_input_buffer (
    .clk(sys_clk),
    .rst_n(rst_n),
    .data_in(input_sample),
    .wr_en(rf_valid),
    .wr_addr(input_wr_addr),
    .rd_en(1'b0),
    .rd_addr(11'b0),
    .data_out(),
    .full(input_full),
    .empty(input_empty),
    .count(),
    .overflow_error()
);

assign rf_ready = !input_full;
assign input_wr_addr = 11'b0;  // Auto-increment

// ============================================================================
// Threat Detector
// ============================================================================
wire threat_valid;
wire [7:0] threat_prob;
wire is_threat;

threat_detector_rtl u_threat_detector (
    .clk(ml_clk),
    .rst_n(rst_n && pwr_ml_en),
    .valid_in(rf_valid),
    .i_data(rf_i_data[7:0]),
    .q_data(rf_q_data[7:0]),
    .valid_out(threat_valid),
    .threat_prob(threat_prob),
    .is_threat(is_threat)
);

// ============================================================================
// Type Classifier
// ============================================================================
wire type_valid;
wire [7:0] type_prob_0;
wire [7:0] type_prob_1;
wire [7:0] type_prob_2;
wire [7:0] type_prob_3;
wire [7:0] type_prob_4;
wire [7:0] type_prob_5;
wire [2:0] type_id;

type_classifier_rtl u_type_classifier (
    .clk(ml_clk),
    .rst_n(rst_n && pwr_ml_en),
    .valid_in(rf_valid),
    .i_data(rf_i_data[7:0]),
    .q_data(rf_q_data[7:0]),
    .valid_out(type_valid),
    .class_prob_0(type_prob_0),
    .class_prob_1(type_prob_1),
    .class_prob_2(type_prob_2),
    .class_prob_3(type_prob_3),
    .class_prob_4(type_prob_4),
    .class_prob_5(type_prob_5),
    .class_id(type_id)
);

// ============================================================================
// Jammer Detector
// ============================================================================
wire jammer_valid;
wire [7:0] jammer_prob;
wire is_jammer;

jammer_detector_rtl u_jammer_detector (
    .clk(ml_clk),
    .rst_n(rst_n && pwr_ml_en),
    .valid_in(rf_valid),
    .i_data(rf_i_data[7:0]),
    .q_data(rf_q_data[7:0]),
    .valid_out(jammer_valid),
    .jammer_prob(jammer_prob),
    .is_jammer(is_jammer)
);

// ============================================================================
// Voting Logic
// ============================================================================
wire voting_valid;
wire final_threat;
wire [2:0] final_type;
wire jammer_flag;
wire [7:0] final_confidence;

voting_logic u_voting_logic (
    .clk(ml_clk),
    .rst_n(rst_n),
    .valid_in(threat_valid),
    .threat_prob(threat_prob),
    .threat_valid(threat_valid),
    .type_prob_0(type_prob_0),
    .type_prob_1(type_prob_1),
    .type_prob_2(type_prob_2),
    .type_prob_3(type_prob_3),
    .type_prob_4(type_prob_4),
    .type_prob_5(type_prob_5),
    .type_id(type_id),
    .type_valid(type_valid),
    .jammer_prob(jammer_prob),
    .jammer_valid(jammer_valid),
    .valid_out(voting_valid),
    .is_threat(final_threat),
    .threat_type(final_type),
    .jammer_flag(jammer_flag),
    .confidence(final_confidence),
    .timestamp()
);

// ============================================================================
// Tracking Engine
// ============================================================================
wire tracking_valid;
wire [3:0] num_tracks;
wire [31:0] track_id_0;
wire [31:0] track_id_1;
wire [31:0] track_id_2;
wire [31:0] track_id_3;
wire [31:0] track_id_4;
wire [31:0] track_id_5;
wire [31:0] track_id_6;
wire [31:0] track_id_7;
wire [31:0] track_id_8;
wire [31:0] track_id_9;
wire [31:0] track_id_10;
wire [31:0] track_id_11;
wire [31:0] track_id_12;
wire [31:0] track_id_13;
wire [31:0] track_id_14;
wire [31:0] track_id_15;
wire [15:0] track_age_0;
wire [15:0] track_age_1;
wire [15:0] track_age_2;
wire [15:0] track_age_3;
wire [15:0] track_age_4;
wire [15:0] track_age_5;
wire [15:0] track_age_6;
wire [15:0] track_age_7;
wire [15:0] track_age_8;
wire [15:0] track_age_9;
wire [15:0] track_age_10;
wire [15:0] track_age_11;
wire [15:0] track_age_12;
wire [15:0] track_age_13;
wire [15:0] track_age_14;
wire [15:0] track_age_15;
wire [15:0] track_velocity_0;
wire [15:0] track_velocity_1;
wire [15:0] track_velocity_2;
wire [15:0] track_velocity_3;
wire [15:0] track_velocity_4;
wire [15:0] track_velocity_5;
wire [15:0] track_velocity_6;
wire [15:0] track_velocity_7;
wire [15:0] track_velocity_8;
wire [15:0] track_velocity_9;
wire [15:0] track_velocity_10;
wire [15:0] track_velocity_11;
wire [15:0] track_velocity_12;
wire [15:0] track_velocity_13;
wire [15:0] track_velocity_14;
wire [15:0] track_velocity_15;
wire [2:0] track_type_0;
wire [2:0] track_type_1;
wire [2:0] track_type_2;
wire [2:0] track_type_3;
wire [2:0] track_type_4;
wire [2:0] track_type_5;
wire [2:0] track_type_6;
wire [2:0] track_type_7;
wire [2:0] track_type_8;
wire [2:0] track_type_9;
wire [2:0] track_type_10;
wire [2:0] track_type_11;
wire [2:0] track_type_12;
wire [2:0] track_type_13;
wire [2:0] track_type_14;
wire [2:0] track_type_15;
wire track_confirmed_0;
wire track_confirmed_1;
wire track_confirmed_2;
wire track_confirmed_3;
wire track_confirmed_4;
wire track_confirmed_5;
wire track_confirmed_6;
wire track_confirmed_7;
wire track_confirmed_8;
wire track_confirmed_9;
wire track_confirmed_10;
wire track_confirmed_11;
wire track_confirmed_12;
wire track_confirmed_13;
wire track_confirmed_14;
wire track_confirmed_15;

tracking_engine u_tracking_engine (
    .clk(ml_clk),
    .rst_n(rst_n),
    .valid_in(voting_valid),
    .threat_type(final_type),
    .is_threat(final_threat),
    .confidence(final_confidence),
    .signal_bearing(16'b0),
    .signal_strength(16'b0),
    .timestamp(32'b0),
    .valid_out(tracking_valid),
    .num_active_tracks(num_tracks),
    .track_id_0(track_id_0),
    .track_id_1(track_id_1),
    .track_id_2(track_id_2),
    .track_id_3(track_id_3),
    .track_id_4(track_id_4),
    .track_id_5(track_id_5),
    .track_id_6(track_id_6),
    .track_id_7(track_id_7),
    .track_id_8(track_id_8),
    .track_id_9(track_id_9),
    .track_id_10(track_id_10),
    .track_id_11(track_id_11),
    .track_id_12(track_id_12),
    .track_id_13(track_id_13),
    .track_id_14(track_id_14),
    .track_id_15(track_id_15),
    .track_age_0(track_age_0),
    .track_age_1(track_age_1),
    .track_age_2(track_age_2),
    .track_age_3(track_age_3),
    .track_age_4(track_age_4),
    .track_age_5(track_age_5),
    .track_age_6(track_age_6),
    .track_age_7(track_age_7),
    .track_age_8(track_age_8),
    .track_age_9(track_age_9),
    .track_age_10(track_age_10),
    .track_age_11(track_age_11),
    .track_age_12(track_age_12),
    .track_age_13(track_age_13),
    .track_age_14(track_age_14),
    .track_age_15(track_age_15),
    .track_velocity_0(track_velocity_0),
    .track_velocity_1(track_velocity_1),
    .track_velocity_2(track_velocity_2),
    .track_velocity_3(track_velocity_3),
    .track_velocity_4(track_velocity_4),
    .track_velocity_5(track_velocity_5),
    .track_velocity_6(track_velocity_6),
    .track_velocity_7(track_velocity_7),
    .track_velocity_8(track_velocity_8),
    .track_velocity_9(track_velocity_9),
    .track_velocity_10(track_velocity_10),
    .track_velocity_11(track_velocity_11),
    .track_velocity_12(track_velocity_12),
    .track_velocity_13(track_velocity_13),
    .track_velocity_14(track_velocity_14),
    .track_velocity_15(track_velocity_15),
    .track_type_0(track_type_0),
    .track_type_1(track_type_1),
    .track_type_2(track_type_2),
    .track_type_3(track_type_3),
    .track_type_4(track_type_4),
    .track_type_5(track_type_5),
    .track_type_6(track_type_6),
    .track_type_7(track_type_7),
    .track_type_8(track_type_8),
    .track_type_9(track_type_9),
    .track_type_10(track_type_10),
    .track_type_11(track_type_11),
    .track_type_12(track_type_12),
    .track_type_13(track_type_13),
    .track_type_14(track_type_14),
    .track_type_15(track_type_15),
    .track_confirmed_0(track_confirmed_0),
    .track_confirmed_1(track_confirmed_1),
    .track_confirmed_2(track_confirmed_2),
    .track_confirmed_3(track_confirmed_3),
    .track_confirmed_4(track_confirmed_4),
    .track_confirmed_5(track_confirmed_5),
    .track_confirmed_6(track_confirmed_6),
    .track_confirmed_7(track_confirmed_7),
    .track_confirmed_8(track_confirmed_8),
    .track_confirmed_9(track_confirmed_9),
    .track_confirmed_10(track_confirmed_10),
    .track_confirmed_11(track_confirmed_11),
    .track_confirmed_12(track_confirmed_12),
    .track_confirmed_13(track_confirmed_13),
    .track_confirmed_14(track_confirmed_14),
    .track_confirmed_15(track_confirmed_15)
);

// ============================================================================
// Output Assignment (Bypass output_aggregator for simplification)
// ============================================================================
assign result_data = {pwr_status, pwr_fault, pwr_ready, num_tracks, jammer_flag, final_threat, final_type, final_confidence, 9'b0};
assign result_valid = tracking_valid;

// ============================================================================
// Status LEDs
// ============================================================================
assign status_led[0] = pwr_ready;            // Power OK
assign status_led[1] = final_threat;         // Threat detected
assign status_led[2] = jammer_flag;          // Jammer detected
assign status_led[3] = tracking_valid;       // Processing active

endmodule
