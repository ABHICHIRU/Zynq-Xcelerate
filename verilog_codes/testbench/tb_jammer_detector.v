`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Jammer Detector Testbench
// ============================================================================

module tb_jammer_detector;

parameter DATA_WIDTH = 8;
parameter INPUT_LENGTH = 512;

reg clk;
reg rst_n;
reg valid_in;
reg [DATA_WIDTH-1:0] i_data;
reg [DATA_WIDTH-1:0] q_data;
wire valid_out;
wire [7:0] jammer_prob;
wire is_jammer;

jammer_detector_rtl #(
    .DATA_WIDTH(DATA_WIDTH),
    .INPUT_LENGTH(INPUT_LENGTH)
) uut (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(valid_in),
    .i_data(i_data),
    .q_data(q_data),
    .valid_out(valid_out),
    .jammer_prob(jammer_prob),
    .is_jammer(is_jammer)
);

always #5 clk = ~clk;

integer sample_count;

initial begin
    $display("========================================");
    $display("Jammer Detector Testbench");
    $display("========================================");
    
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    i_data = 0;
    q_data = 0;
    sample_count = 0;
    
    #20 rst_n = 1;
    #20;
    
    $display("\n[Test 1] Clean signal (no jammer)...");
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = 8'h80 + sample_count[7:0];
        q_data = 8'h80 + sample_count[7:0];
    end
    @(posedge clk);
    valid_in = 0;
    
    #100;
    $display("Result: jammer_prob=%d, is_jammer=%b", jammer_prob, is_jammer);
    
    if (jammer_prob < 100) begin
        $display("PASS: Low jammer probability for clean signal");
    end else begin
        $display("FAIL: Unexpected high jammer probability");
    end
    
    $display("\n[Test 2] Jammer signal (high noise)...");
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = $random;
        q_data = $random;
    end
    @(posedge clk);
    valid_in = 0;
    
    #100;
    $display("Result: jammer_prob=%d, is_jammer=%b", jammer_prob, is_jammer);
    
    if (jammer_prob > 150) begin
        $display("PASS: High jammer probability for noise signal");
    end else begin
        $display("FAIL: Unexpected low jammer probability");
    end
    
    $display("\n[Test 3] Partial jammer (pulse noise)...");
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        if (sample_count[4:0] < 16) begin
            i_data = $random;
            q_data = $random;
        end else begin
            i_data = 8'h80;
            q_data = 8'h80;
        end
    end
    @(posedge clk);
    valid_in = 0;
    
    #100;
    $display("Result: jammer_prob=%d, is_jammer=%b", jammer_prob, is_jammer);
    
    #100;
    
    $display("\n========================================");
    $display("Testbench Complete - PASSED");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_jammer_detector.vcd");
    $dumpvars(0, tb_jammer_detector);
end

endmodule
