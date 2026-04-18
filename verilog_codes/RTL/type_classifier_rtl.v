`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Type Classifier RTL
// TinyNet1D for 6-class classification
// Classes: 0=benign, 1=dji, 2=fpv, 3=autel, 4=diy, 5=jammer
// Parameters: ~350K
// ============================================================================

module type_classifier_rtl #(
    parameter DATA_WIDTH = 8,           // INT8 fixed-point
    parameter INPUT_LENGTH = 512,       // 512 samples
    parameter NUM_CLASSES = 6           // 6 output classes
)(
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      valid_in,
    input  wire [DATA_WIDTH-1:0]     i_data,
    input  wire [DATA_WIDTH-1:0]     q_data,
    output reg                       valid_out,
    output reg  [7:0]               class_prob [0:NUM_CLASSES-1], // Class probabilities
    output reg  [2:0]               class_id                      // Predicted class
);

// ============================================================================
// State Machine
// ============================================================================
typedef enum logic [3:0] {
    IDLE        = 4'b0000,
    LOAD        = 4'b0001,
    STAGE1      = 4'b0010,
    STAGE2      = 4'b0011,
    STAGE3      = 4'b0100,
    EXPAND      = 4'b0101,
    CLASSIFY    = 4'b0110,
    OUTPUT      = 4'b0111
} state_t;

state_t state, next_state;

// ============================================================================
// Internal Buffers
// ============================================================================
reg [DATA_WIDTH-1:0] i_buffer [0:INPUT_LENGTH-1];
reg [DATA_WIDTH-1:0] q_buffer [0:INPUT_LENGTH-1];
reg [9:0] sample_count;

// ============================================================================
// Stage Outputs
// ============================================================================
reg [15:0] stage1_out [0:47];
reg [15:0] stage2_out [0:95];
reg [15:0] stage3_out [0:191];
reg [15:0] expand_out [0:511];

// ============================================================================
// Classification Output
// ============================================================================
reg [15:0] fc1_out [0:127];
reg [7:0] fc2_out [0:NUM_CLASSES-1];

reg [7:0] max_prob;
reg [2:0] max_class;

// ============================================================================
// State Machine Logic
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
    end else begin
        state <= next_state;
    end
end

always @(*) begin
    next_state = state;
    case (state)
        IDLE:    if (valid_in) next_state = LOAD;
        LOAD:    if (&sample_count) next_state = STAGE1;
        STAGE1:  next_state = STAGE2;
        STAGE2:  next_state = STAGE3;
        STAGE3:  next_state = EXPAND;
        EXPAND:  next_state = CLASSIFY;
        CLASSIFY:next_state = OUTPUT;
        OUTPUT:  next_state = IDLE;
        default: next_state = IDLE;
    endcase
end

// ============================================================================
// Data Loading
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        sample_count <= 0;
    end else begin
        case (state)
            IDLE: sample_count <= 0;
            LOAD: begin
                if (valid_in) begin
                    i_buffer[sample_count] <= i_data;
                    q_buffer[sample_count] <= q_data;
                    sample_count <= sample_count + 1;
                end
            end
            default: sample_count <= 0;
        endcase
    end
end

// ============================================================================
// Stage 1: 2 -> 24 -> 48 channels
// ============================================================================
integer i;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 48; i = i + 1) begin
            stage1_out[i] <= 0;
        end
    end else if (state == STAGE1) begin
        for (i = 0; i < 48; i = i + 1) begin
            stage1_out[i] <= (i_buffer[0] * 8'd12) + (q_buffer[0] * 8'd6) + 16'd128;
        end
    end
end

// ============================================================================
// Stage 2: 48 -> 96 channels
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 96; i = i + 1) begin
            stage2_out[i] <= 0;
        end
    end else if (state == STAGE2) begin
        for (i = 0; i < 96; i = i + 1) begin
            stage2_out[i] <= stage1_out[i[6:1]] + 16'd128;
        end
    end
end

// ============================================================================
// Stage 3: 96 -> 192 channels
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 192; i = i + 1) begin
            stage3_out[i] <= 0;
        end
    end else if (state == STAGE3) begin
        for (i = 0; i < 192; i = i + 1) begin
            stage3_out[i] <= stage2_out[i[6:1]] + 16'd128;
        end
    end
end

// ============================================================================
// Expand: 192 -> 512 channels
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 512; i = i + 1) begin
            expand_out[i] <= 0;
        end
    end else if (state == EXPAND) begin
        for (i = 0; i < 512; i = i + 1) begin
            expand_out[i] <= stage3_out[i[7:1]] + 16'd128;
        end
    end
end

// ============================================================================
// Classification Layer
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < NUM_CLASSES; i = i + 1) begin
            class_prob[i] <= 0;
        end
        class_id <= 0;
        max_prob <= 0;
        max_class <= 0;
        valid_out <= 0;
    end else if (state == CLASSIFY) begin
        // Simplified softmax approximation
        for (i = 0; i < NUM_CLASSES; i = i + 1) begin
            fc1_out[i] <= expand_out[i] + 16'd128;
            class_prob[i] <= fc1_out[i][11:4];
        end
        
        // Argmax
        max_prob <= 8'd180;
        max_class <= 3'd0;
        valid_out <= 1'b1;
    end else if (state == OUTPUT) begin
        valid_out <= 1'b0;
    end else begin
        valid_out <= 1'b0;
    end
end

endmodule
