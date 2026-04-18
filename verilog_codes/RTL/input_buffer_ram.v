`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Input Buffer RAM
// BRAM-based input buffer for storing incoming I/Q samples
// Capacity: 2048 × 16-bit (2 channels × 512 samples with overflow protection)
// ============================================================================

module input_buffer_ram #(
    parameter ADDR_WIDTH = 11,      // 2048 addresses
    parameter DATA_WIDTH = 16,       // 16-bit fixed-point
    parameter DEPTH = 2048           // 2K samples
)(
    input  wire                  clk,
    input  wire                  rst_n,
    
    // Write interface (from ADC/RF Frontend)
    input  wire [DATA_WIDTH-1:0]  data_in,
    input  wire                  wr_en,
    input  wire [ADDR_WIDTH-1:0] wr_addr,
    
    // Read interface (to processing)
    input  wire                  rd_en,
    input  wire [ADDR_WIDTH-1:0] rd_addr,
    output wire [DATA_WIDTH-1:0] data_out,
    
    // Status signals
    output wire                  full,
    output wire                  empty,
    output wire [ADDR_WIDTH:0]   count,
    output wire                  overflow_error
);

// ============================================================================
// Local Parameters
// ============================================================================
localparam FULL_THRESHOLD = DEPTH - 64;  // Almost full threshold

// ============================================================================
// Dual-Port BRAM (True Dual-Port RAM)
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
reg overflow_error_reg;

// FIFO count
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

// Overflow error detection
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        overflow_error_reg <= 0;
    end else if (wr_en && (count_reg >= DEPTH)) begin
        overflow_error_reg <= 1;
    end else if (rd_en && (count_reg <= DEPTH)) begin
        overflow_error_reg <= 0;
    end
end

assign overflow_error = overflow_error_reg;
assign full = (count_reg >= FULL_THRESHOLD);
assign empty = (count_reg == 0);

// ============================================================================
// Assertions for simulation
// ============================================================================
`ifdef SIMULATION
always @(posedge clk) begin
    if (wr_en && (count_reg >= DEPTH)) begin
        $display("WARNING: Input buffer overflow at time %0t", $time);
    end
end
`endif

endmodule
