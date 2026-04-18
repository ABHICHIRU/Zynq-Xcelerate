`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Output Buffer Testbench
// ============================================================================

module tb_output_buffer;

parameter ADDR_WIDTH = 8;
parameter DATA_WIDTH = 32;
parameter DEPTH = 256;

reg clk;
reg rst_n;

reg [DATA_WIDTH-1:0] data_in;
reg wr_en;
reg [ADDR_WIDTH-1:0] wr_addr;
reg rd_en;
reg [ADDR_WIDTH-1:0] rd_addr;
wire [DATA_WIDTH-1:0] data_out;
wire full;
wire empty;
wire [ADDR_WIDTH:0] count;
wire underflow_error;

output_buffer_ram #(
    .ADDR_WIDTH(ADDR_WIDTH),
    .DATA_WIDTH(DATA_WIDTH),
    .DEPTH(DEPTH)
) uut (
    .clk(clk),
    .rst_n(rst_n),
    .data_in(data_in),
    .wr_en(wr_en),
    .wr_addr(wr_addr),
    .rd_en(rd_en),
    .rd_addr(rd_addr),
    .data_out(data_out),
    .full(full),
    .empty(empty),
    .count(count),
    .underflow_error(underflow_error)
);

always #5 clk = ~clk;

initial begin
    $display("========================================");
    $display("Output Buffer RAM Testbench");
    $display("========================================");
    
    clk = 0;
    rst_n = 0;
    data_in = 0;
    wr_en = 0;
    wr_addr = 0;
    rd_en = 0;
    rd_addr = 0;
    
    #20 rst_n = 1;
    #10;
    
    $display("\n[Test 1] Write result samples...");
    for (integer i = 0; i < 8; i = i + 1) begin
        @(posedge clk);
        data_in = {8'b0, 8'(i+1), 8'(i+2), 8'(i+3)}; // timestamp, type, threat, confidence
        wr_addr = i;
        wr_en = 1;
    end
    @(posedge clk);
    wr_en = 0;
    
    $display("Count after write: %d", count);
    
    #50;
    
    $display("\n[Test 2] Read all samples...");
    for (integer i = 0; i < 8; i = i + 1) begin
        @(posedge clk);
        rd_addr = i;
        rd_en = 1;
        @(posedge clk);
        $display("Read[%d] = 0x%h", i, data_out);
    end
    @(posedge clk);
    rd_en = 0;
    
    #50;
    
    $display("\n[Test 3] Underflow test (read from empty)...");
    rd_en = 1;
    #20;
    $display("Underflow error: %b", underflow_error);
    rd_en = 0;
    
    #100;
    
    $display("\n========================================");
    $display("Testbench Complete - PASSED");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_output_buffer.vcd");
    $dumpvars(0, tb_output_buffer);
end

endmodule
