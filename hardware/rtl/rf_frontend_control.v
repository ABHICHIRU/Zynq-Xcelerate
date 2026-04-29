`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - RF Frontend Control
// SPST Switch control for RF frontend (LNA, filters, antenna)
// ============================================================================

module rf_frontend_control (
    input  wire              clk,
    input  wire              rst_n,
    input  wire              enable,
    
    // Control signals from system
    input  wire [1:0]       filter_select,    // 00=2.4GHz, 01=5.8GHz, 10=wideband
    input  wire              lna_enable,
    input  wire              antenna_rx,        // 0=TX, 1=RX
    input  wire              calibration_mode,
    
    // SPST Switch Outputs
    output reg              sw_lna_in,
    output reg              sw_lna_bypass,
    output reg              sw_filter_2g4,
    output reg              sw_filter_5g8,
    output reg              sw_filter_wide,
    output reg              sw_ant_rx,
    output reg              sw_ant_tx,
    output reg              sw_calibration,
    
    // Status
    output reg  [3:0]       frontend_status,
    output reg              frontend_ready
);

// ============================================================================
// State Machine
// ============================================================================
localparam STANDBY   = 3'b000;
localparam INIT      = 3'b001;
localparam CONFIGURE = 3'b010;
localparam ACTIVE    = 3'b011;
localparam CALIBRATE = 3'b100;
localparam ERROR     = 3'b101;

reg [2:0] state, next_state;

// ============================================================================
// Switch Control Logic
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= STANDBY;
        frontend_ready <= 0;
    end else begin
        state <= next_state;
        
        case (next_state)
            STANDBY: begin
                frontend_ready <= 0;
                sw_lna_in <= 0;
                sw_lna_bypass <= 1;
                sw_filter_2g4 <= 0;
                sw_filter_5g8 <= 0;
                sw_filter_wide <= 0;
                sw_ant_rx <= 0;
                sw_ant_tx <= 0;
                sw_calibration <= 0;
                frontend_status <= 4'h0;
            end
            
            INIT: begin
                frontend_ready <= 0;
                frontend_status <= 4'h1;
            end
            
            CONFIGURE: begin
                frontend_ready <= 0;
                frontend_status <= 4'h2;
            end
            
            ACTIVE: begin
                frontend_ready <= 1;
                frontend_status <= 4'h8;
                
                // LNA control
                sw_lna_in <= lna_enable;
                sw_lna_bypass <= ~lna_enable;
                
                // Filter selection
                sw_filter_2g4 <= (filter_select == 2'b00);
                sw_filter_5g8 <= (filter_select == 2'b01);
                sw_filter_wide <= (filter_select == 2'b10);
                
                // Antenna selection
                sw_ant_rx <= antenna_rx;
                sw_ant_tx <= ~antenna_rx;
                
                sw_calibration <= 0;
            end
            
            CALIBRATE: begin
                frontend_ready <= 0;
                frontend_status <= 4'h4;
                sw_lna_in <= 0;
                sw_lna_bypass <= 0;
                sw_filter_2g4 <= 0;
                sw_filter_5g8 <= 0;
                sw_filter_wide <= 0;
                sw_ant_rx <= 0;
                sw_ant_tx <= 0;
                sw_calibration <= 1;
            end
            
            ERROR: begin
                frontend_ready <= 0;
                frontend_status <= 4'hF;
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
        STANDBY: begin
            if (enable) begin
                next_state = INIT;
            end
        end
        
        INIT: begin
            next_state = CONFIGURE;
        end
        
        CONFIGURE: begin
            next_state = ACTIVE;
        end
        
        ACTIVE: begin
            if (calibration_mode) begin
                next_state = CALIBRATE;
            end else if (!enable) begin
                next_state = STANDBY;
            end
        end
        
        CALIBRATE: begin
            if (!calibration_mode) begin
                next_state = ACTIVE;
            end
        end
        
        ERROR: begin
            if (enable) begin
                next_state = INIT;
            end
        end
    endcase
end

endmodule
