`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Input Buffer Testbench
// ============================================================================

module tb_input_buffer;

parameter DATA_WIDTH = 16;
parameter ADDR_WIDTH = 11;
parameter DEPTH = 2048;

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
wire overflow_error;

input_buffer_ram uut (
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
    .overflow_error(overflow_error)
);

always #5 clk = ~clk;

initial begin
    $display("========================================");
    $display("Input Buffer RAM Testbench");
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
    
    $display("\n[Test 1] Write 10 samples...");
    for (integer i = 0; i < 10; i = i + 1) begin
        @(posedge clk);
        data_in = i;
        wr_addr = i;
        wr_en = 1;
    end
    @(posedge clk);
    wr_en = 0;
    
    $display("Count after write: %d", count);
    $display("Full: %b, Empty: %b", full, empty);
    
    #50;
    
    $display("\n[Test 2] Read 5 samples...");
    for (integer i = 0; i < 5; i = i + 1) begin
        @(posedge clk);
        rd_addr = i;
        rd_en = 1;
        @(posedge clk);
        $display("Read[%d] = %d", i, data_out);
    end
    @(posedge clk);
    rd_en = 0;
    
    $display("Count after read: %d", count);
    
    #50;
    
    $display("\n[Test 3] Overflow test...");
    for (integer i = 0; i < DEPTH + 10; i = i + 1) begin
        @(posedge clk);
        data_in = i[DATA_WIDTH-1:0];
        wr_addr = i[ADDR_WIDTH-1:0];
        wr_en = 1;
    end
    @(posedge clk);
    wr_en = 0;
    
    $display("Final count: %d", count);
    $display("Overflow error: %b", overflow_error);
    
    #100;
    
    $display("\n========================================");
    $display("Testbench Complete");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_input_buffer.vcd");
    $dumpvars(0, tb_input_buffer);
end

endmodule
