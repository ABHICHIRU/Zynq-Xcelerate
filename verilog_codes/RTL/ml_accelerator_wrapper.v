`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - ML Accelerator Wrapper
// AXI Master for DRAM access to model weights
// ============================================================================

module ml_accelerator_wrapper #(
    parameter BASE_ADDR = 32'h40000000
)(
    input  wire              clk,
    input  wire              rst_n,
    
    // Configuration
    input  wire [31:0]      model_base_addr,
    input  wire [15:0]      model_size,
    input  wire              load_model,
    
    // AXI Master Interface (to DDR)
    output wire [31:0]      m_axi_araddr,
    output wire [7:0]       m_axi_arlen,
    output wire [2:0]       m_axi_arsize,
    output wire [1:0]       m_axi_arburst,
    output wire             m_axi_arvalid,
    input  wire             m_axi_arready,
    input  wire [31:0]      m_axi_rdata,
    input  wire [1:0]       m_axi_rresp,
    input  wire             m_axi_rvalid,
    output wire             m_axi_rready,
    
    // Local Memory Interface
    output reg  [15:0]      mem_addr,
    output reg              mem_we,
    output reg  [31:0]      mem_wdata,
    input  wire [31:0]      mem_rdata,
    output reg              mem_req,
    input  wire             mem_ack,
    
    // Status
    output reg              load_complete,
    output reg  [15:0]      load_progress
);

// ============================================================================
// State Machine
// ============================================================================
typedef enum logic [2:0] {
    IDLE       = 3'b000,
    INIT_READ  = 3'b001,
    WAIT_READY = 3'b010,
    WRITE_MEM  = 3'b011,
    INCREMENT  = 3'b100,
    COMPLETE   = 3'b101
} state_t;

state_t state, next_state;

// ============================================================================
// Internal Counters
// ============================================================================
reg [15:0] word_count;
reg [15:0] total_words;

// ============================================================================
// State Machine Logic
// ============================================================================
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        state <= IDLE;
        load_complete <= 0;
        load_progress <= 0;
        mem_we <= 0;
        mem_req <= 0;
        mem_wdata <= 0;
        word_count <= 0;
        total_words <= 0;
    end else begin
        state <= next_state;
        
        case (next_state)
            IDLE: begin
                load_complete <= 0;
                load_progress <= 0;
                mem_we <= 0;
                mem_req <= 0;
                word_count <= 0;
                if (load_model) begin
                    total_words <= model_size;
                end
            end
            
            INIT_READ: begin
                mem_req <= 1;
            end
            
            WRITE_MEM: begin
                mem_addr <= word_count;
                mem_wdata <= m_axi_rdata;
                mem_we <= 1;
                mem_req <= 0;
            end
            
            INCREMENT: begin
                mem_we <= 0;
                word_count <= word_count + 1;
                load_progress <= (word_count * 100) / total_words;
            end
            
            COMPLETE: begin
                load_complete <= 1;
                load_progress <= 16'hFFFF;
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
            if (load_model) begin
                next_state = INIT_READ;
            end
        end
        
        INIT_READ: begin
            next_state = WAIT_READY;
        end
        
        WAIT_READY: begin
            if (m_axi_arvalid && m_axi_arready) begin
                next_state = WRITE_MEM;
            end
        end
        
        WRITE_MEM: begin
            next_state = INCREMENT;
        end
        
        INCREMENT: begin
            if (word_count >= total_words) begin
                next_state = COMPLETE;
            end else begin
                next_state = INIT_READ;
            end
        end
        
        COMPLETE: begin
            next_state = IDLE;
        end
    endcase
end

// ============================================================================
// AXI Read Address Channel
// ============================================================================
assign m_axi_araddr = model_base_addr + (word_count * 4);
assign m_axi_arlen = 0;
assign m_axi_arsize = 3'b010;  // 4 bytes
assign m_axi_arburst = 2'b01;
assign m_axi_arvalid = (state == WAIT_READY);
assign m_axi_rready = (state == WRITE_MEM);

endmodule
