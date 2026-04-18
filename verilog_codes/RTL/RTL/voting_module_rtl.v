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
    parameter TYPE_WEIGHT = 3,         // Type classifier weight
    parameter THREAT_WEIGHT = 4,       // Threat detector weight
    parameter JAMMER_WEIGHT = 3        // Jammer detector weight
)(
    input  wire              clk,
    input  wire              rst_n,
    input  wire              valid_in,
    
    // Threat Detector Input
    input  wire [7:0]       threat_prob,
    input  wire             threat_valid,
    
    // Type Classifier Input
    input  wire [7:0]       type_prob [0:5],  // 6 class probabilities
    input  wire [2:0]       type_id,
    input  wire             type_valid,
    
    // Jammer Detector Input
    input  wire [7:0]       jammer_prob,
    input  wire             jammer_valid,
    
    // Final Decision Output
    output reg              valid_out,
    output reg              is_threat,
    output reg  [2:0]       threat_type,       // 0=benign, 1=dji, 2=fpv, 3=autel, 4=diy, 5=jammer
    output reg              jammer_flag,
    output reg  [7:0]       confidence,        // Combined confidence score
    output reg  [31:0]      timestamp
);

// ============================================================================
// Internal Signals
// ============================================================================
reg [7:0] weighted_sum;
reg [7:0] type_max_prob;
reg all_valid;
reg [1:0] jammer_priority;

// ============================================================================
// Type Probability Max
// ============================================================================
integer i;
always @(*) begin
    type_max_prob = type_prob[0];
    for (i = 1; i < 6; i = i + 1) begin
        if (type_prob[i] > type_max_prob) begin
            type_max_prob = type_prob[i];
        end
    end
end

// ============================================================================
// Validity Check
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        all_valid <= 0;
    end else begin
        all_valid <= threat_valid && type_valid && jammer_valid;
    end
end

// ============================================================================
// Weighted Confidence Calculation
// ============================================================================
always @(*) begin
    weighted_sum = (threat_prob * THREAT_WEIGHT +
                   type_max_prob * TYPE_WEIGHT +
                   jammer_prob * JAMMER_WEIGHT) / (THREAT_WEIGHT + TYPE_WEIGHT + JAMMER_WEIGHT);
end

// ============================================================================
// Voting Logic
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        is_threat <= 0;
        threat_type <= 0;
        jammer_flag <= 0;
        confidence <= 0;
        valid_out <= 0;
        timestamp <= 0;
    end else if (valid_in && all_valid) begin
        valid_out <= 1'b1;
        timestamp <= timestamp + 1;
        
        // Strategy 1: Threat + Type
        if (threat_prob > THREAT_THRESHOLD) begin
            is_threat <= 1'b1;
            threat_type <= type_id;
            confidence <= weighted_sum;
        end else begin
            is_threat <= 1'b0;
            threat_type <= 3'd0;  // Benign
            confidence <= type_max_prob;
        end
        
        // Strategy 2: Threat + Jammer Confirmation
        if (threat_prob > THREAT_THRESHOLD && jammer_prob > JAMMER_THRESHOLD) begin
            jammer_flag <= 1'b1;
            jammer_priority <= 2'b11;  // Highest priority
        end else if (jammer_prob > JAMMER_THRESHOLD) begin
            jammer_flag <= 1'b1;
            jammer_priority <= 2'b10;  // Medium priority
        end else begin
            jammer_flag <= 1'b0;
            jammer_priority <= 2'b00;
        end
    end else begin
        valid_out <= 1'b0;
    end
end

endmodule
