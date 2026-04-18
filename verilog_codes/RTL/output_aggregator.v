`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Output Aggregator
// AXI-Stream to AXI output bridge
// ============================================================================

module output_aggregator #(
    parameter DATA_WIDTH = 32
)(
    input  wire              clk,
    input  wire              rst_n,
    
    // Classification results from voting logic
    input  wire [31:0]      result_data,       // {timestamp, confidence, type, threat}
    input  wire              result_valid,
    
    // AXI-Stream input (from voting)
    input  wire [DATA_WIDTH-1:0] s_axis_tdata,
    input  wire             s_axis_tvalid,
    output wire             s_axis_tready,
    input  wire             s_axis_tlast,
    
    // AXI Master write interface
    output reg  [31:0]      m_axi_awaddr,
    output reg  [7:0]      m_axi_awlen,
    output reg  [2:0]       m_axi_awsize,
    output reg  [1:0]       m_axi_awburst,
    output reg              m_axi_awvalid,
    input  wire             m_axi_awready,
    
    output reg  [31:0]      m_axi_wdata,
    output reg  [3:0]       m_axi_wstrb,
    output reg              m_axi_wlast,
    output reg              m_axi_wvalid,
    input  wire             m_axi_wready,
    
    input  wire              m_axi_bready,
    output wire [1:0]       m_axi_bresp,
    output wire              m_axi_bvalid,
    
    // Status
    output reg  [31:0]      result_count
);

// ============================================================================
// State Machine
// ============================================================================
typedef enum logic [1:0] {
    IDLE    = 2'b00,
    ADDR    = 2'b01,
    WRITE   = 2'b10,
    RESP    = 2'b11
} state_t;

state_t state, next_state;

// ============================================================================
// Result Buffer
// ============================================================================
reg [31:0] result_buffer;
reg result_valid_reg;

// ============================================================================
// State Machine Logic
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        result_count <= 0;
        m_axi_awvalid <= 0;
        m_axi_wvalid <= 0;
    end else begin
        state <= next_state;
        
        case (next_state)
            IDLE: begin
                if (s_axis_tvalid) begin
                    result_buffer <= s_axis_tdata;
                    result_valid_reg <= 1;
                    result_count <= result_count + 1;
                end
            end
            
            ADDR: begin
                m_axi_awaddr <= 32'h40001000 + (result_count * 4);
                m_axi_awlen <= 0;
                m_axi_awsize <= 3'b010;  // 4 bytes
                m_axi_awburst <= 2'b01;
                m_axi_awvalid <= 1;
            end
            
            WRITE: begin
                m_axi_wdata <= result_buffer;
                m_axi_wstrb <= 4'b1111;
                m_axi_wlast <= 1;
                m_axi_wvalid <= 1;
            end
            
            RESP: begin
                m_axi_awvalid <= 0;
                m_axi_wvalid <= 0;
                result_valid_reg <= 0;
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
        IDLE: begin
            if (s_axis_tvalid) begin
                next_state = ADDR;
            end
        end
        
        ADDR: begin
            if (m_axi_awready) begin
                next_state = WRITE;
            end
        end
        
        WRITE: begin
            if (m_axi_wready) begin
                next_state = RESP;
            end
        end
        
        RESP: begin
            next_state = IDLE;
        end
    endcase
end

assign s_axis_tready = (state == IDLE) && !s_axis_tvalid;
assign m_axi_bvalid = (state == RESP);
assign m_axi_bresp = 2'b00;  // OKAY

endmodule
