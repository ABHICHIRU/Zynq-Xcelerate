`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Threat Detector Testbench
// ============================================================================

module tb_threat_detector;

parameter DATA_WIDTH = 8;
parameter INPUT_LENGTH = 512;

reg clk;
reg rst_n;
reg valid_in;
reg [DATA_WIDTH-1:0] i_data;
reg [DATA_WIDTH-1:0] q_data;
wire valid_out;
wire [7:0] threat_prob;
wire is_threat;

threat_detector_rtl uut (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(valid_in),
    .i_data(i_data),
    .q_data(q_data),
    .valid_out(valid_out),
    .threat_prob(threat_prob),
    .is_threat(is_threat)
);

always #5 clk = ~clk;

integer sample_count;
reg [15:0] test_pattern;

initial begin
    $display("========================================");
    $display("Threat Detector Testbench");
    $display("========================================");
    
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    i_data = 0;
    q_data = 0;
    sample_count = 0;
    
    #20 rst_n = 1;
    #20;
    
    $display("\n[Test 1] Benign signal (low amplitude)...");
    test_pattern = 16'h0040;
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = test_pattern[7:0] + sample_count[7:0];
        q_data = test_pattern[7:0] + sample_count[7:0];
    end
    @(posedge clk);
    valid_in = 0;
    
    #100;
    $display("Result: threat_prob=%d, is_threat=%b", threat_prob, is_threat);
    
    $display("\n[Test 2] Threat signal (high amplitude)...");
    test_pattern = 16'h00C0;
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = test_pattern[7:0];
        q_data = test_pattern[7:0];
    end
    @(posedge clk);
    valid_in = 0;
    
    #100;
    $display("Result: threat_prob=%d, is_threat=%b", threat_prob, is_threat);
    
    $display("\n[Test 3] Jammer-like signal (noise pattern)...");
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = $random;
        q_data = $random;
    end
    @(posedge clk);
    valid_in = 0;
    
    #100;
    $display("Result: threat_prob=%d, is_threat=%b", threat_prob, is_threat);
    
    #100;
    
    $display("\n========================================");
    $display("Testbench Complete");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_threat_detector.vcd");
    $dumpvars(0, tb_threat_detector);
end

endmodule
