`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Voting Logic Module
// Combines outputs from 3 detectors with confidence weighting
// Strategy 1: Threat + Type -> Detection + Classification
// Strategy 2: Threat + Jammer -> Confirmation + Jammer Flag
// ============================================================================

module voting_logic #(
    parameter THREAT_THRESHOLD = 180,  // 70% threshold (180/255)
    parameter JAMMER_THRESHOLD = 200,  // 78% threshold
    parameter TYPE_WEIGHT = 3,
    parameter THREAT_WEIGHT = 4,
    parameter JAMMER_WEIGHT = 3
)(
    input  wire              clk,
    input  wire              rst_n,
    input  wire              valid_in,
    
    // Threat Detector Input
    input  wire [7:0]       threat_prob,
    input  wire             threat_valid,
    
    // Type Classifier Input (Flattened)
    input  wire [7:0]       type_prob_0,
    input  wire [7:0]       type_prob_1,
    input  wire [7:0]       type_prob_2,
    input  wire [7:0]       type_prob_3,
    input  wire [7:0]       type_prob_4,
    input  wire [7:0]       type_prob_5,
    input  wire [2:0]       type_id,
    input  wire             type_valid,
    
    // Jammer Detector Input
    input  wire [7:0]       jammer_prob,
    input  wire             jammer_valid,
    
    // Final Decision Output
    output reg              valid_out,
    output reg              is_threat,
    output reg  [2:0]       threat_type,
    output reg              jammer_flag,
    output reg  [7:0]       confidence,
    output reg  [31:0]      timestamp
);

// ============================================================================
// Internal Signals
// ============================================================================
reg [7:0] weighted_sum;
reg [7:0] type_max_prob;
reg all_valid;

// ============================================================================
// Type Probability Max
// ============================================================================
always @(*) begin
    // Find max of 6 type probabilities
    type_max_prob = type_prob_0;
    if (type_prob_1 > type_max_prob) type_max_prob = type_prob_1;
    if (type_prob_2 > type_max_prob) type_max_prob = type_prob_2;
    if (type_prob_3 > type_max_prob) type_max_prob = type_prob_3;
    if (type_prob_4 > type_max_prob) type_max_prob = type_prob_4;
    if (type_prob_5 > type_max_prob) type_max_prob = type_prob_5;
end

// ============================================================================
// Validity Check
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        all_valid <= 1'b0;
    end else begin
        all_valid <= threat_valid && type_valid && jammer_valid;
    end
end

// ============================================================================
// Weighted Confidence Calculation
// ============================================================================
always @(*) begin
    weighted_sum = ((threat_prob * THREAT_WEIGHT) +
                    (type_max_prob * TYPE_WEIGHT) +
                    (jammer_prob * JAMMER_WEIGHT)) / (THREAT_WEIGHT + TYPE_WEIGHT + JAMMER_WEIGHT);
end

// ============================================================================
// Voting Decision Logic
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        valid_out <= 1'b0;
        is_threat <= 1'b0;
        threat_type <= 3'b000;
        jammer_flag <= 1'b0;
        confidence <= 8'h00;
        timestamp <= 32'h00000000;
    end else if (valid_in && all_valid) begin
        valid_out <= 1'b1;
        
        // Threat decision based on weighted sum
        if (weighted_sum >= THREAT_THRESHOLD) begin
            is_threat <= 1'b1;
            threat_type <= type_id;
        end else begin
            is_threat <= 1'b0;
            threat_type <= 3'b000;
        end
        
        // Jammer flag decision
        if (jammer_prob >= JAMMER_THRESHOLD) begin
            jammer_flag <= 1'b1;
        end else begin
            jammer_flag <= 1'b0;
        end
        
        confidence <= weighted_sum;
        timestamp <= 32'h00000000;
    end else begin
        valid_out <= 1'b0;
    end
end

endmodule
