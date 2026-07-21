`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - AXI to AXI-Stream Bridge
// Converts AXI memory-mapped interface to streaming data
// ============================================================================

module data_input_fifo #(
    parameter DATA_WIDTH = 16,
    parameter ADDR_WIDTH = 11,
    parameter FIFO_DEPTH = 2048
)(
    input  wire              s_axi_aclk,
    input  wire              s_axi_aresetn,
    
    // AXI Slave Interface (from ARM/DDR)
    input  wire [31:0]       s_axi_araddr,
    input  wire [7:0]       s_axi_arlen,
    input  wire [2:0]       s_axi_arsize,
    input  wire [1:0]       s_axi_arburst,
    input  wire             s_axi_arvalid,
    output wire             s_axi_arready,
    output wire [31:0]      s_axi_rdata,
    output wire [1:0]       s_axi_rresp,
    output wire             s_axi_rvalid,
    input  wire             s_axi_rready,
    
    // AXI-Stream Master Interface (to processing)
    output wire [DATA_WIDTH-1:0] m_axis_tdata,
    output wire             m_axis_tvalid,
    input  wire             m_axis_tready,
    output wire             m_axis_tlast,
    output wire             m_axis_tuser,
    
    // Status
    output wire [ADDR_WIDTH:0] fifo_count
);

// ============================================================================
// Internal Signals
// ============================================================================
wire [DATA_WIDTH-1:0] fifo_din;
wire [DATA_WIDTH-1:0] fifo_dout;
wire fifo_wr_en, fifo_rd_en;
wire fifo_full, fifo_empty;

// ============================================================================
// FIFO Instance
// ============================================================================
(* RAM_STYLE = "BLOCK" *)
reg [DATA_WIDTH-1:0] fifo_ram [0:FIFO_DEPTH-1];
reg [ADDR_WIDTH:0] wr_ptr, rd_ptr;
reg [ADDR_WIDTH:0] count_reg;

assign fifo_count = count_reg;
assign fifo_full = (count_reg >= FIFO_DEPTH - 1);
assign fifo_empty = (count_reg == 0);

// Write pointer
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        wr_ptr <= 0;
    end else if (fifo_wr_en && !fifo_full) begin
        fifo_ram[wr_ptr[ADDR_WIDTH-1:0]] <= fifo_din;
        wr_ptr <= wr_ptr + 1;
    end
end

// Read pointer
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        rd_ptr <= 0;
    end else if (fifo_rd_en && !fifo_empty) begin
        rd_ptr <= rd_ptr + 1;
    end
end

// Count
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        count_reg <= 0;
    end else if (fifo_wr_en && !fifo_rd_en && !fifo_full) begin
        count_reg <= count_reg + 1;
    end else if (fifo_rd_en && !fifo_wr_en && !fifo_empty) begin
        count_reg <= count_reg - 1;
    end
end

assign fifo_dout = fifo_ram[rd_ptr[ADDR_WIDTH-1:0]];

// ============================================================================
// AXI Read Channel
// ============================================================================
reg [7:0] beat_count;
reg [2:0] state;

localparam IDLE = 0, READ_BURST = 1, WAIT_LAST = 2;

always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        state <= IDLE;
        beat_count <= 0;
    end else begin
        case (state)
            IDLE: begin
                if (s_axi_arvalid) begin
                    beat_count <= s_axi_arlen;
                    state <= READ_BURST;
                end
            end
            READ_BURST: begin
                if (!fifo_full && beat_count > 0) begin
                    beat_count <= beat_count - 1;
                    if (beat_count == 0) begin
                        state <= IDLE;
                    end
                end
            end
        endcase
    end
end

assign s_axi_arready = (state == IDLE);
assign fifo_wr_en = (state == READ_BURST) && !fifo_full;
assign fifo_din = s_axi_rdata[DATA_WIDTH-1:0];

reg [31:0] rdata_reg;
reg rvalid_reg;
assign s_axi_rdata = rdata_reg;
assign s_axi_rvalid = rvalid_reg;
assign s_axi_rresp = 2'b00;

always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        rvalid_reg <= 0;
        rdata_reg <= 0;
    end else begin
        rvalid_reg <= s_axi_arvalid && (state == IDLE);
        rdata_reg <= {16'b0, fifo_dout};
    end
end

// ============================================================================
// AXI-Stream Output
// ============================================================================
assign m_axis_tdata = fifo_dout;
assign m_axis_tvalid = !fifo_empty;
assign m_axis_tlast = (count_reg == 1) && m_axis_tready;
assign m_axis_tuser = fifo_empty;
assign fifo_rd_en = m_axis_tvalid && m_axis_tready;

endmodule
