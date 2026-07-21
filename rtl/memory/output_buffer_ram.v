`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Output Buffer RAM
// BRAM-based output buffer for storing classification results
// Capacity: 256 × 32-bit (timestamps + results for 3 models)
// ============================================================================

module output_buffer_ram #(
    parameter ADDR_WIDTH = 8,       // 256 addresses
    parameter DATA_WIDTH = 32,      // 32-bit result
    parameter DEPTH = 256           // 256 entries
)(
    input  wire                  clk,
    input  wire                  rst_n,
    
    // Write interface (from voting logic)
    input  wire [DATA_WIDTH-1:0] data_in,
    input  wire                  wr_en,
    input  wire [ADDR_WIDTH-1:0] wr_addr,
    
    // Read interface (to AXI/ARM)
    input  wire                  rd_en,
    input  wire [ADDR_WIDTH-1:0] rd_addr,
    output wire [DATA_WIDTH-1:0] data_out,
    
    // Status signals
    output wire                  full,
    output wire                  empty,
    output wire [ADDR_WIDTH:0]   count,
    output wire                  underflow_error
);

// ============================================================================
// Local Parameters
// ============================================================================
localparam FULL_THRESHOLD = DEPTH - 8;  // Almost full threshold

// ============================================================================
// BRAM (True Dual-Port)
// ============================================================================
(* RAM_STYLE = "BLOCK" *)
reg [DATA_WIDTH-1:0] ram [0:DEPTH-1];

// Write port
always @(posedge clk) begin
    if (wr_en) begin
        ram[wr_addr] <= data_in;
    end
end

// Read port
reg [DATA_WIDTH-1:0] data_out_reg;
always @(posedge clk) begin
    if (rd_en) begin
        data_out_reg <= ram[rd_addr];
    end
end

assign data_out = data_out_reg;

// ============================================================================
// Status Logic
// ============================================================================
reg [ADDR_WIDTH:0] count_reg;
reg underflow_error_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        count_reg <= 0;
    end else if (wr_en && !rd_en) begin
        count_reg <= count_reg + 1;
    end else if (!wr_en && rd_en && count_reg > 0) begin
        count_reg <= count_reg - 1;
    end
end

assign count = count_reg;

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        underflow_error_reg <= 0;
    end else if (rd_en && (count_reg == 0)) begin
        underflow_error_reg <= 1;
    end else if (wr_en) begin
        underflow_error_reg <= 0;
    end
end

assign underflow_error = underflow_error_reg;
assign full = (count_reg >= FULL_THRESHOLD);
assign empty = (count_reg == 0);

endmodule
