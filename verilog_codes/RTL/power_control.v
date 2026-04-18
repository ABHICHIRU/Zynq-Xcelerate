`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - SPST Power Control
// Power domain management with soft-start and sequencing
// ============================================================================

module power_control (
    input  wire              clk,
    input  wire              rst_n,
    
    // Power enable signals
    input  wire              pwr_enable,
    input  wire              pwr_lna_req,      // Request LNA power
    input  wire              pwr_adc_req,      // Request ADC power
    input  wire              pwr_ml_req,       // Request ML accelerator power
    input  wire              pwr_ddr_req,      // Request DDR power
    
    // Thermal shutdown
    input  wire              thermal_shutdown,
    
    // SPST Power Enable Outputs
    output reg               pwr_lna_en,
    output reg               pwr_adc_en,
    output reg               pwr_ml_en,
    output reg               pwr_ddr_en,
    
    // Power good signals
    input  wire              pwr_lna_pgood,
    input  wire              pwr_adc_pgood,
    input  wire              pwr_ml_pgood,
    input  wire              pwr_ddr_pgood,
    
    // Status
    output reg  [3:0]        pwr_status,        // Power rail status
    output reg               pwr_ready,
    output reg               pwr_fault
);

// ============================================================================
// State Machine
// ============================================================================
typedef enum logic [3:0] {
    PWR_OFF       = 4'b0000,
    PWR_SOFT_START= 4'b0001,
    PWR_SEQ_1     = 4'b0010,
    PWR_SEQ_2     = 4'b0011,
    PWR_SEQ_3     = 4'b0100,
    PWR_SEQ_4     = 4'b0101,
    PWR_ON        = 4'b0110,
    PWR_FAULT     = 4'b0111,
    PWR_SHUTDOWN  = 4'b1000
} power_state_t;

power_state_t state, next_state;

// ============================================================================
// Soft-start Counter
// ============================================================================
reg [15:0] soft_start_cnt;
reg [3:0] seq_cnt;

localparam SOFT_START_TIME = 16'd1000;  // ~1ms at 100MHz
localparam SEQ_DELAY = 4'd5;            // ~50ns between enables

always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        soft_start_cnt <= 0;
        seq_cnt <= 0;
    end else begin
        case (state)
            PWR_SOFT_START: begin
                if (soft_start_cnt < SOFT_START_TIME) begin
                    soft_start_cnt <= soft_start_cnt + 1;
                end
            end
            
            PWR_SEQ_1, PWR_SEQ_2, PWR_SEQ_3, PWR_SEQ_4: begin
                if (seq_cnt < SEQ_DELAY) begin
                    seq_cnt <= seq_cnt + 1;
                end else begin
                    seq_cnt <= 0;
                end
            end
            
            default: begin
                soft_start_cnt <= 0;
                seq_cnt <= 0;
            end
        endcase
    end
end

// ============================================================================
// State Machine Logic
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= PWR_OFF;
        pwr_ready <= 0;
        pwr_fault <= 0;
        pwr_lna_en <= 0;
        pwr_adc_en <= 0;
        pwr_ml_en <= 0;
        pwr_ddr_en <= 0;
        pwr_status <= 4'h0;
    end else begin
        state <= next_state;
        
        case (next_state)
            PWR_OFF: begin
                pwr_ready <= 0;
                pwr_fault <= 0;
                pwr_lna_en <= 0;
                pwr_adc_en <= 0;
                pwr_ml_en <= 0;
                pwr_ddr_en <= 0;
                pwr_status <= 4'h0;
            end
            
            PWR_SOFT_START: begin
                pwr_status <= 4'h1;
            end
            
            PWR_SEQ_1: begin
                pwr_status <= 4'h2;
                if (seq_cnt >= SEQ_DELAY) begin
                    pwr_ddr_en <= 1;  // DDR first (reference for others)
                end
            end
            
            PWR_SEQ_2: begin
                pwr_status <= 4'h3;
                if (seq_cnt >= SEQ_DELAY) begin
                    pwr_adc_en <= 1;
                end
            end
            
            PWR_SEQ_3: begin
                pwr_status <= 4'h4;
                if (seq_cnt >= SEQ_DELAY) begin
                    pwr_ml_en <= 1;
                end
            end
            
            PWR_SEQ_4: begin
                pwr_status <= 4'h5;
                if (seq_cnt >= SEQ_DELAY) begin
                    pwr_lna_en <= 1;
                end
            end
            
            PWR_ON: begin
                pwr_ready <= 1;
                pwr_status <= 4'hF;
            end
            
            PWR_FAULT: begin
                pwr_ready <= 0;
                pwr_fault <= 1;
                pwr_status <= 4'hA;
            end
            
            PWR_SHUTDOWN: begin
                pwr_ready <= 0;
                pwr_status <= 4'h8;
            end
        endcase
    end
end

// ============================================================================
// State Transitions
// ============================================================================
always @(*) begin
    next_state = state;
    
    case (state)
        PWR_OFF: begin
            if (pwr_enable) begin
                next_state = PWR_SOFT_START;
            end
        end
        
        PWR_SOFT_START: begin
            if (thermal_shutdown) begin
                next_state = PWR_FAULT;
            end else if (soft_start_cnt >= SOFT_START_TIME) begin
                next_state = PWR_SEQ_1;
            end
        end
        
        PWR_SEQ_1: begin
            if (thermal_shutdown) begin
                next_state = PWR_FAULT;
            end else if (seq_cnt >= SEQ_DELAY) begin
                next_state = PWR_SEQ_2;
            end
        end
        
        PWR_SEQ_2: begin
            if (thermal_shutdown) begin
                next_state = PWR_FAULT;
            end else if (seq_cnt >= SEQ_DELAY) begin
                next_state = PWR_SEQ_3;
            end
        end
        
        PWR_SEQ_3: begin
            if (thermal_shutdown) begin
                next_state = PWR_FAULT;
            end else if (seq_cnt >= SEQ_DELAY) begin
                next_state = PWR_SEQ_4;
            end
        end
        
        PWR_SEQ_4: begin
            if (thermal_shutdown) begin
                next_state = PWR_FAULT;
            end else if (seq_cnt >= SEQ_DELAY) begin
                next_state = PWR_ON;
            end
        end
        
        PWR_ON: begin
            if (thermal_shutdown || !pwr_enable) begin
                next_state = PWR_SHUTDOWN;
            end
        end
        
        PWR_FAULT, PWR_SHUTDOWN: begin
            if (pwr_enable && !thermal_shutdown) begin
                next_state = PWR_SOFT_START;
            end else if (!pwr_enable) begin
                next_state = PWR_OFF;
            end
        end
    endcase
end

// ============================================================================
// Overcurrent Detection (simplified)
// ============================================================================
always @(posedge clk) begin
    if (state == PWR_ON) begin
        if (!pwr_lna_pgood || !pwr_adc_pgood || 
            !pwr_ml_pgood || !pwr_ddr_pgood) begin
            // Power good de-asserted - fault condition
        end
    end
end

endmodule
