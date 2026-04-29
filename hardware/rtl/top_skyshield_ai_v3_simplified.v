`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Top Level Integration (SIMPLIFIED FOR FPGA)
// Reduced IO interface to fit xc7z020clg484-1 (~100 pins max)
// Integrates 1D Convolution Processing natively into the fabric.
// ============================================================================

module top_skyshield_ai_v3 #(
    parameter BASE_ADDR = 32'h40000000
)(
    // Clock and Reset - Simplified to Single Ended to bypass LVDS pin locking
    input  wire              sys_clk,
    input  wire              ml_clk,
    input  wire              rst_n,
    
    // AXI Clock Domain
    input  wire              s_axi_aclk,
    input  wire              s_axi_aresetn,
    
    // AXI Slave Interface - SIMPLIFIED (16-bit data bus)
    input  wire [7:0]       s_axi_awaddr,
    input  wire             s_axi_awvalid,
    output wire             s_axi_awready,
    
    input  wire [15:0]      s_axi_wdata,
    input  wire             s_axi_wvalid,
    output wire             s_axi_wready,
    
    output wire [1:0]       s_axi_bresp,
    output wire             s_axi_bvalid,
    input  wire             s_axi_bready,
    
    input  wire [7:0]       s_axi_araddr,
    input  wire             s_axi_arvalid,
    output wire             s_axi_arready,
    
    output wire [15:0]      s_axi_rdata,
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
    output wire              pwr_ddr_en,
    output wire              pwr_mgt_en
);

// ============================================================================
// Power Control - Buffered explicitly to avoid UnBuffered IO DRC Errors
// ============================================================================
assign pwr_enable = 1'b0;
assign pwr_lna_en = 1'b1;
assign pwr_adc_en = 1'b1;
assign pwr_ml_en  = 1'b1;
assign pwr_ddr_en = 1'b1;
assign pwr_mgt_en = 1'b1;

// ============================================================================
// AXI Reg Stub Space
// ============================================================================
assign s_axi_awready = 1'b1;
assign s_axi_wready  = 1'b1;
assign s_axi_bresp   = 2'b00;
assign s_axi_bvalid  = 1'b0;
assign s_axi_arready = 1'b1;
assign s_axi_rdata   = 16'hDEAD;
assign s_axi_rresp   = 2'b00;
assign s_axi_rvalid  = 1'b0;

// ============================================================================
// 1D Convolution Engine Integration
// ============================================================================
wire [15:0] conv_i_out;
wire [15:0] conv_q_out;
wire        conv_i_valid;
wire        conv_q_valid;
wire        conv_i_ready;
wire        conv_q_ready;

// Instance 1: I-Channel 1D Convolution Pipeline
conv1d #(
    .DATA_WIDTH(16),
    .KERNEL_SIZE(5),
    .COEFF_WIDTH(16),
    .ACC_WIDTH(32)
) conv_i_inst (
    .clk(sys_clk),
    .rst_n(rst_n),
    
    .s_axis_tdata(rf_i_data),
    .s_axis_tvalid(rf_valid),
    .s_axis_tready(conv_i_ready),
    
    .m_axis_tdata(conv_i_out),
    .m_axis_tvalid(conv_i_valid),
    .m_axis_tready(result_ready),
    
    .coeff_data(16'h0001), 
    .coeff_addr(5'd0),
    .coeff_we(1'b0),
    .kernel_sel(3'd1), 
    .enable(1'b1)
);

// Instance 2: Q-Channel 1D Convolution Pipeline
conv1d #(
    .DATA_WIDTH(16),
    .KERNEL_SIZE(5),
    .COEFF_WIDTH(16),
    .ACC_WIDTH(32)
) conv_q_inst (
    .clk(sys_clk),
    .rst_n(rst_n),
    
    .s_axis_tdata(rf_q_data),
    .s_axis_tvalid(rf_valid),
    .s_axis_tready(conv_q_ready),
    
    .m_axis_tdata(conv_q_out),
    .m_axis_tvalid(conv_q_valid),
    .m_axis_tready(result_ready),
    
    .coeff_data(16'h0001),
    .coeff_addr(5'd0),
    .coeff_we(1'b0),
    .kernel_sel(3'd1),
    .enable(1'b1)
);

assign rf_ready = conv_i_ready & conv_q_ready;
assign result_data  = {conv_i_out, conv_q_out};
assign result_valid = conv_i_valid & conv_q_valid;

// Clock buffered LEDs to avoid Unbuffered logic
reg [3:0] led_reg;
always @(posedge sys_clk or negedge rst_n) begin
    if (!rst_n) begin
        led_reg <= 4'b0000;
    end else begin
        led_reg <= {2'b00, result_valid, rf_ready};
    end
end
assign status_led = led_reg;

endmodule
