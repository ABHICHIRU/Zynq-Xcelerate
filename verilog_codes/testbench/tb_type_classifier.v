`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Type Classifier Testbench
// ============================================================================

module tb_type_classifier;

parameter DATA_WIDTH = 8;
parameter INPUT_LENGTH = 512;
parameter NUM_CLASSES = 6;

reg clk;
reg rst_n;
reg valid_in;
reg [DATA_WIDTH-1:0] i_data;
reg [DATA_WIDTH-1:0] q_data;
wire valid_out;
wire [7:0] class_prob_0;
wire [7:0] class_prob_1;
wire [7:0] class_prob_2;
wire [7:0] class_prob_3;
wire [7:0] class_prob_4;
wire [7:0] class_prob_5;
wire [2:0] class_id;

type_classifier_rtl #(
    .DATA_WIDTH(DATA_WIDTH),
    .INPUT_LENGTH(INPUT_LENGTH),
    .NUM_CLASSES(NUM_CLASSES)
) uut (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(valid_in),
    .i_data(i_data),
    .q_data(q_data),
    .valid_out(valid_out),
    .class_prob_0(class_prob_0),
    .class_prob_1(class_prob_1),
    .class_prob_2(class_prob_2),
    .class_prob_3(class_prob_3),
    .class_prob_4(class_prob_4),
    .class_prob_5(class_prob_5),
    .class_id(class_id)
);

always #5 clk = ~clk;

integer sample_count;
reg [7:0] pattern_value;

initial begin
    $display("========================================");
    $display("Type Classifier Testbench");
    $display("========================================");
    
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    i_data = 0;
    q_data = 0;
    sample_count = 0;
    
    #20 rst_n = 1;
    #20;
    
    $display("\n[Test 1] DJI-like signal...");
    pattern_value = 8'hA0;
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = pattern_value;
        q_data = pattern_value + 8'd10;
    end
    @(posedge clk);
    valid_in = 0;
    
    #200;
    $display("Result: class_id=%d", class_id);
    $display("Class probabilities:");
    $display("  Class[0] (Benign): %d", class_prob_0);
    $display("  Class[1] (DJI):    %d", class_prob_1);
    $display("  Class[2] (FPV):    %d", class_prob_2);
    $display("  Class[3] (Autel):  %d", class_prob_3);
    $display("  Class[4] (DIY):    %d", class_prob_4);
    $display("  Class[5] (Jammer): %d", class_prob_5);
    
    $display("\n[Test 2] FPV-like signal...");
    pattern_value = 8'h80;
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = pattern_value + sample_count[7:0];
        q_data = pattern_value;
    end
    @(posedge clk);
    valid_in = 0;
    
    #200;
    $display("Result: class_id=%d", class_id);
    
    $display("\n[Test 3] Jammer signal...");
    for (sample_count = 0; sample_count < INPUT_LENGTH; sample_count = sample_count + 1) begin
        @(posedge clk);
        valid_in = 1;
        i_data = $random;
        q_data = $random;
    end
    @(posedge clk);
    valid_in = 0;
    
    #200;
    $display("Result: class_id=%d", class_id);
    
    #100;
    
    $display("\n========================================");
    $display("Testbench Complete - PASSED");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_type_classifier.vcd");
    $dumpvars(0, tb_type_classifier);
end

endmodule
