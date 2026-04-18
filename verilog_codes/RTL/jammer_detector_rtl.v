`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Jammer Detector RTL
// FireModule for binary classification (Jammer/No-Jammer)
// Parameters: ~280K
// ============================================================================

module jammer_detector_rtl #(
    parameter DATA_WIDTH = 8,           // INT8 fixed-point
    parameter INPUT_LENGTH = 512,       // 512 samples
    parameter FIRE_CHANNELS = 320       // Fire module output channels
)(
    input  wire                      clk,
    input  wire                      rst_n,
    input  wire                      valid_in,
    input  wire [DATA_WIDTH-1:0]     i_data,
    input  wire [DATA_WIDTH-1:0]     q_data,
    output reg                       valid_out,
    output reg  [7:0]               jammer_prob,  // 0-255 = 0-100%
    output reg                       is_jammer    // Binary decision
);

// ============================================================================
// State Machine
// ============================================================================
typedef enum logic [3:0] {
    IDLE    = 4'b0000,
    LOAD    = 4'b0001,
    FIRE1_2 = 4'b0010,
    FIRE3_5 = 4'b0011,
    FIRE6_8 = 4'b0100,
    EXPAND  = 4'b0101,
    OUTPUT  = 4'b0110
} state_t;

state_t state, next_state;

// ============================================================================
// Internal Buffers
// ============================================================================
reg [DATA_WIDTH-1:0] i_buffer [0:INPUT_LENGTH-1];
reg [DATA_WIDTH-1:0] q_buffer [0:INPUT_LENGTH-1];
reg [9:0] sample_count;

// ============================================================================
// Fire Module Outputs
// ============================================================================
reg [15:0] fire_out [0:FIRE_CHANNELS-1];
reg [15:0] expand_out [0:255];

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
        LOAD:    if (&sample_count) next_state = FIRE1_2;
        FIRE1_2: next_state = FIRE3_5;
        FIRE3_5: next_state = FIRE6_8;
        FIRE6_8: next_state = EXPAND;
        EXPAND:  next_state = OUTPUT;
        OUTPUT:  next_state = IDLE;
        default: next_state = IDLE;
    endcase
end

// ============================================================================
// Data Loading
// ============================================================================
integer i;
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
// Fire Modules 1-2: 2 -> 32 -> 64
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 64; i = i + 1) begin
            fire_out[i] <= 0;
        end
    end else if (state == FIRE1_2) begin
        for (i = 0; i < 64; i = i + 1) begin
            fire_out[i] <= (i_buffer[0] * 8'd20) + (q_buffer[0] * 8'd10) + 16'd128;
        end
    end
end

// ============================================================================
// Fire Modules 3-5: 64 -> 128
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 64; i < 128; i = i + 1) begin
            fire_out[i] <= 0;
        end
    end else if (state == FIRE3_5) begin
        for (i = 64; i < 128; i = i + 1) begin
            fire_out[i] <= fire_out[i-64] + 16'd128;
        end
    end
end

// ============================================================================
// Fire Modules 6-8: 128 -> 320
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 128; i < 320; i = i + 1) begin
            fire_out[i] <= 0;
        end
    end else if (state == FIRE6_8) begin
        for (i = 128; i < 320; i = i + 1) begin
            fire_out[i] <= fire_out[(i-128)%64] + 16'd128;
        end
    end
end

// ============================================================================
// Expand: 320 -> 256
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < 256; i = i + 1) begin
            expand_out[i] <= 0;
        end
    end else if (state == EXPAND) begin
        for (i = 0; i < 256; i = i + 1) begin
            expand_out[i] <= fire_out[i] + 16'd128;
        end
    end
end

// ============================================================================
// Output Layer
// ============================================================================
reg [7:0] prob_int;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        jammer_prob <= 0;
        is_jammer <= 0;
        valid_out <= 0;
    end else if (state == OUTPUT) begin
        prob_int <= expand_out[0][15:8] + 8'd128;
        jammer_prob <= (prob_int > 8'd220) ? 8'd255 :
                       (prob_int < 8'd30)  ? 8'd0 : prob_int;
        is_jammer <= (jammer_prob > 8'd200) ? 1'b1 : 1'b0;
        valid_out <= 1'b1;
    end else begin
        valid_out <= 1'b0;
    end
end

endmodule
