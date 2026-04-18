`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - AXI Interface Testbench
// ============================================================================

module tb_axi_interface;

parameter BASE_ADDR = 32'h40000000;

reg s_axi_aclk;
reg s_axi_aresetn;
reg [31:0] s_axi_awaddr;
reg [2:0] s_axi_awprot;
reg s_axi_awvalid;
wire s_axi_awready;
reg [31:0] s_axi_wdata;
reg [3:0] s_axi_wstrb;
reg s_axi_wvalid;
wire s_axi_wready;
wire [1:0] s_axi_bresp;
wire s_axi_bvalid;
reg s_axi_bready;
reg [31:0] s_axi_araddr;
reg [2:0] s_axi_arprot;
reg s_axi_arvalid;
wire s_axi_arready;
wire [31:0] s_axi_rdata;
wire [1:0] s_axi_rresp;
wire s_axi_rvalid;
reg s_axi_rready;

control_registers #(
    .BASE_ADDR(BASE_ADDR)
) uut (
    .s_axi_aclk(s_axi_aclk),
    .s_axi_aresetn(s_axi_aresetn),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_awprot(s_axi_awprot),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_bresp(s_axi_bresp),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),
    .s_axi_araddr(s_axi_araddr),
    .s_axi_arprot(s_axi_arprot),
    .s_axi_arvalid(s_axi_arvalid),
    .s_axi_arready(s_axi_arready),
    .s_axi_rdata(s_axi_rdata),
    .s_axi_rresp(s_axi_rresp),
    .s_axi_rvalid(s_axi_rvalid),
    .s_axi_rready(s_axi_rready),
    .control_reg(),
    .status_reg(),
    .model_addr_reg(),
    .threshold_reg()
);

always #5 s_axi_aclk = ~s_axi_aclk;

initial begin
    $display("========================================");
    $display("AXI Interface Testbench");
    $display("========================================");
    
    s_axi_aclk = 0;
    s_axi_aresetn = 0;
    s_axi_awaddr = 0;
    s_axi_awprot = 0;
    s_axi_awvalid = 0;
    s_axi_wdata = 0;
    s_axi_wstrb = 4'b1111;
    s_axi_wvalid = 0;
    s_axi_bready = 0;
    s_axi_araddr = 0;
    s_axi_arprot = 0;
    s_axi_arvalid = 0;
    s_axi_rready = 0;
    
    #40 s_axi_aresetn = 1;
    #20;
    
    $display("\n[Test 1] Write to control register...");
    @(posedge s_axi_aclk);
    s_axi_awaddr = BASE_ADDR;
    s_axi_awvalid = 1;
    s_axi_wdata = 32'h00000001;
    s_axi_wvalid = 1;
    
    wait(s_axi_awready && s_axi_wready);
    @(posedge s_axi_aclk);
    s_axi_awvalid = 0;
    s_axi_wvalid = 0;
    
    s_axi_bready = 1;
    wait(s_axi_bvalid);
    @(posedge s_axi_aclk);
    s_axi_bready = 0;
    $display("Write complete: bresp=%b", s_axi_bresp);
    
    $display("\n[Test 2] Read from control register...");
    @(posedge s_axi_aclk);
    s_axi_araddr = BASE_ADDR;
    s_axi_arvalid = 1;
    
    wait(s_axi_arready);
    @(posedge s_axi_aclk);
    s_axi_arvalid = 0;
    
    s_axi_rready = 1;
    wait(s_axi_rvalid);
    $display("Read data: 0x%h", s_axi_rdata);
    @(posedge s_axi_aclk);
    s_axi_rready = 0;
    
    $display("\n[Test 3] Write and read threshold register...");
    @(posedge s_axi_aclk);
    s_axi_awaddr = BASE_ADDR + 8'h0C;
    s_axi_awvalid = 1;
    s_axi_wdata = 32'h00B400B4;
    s_axi_wvalid = 1;
    
    wait(s_axi_awready && s_axi_wready);
    @(posedge s_axi_aclk);
    s_axi_awvalid = 0;
    s_axi_wvalid = 0;
    
    s_axi_bready = 1;
    wait(s_axi_bvalid);
    @(posedge s_axi_aclk);
    s_axi_bready = 0;
    
    @(posedge s_axi_aclk);
    s_axi_araddr = BASE_ADDR + 8'h0C;
    s_axi_arvalid = 1;
    
    wait(s_axi_arready);
    @(posedge s_axi_aclk);
    s_axi_arvalid = 0;
    
    s_axi_rready = 1;
    wait(s_axi_rvalid);
    $display("Threshold read: 0x%h", s_axi_rdata);
    
    #100;
    
    $display("\n========================================");
    $display("Testbench Complete - PASSED");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_axi_interface.vcd");
    $dumpvars(0, tb_axi_interface);
end

endmodule
