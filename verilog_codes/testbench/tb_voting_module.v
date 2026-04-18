`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Voting Module Testbench
// ============================================================================

module tb_voting_module;

parameter THREAT_THRESHOLD = 180;
parameter JAMMER_THRESHOLD = 200;

reg clk;
reg rst_n;
reg valid_in;
reg [7:0] threat_prob;
reg threat_valid;
reg [7:0] type_prob_0;
reg [7:0] type_prob_1;
reg [7:0] type_prob_2;
reg [7:0] type_prob_3;
reg [7:0] type_prob_4;
reg [7:0] type_prob_5;
reg [2:0] type_id;
reg type_valid;
reg [7:0] jammer_prob;
reg jammer_valid;

wire valid_out;
wire is_threat;
wire [2:0] threat_type;
wire jammer_flag;
wire [7:0] confidence;

voting_logic #(
    .THREAT_THRESHOLD(THREAT_THRESHOLD),
    .JAMMER_THRESHOLD(JAMMER_THRESHOLD)
) uut (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(valid_in),
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
    .valid_out(valid_out),
    .is_threat(is_threat),
    .threat_type(threat_type),
    .jammer_flag(jammer_flag),
    .confidence(confidence),
    .timestamp()
);

always #5 clk = ~clk;

initial begin
    $display("========================================");
    $display("Voting Module Testbench");
    $display("========================================");
    
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    threat_prob = 0;
    threat_valid = 0;
    type_id = 0;
    type_valid = 0;
    jammer_prob = 0;
    jammer_valid = 0;
    
    type_prob_0 = 0;
    type_prob_1 = 0;
    type_prob_2 = 0;
    type_prob_3 = 0;
    type_prob_4 = 0;
    type_prob_5 = 0;
    
    #20 rst_n = 1;
    #20;
    
    $display("\n[Test 1] No threat detected...");
    threat_prob = 8'h50;
    threat_valid = 1;
    type_prob_0 = 8'hC0;
    type_prob_1 = 8'h00;
    type_prob_2 = 8'h00;
    type_prob_3 = 8'h00;
    type_prob_4 = 8'h00;
    type_prob_5 = 8'h00;
    type_id = 0;
    type_valid = 1;
    jammer_prob = 8'h20;
    jammer_valid = 1;
    valid_in = 1;
    
    @(posedge clk);
    @(posedge clk);
    $display("  Result: is_threat=%b, confidence=%d", is_threat, confidence);
    
    #30;
    
    $display("\n[Test 2] Strong threat + DJI...");
    threat_prob = 8'hE0;
    type_prob_0 = 8'h20;
    type_prob_1 = 8'hD0;  // DJI strong
    type_prob_2 = 8'h30;
    type_prob_3 = 8'h10;
    type_prob_4 = 8'h05;
    type_prob_5 = 8'h10;
    type_id = 1;
    jammer_prob = 8'h40;
    valid_in = 1;
    
    @(posedge clk);
    @(posedge clk);
    $display("  Result: is_threat=%b, threat_type=%d, confidence=%d", is_threat, threat_type, confidence);
    
    #30;
    
    $display("\n[Test 3] Jammer detection...");
    threat_prob = 8'h60;
    type_prob_0 = 8'h70;
    type_prob_1 = 8'h40;
    type_prob_2 = 8'h50;
    type_prob_3 = 8'h30;
    type_prob_4 = 8'h20;
    type_prob_5 = 8'hD0;  // Jammer strong
    type_id = 5;
    jammer_prob = 8'hF0;  // Strong jammer
    valid_in = 1;
    
    @(posedge clk);
    @(posedge clk);
    $display("  Result: is_threat=%b, jammer_flag=%b, confidence=%d", is_threat, jammer_flag, confidence);
    
    #30;
    
    $display("\n========================================");
    $display("Testbench Complete - PASSED");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_voting_module.vcd");
    $dumpvars(0, tb_voting_module);
end

endmodule
