`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - AXI-Lite Control Registers
// Memory-mapped registers for control and configuration
// ============================================================================

module control_registers #(
    parameter BASE_ADDR = 32'h40000000
)(
    input  wire              s_axi_aclk,
    input  wire              s_axi_aresetn,
    
    // AXI-Lite Slave Interface
    input  wire [31:0]      s_axi_awaddr,
    input  wire [2:0]       s_axi_awprot,
    input  wire             s_axi_awvalid,
    output wire             s_axi_awready,
    
    input  wire [31:0]      s_axi_wdata,
    input  wire [3:0]       s_axi_wstrb,
    input  wire             s_axi_wvalid,
    output wire             s_axi_wready,
    
    output wire [1:0]      s_axi_bresp,
    output wire             s_axi_bvalid,
    input  wire             s_axi_bready,
    
    input  wire [31:0]      s_axi_araddr,
    input  wire [2:0]       s_axi_arprot,
    input  wire             s_axi_arvalid,
    output wire             s_axi_arready,
    
    output wire [31:0]      s_axi_rdata,
    output wire [1:0]       s_axi_rresp,
    output wire             s_axi_rvalid,
    input  wire             s_axi_rready,
    
    // Control Outputs
    output reg  [31:0]      control_reg,
    output reg  [31:0]      status_reg,
    output reg  [31:0]      model_addr_reg,
    output reg  [31:0]      threshold_reg
);

// ============================================================================
// Register Addresses
// ============================================================================
localparam ADDR_CONTROL    = 4'h0;
localparam ADDR_STATUS     = 4'h4;
localparam ADDR_MODEL_ADDR = 4'h8;
localparam ADDR_THRESHOLD  = 4'hC;
localparam ADDR_VERSION    = 4'h10;

// ============================================================================
// AXI Handshake Signals
// ============================================================================
reg aw_en;
reg [31:0] aw_addr_reg;
reg w_ready;

// Write address channel
assign s_axi_awready = ~aw_en && w_ready;
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        aw_en <= 0;
        aw_addr_reg <= 0;
    end else if (s_axi_awvalid && s_axi_awready) begin
        aw_en <= 1;
        aw_addr_reg <= s_axi_awaddr;
    end else if (s_axi_bvalid && s_axi_bready) begin
        aw_en <= 0;
    end
end

// Write data channel
assign s_axi_wready = ~aw_en;
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        w_ready <= 1;
    end else begin
        w_ready <= ~s_axi_wvalid || (s_axi_wvalid && s_axi_awvalid);
    end
end

// Write response
reg b_valid;
assign s_axi_bvalid = b_valid;
assign s_axi_bresp = 2'b00;  // OKAY

always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        b_valid <= 0;
    end else if (s_axi_wvalid && s_axi_wready) begin
        b_valid <= 1;
    end else if (s_axi_bready && s_axi_bvalid) begin
        b_valid <= 0;
    end
end

// ============================================================================
// Register Write Logic
// ============================================================================
always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        control_reg <= 32'h00000001;  // Enable by default
        status_reg <= 32'h00000000;
        model_addr_reg <= 32'h00000000;
        threshold_reg <= 32'h00B400B4; // Default thresholds: 180/180/180
    end else if (s_axi_wvalid && s_axi_wready) begin
        case (aw_addr_reg[5:2])
            ADDR_CONTROL: begin
                if (s_axi_wstrb[0]) control_reg[7:0] <= s_axi_wdata[7:0];
                if (s_axi_wstrb[1]) control_reg[15:8] <= s_axi_wdata[15:8];
                if (s_axi_wstrb[2]) control_reg[23:16] <= s_axi_wdata[23:16];
                if (s_axi_wstrb[3]) control_reg[31:24] <= s_axi_wdata[31:24];
            end
            ADDR_STATUS: begin
                if (s_axi_wstrb[0]) status_reg[7:0] <= s_axi_wdata[7:0];
            end
            ADDR_MODEL_ADDR: begin
                model_addr_reg <= s_axi_wdata;
            end
            ADDR_THRESHOLD: begin
                threshold_reg <= s_axi_wdata;
            end
        endcase
    end
end

// ============================================================================
// AXI Read Channel
// ============================================================================
reg [31:0] rdata;
reg r_valid;

assign s_axi_arready = ~r_valid;
assign s_axi_rvalid = r_valid;
assign s_axi_rdata = rdata;
assign s_axi_rresp = 2'b00;

always @(posedge s_axi_aclk) begin
    if (!s_axi_aresetn) begin
        r_valid <= 0;
        rdata <= 0;
    end else if (s_axi_arvalid && s_axi_arready) begin
        r_valid <= 1;
        case (s_axi_araddr[5:2])
            ADDR_CONTROL:    rdata <= control_reg;
            ADDR_STATUS:     rdata <= status_reg;
            ADDR_MODEL_ADDR: rdata <= model_addr_reg;
            ADDR_THRESHOLD:  rdata <= threshold_reg;
            ADDR_VERSION:    rdata <= 32'h00030000;  // Version 3.0
            default:         rdata <= 0;
        endcase
    end else if (s_axi_rready && s_axi_rvalid) begin
        r_valid <= 0;
    end
end

endmodule
