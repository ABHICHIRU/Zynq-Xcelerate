`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Integrated System Testbench
// Complete end-to-end system validation
// ============================================================================

module tb_integrated_system;

parameter BASE_ADDR = 32'h40000000;

reg sys_clk_p;
reg sys_clk_n;
reg ml_clk;
reg rst_n;
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

reg [15:0] rf_i_data;
reg [15:0] rf_q_data;
reg rf_valid;
wire rf_ready;

wire [31:0] result_data;
wire result_valid;
reg result_ready;

wire [3:0] status_led;
wire pwr_enable;
reg thermal_shutdown;
wire pwr_lna_en;
wire pwr_adc_en;
wire pwr_ml_en;
wire pwr_ddr_en;

wire sys_clk = sys_clk_p;

top_skyshield_ai_v3 #(
    .BASE_ADDR(BASE_ADDR)
) uut (
    .sys_clk_p(sys_clk_p),
    .sys_clk_n(sys_clk_n),
    .ml_clk(ml_clk),
    .rst_n(rst_n),
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
    .rf_i_data(rf_i_data),
    .rf_q_data(rf_q_data),
    .rf_valid(rf_valid),
    .rf_ready(rf_ready),
    .result_data(result_data),
    .result_valid(result_valid),
    .result_ready(result_ready),
    .status_led(status_led),
    .pwr_enable(pwr_enable),
    .thermal_shutdown(thermal_shutdown),
    .pwr_lna_en(pwr_lna_en),
    .pwr_adc_en(pwr_adc_en),
    .pwr_ml_en(pwr_ml_en),
    .pwr_ddr_en(pwr_ddr_en)
);

always #2.5 sys_clk_p = ~sys_clk_p;
always #5 s_axi_aclk = ~s_axi_aclk;
always #6.67 ml_clk = ~ml_clk;

integer sample_count;

task axi_write;
    input [31:0] addr;
    input [31:0] data;
    begin
        @(posedge s_axi_aclk);
        s_axi_awaddr <= addr;
        s_axi_awvalid <= 1'b1;
        s_axi_wdata <= data;
        s_axi_wvalid <= 1'b1;
        s_axi_bready <= 1'b1;
        wait (s_axi_awready && s_axi_wready);
        @(posedge s_axi_aclk);
        s_axi_awvalid <= 1'b0;
        s_axi_wvalid <= 1'b0;
        wait (s_axi_bvalid);
        @(posedge s_axi_aclk);
        s_axi_bready <= 1'b0;
        $display("AXI WRITE addr=0x%08h data=0x%08h bresp=%b", addr, data, s_axi_bresp);
    end
endtask

task axi_read;
    input  [31:0] addr;
    output [31:0] data;
    begin
        @(posedge s_axi_aclk);
        s_axi_araddr <= addr;
        s_axi_arvalid <= 1'b1;
        s_axi_rready <= 1'b1;
        wait (s_axi_arready);
        @(posedge s_axi_aclk);
        s_axi_arvalid <= 1'b0;
        wait (s_axi_rvalid);
        data = s_axi_rdata;
        @(posedge s_axi_aclk);
        s_axi_rready <= 1'b0;
        $display("AXI READ  addr=0x%08h data=0x%08h rresp=%b", addr, data, s_axi_rresp);
    end
endtask

initial begin
    $display("========================================");
    $display("SkyShield AI v3.0 - Integrated System Testbench");
    $display("========================================");
    
    sys_clk_p = 0;
    sys_clk_n = 1;
    ml_clk = 0;
    rst_n = 0;
    s_axi_aresetn = 0;
    
    s_axi_awaddr = 0;
    s_axi_awvalid = 0;
    s_axi_wdata = 0;
    s_axi_wstrb = 4'b1111;
    s_axi_wvalid = 0;
    s_axi_bready = 0;
    s_axi_araddr = 0;
    s_axi_arvalid = 0;
    s_axi_rready = 0;
    
    rf_i_data = 0;
    rf_q_data = 0;
    rf_valid = 0;
    result_ready = 0;
    
    thermal_shutdown = 0;
    
    #100 rst_n = 1;
    #50 s_axi_aresetn = 1;
    #50;

    begin : AXI_INIT
        reg [31:0] rd_data;
        axi_write(BASE_ADDR + 32'h0, 32'h000000F1);   // enable + request all power rails
        axi_write(BASE_ADDR + 32'hC, 32'h00B400B4);   // threshold reg
        axi_read(BASE_ADDR + 32'h0, rd_data);
        axi_read(BASE_ADDR + 32'hC, rd_data);
        axi_read(BASE_ADDR + 32'h10, rd_data);
    end
    
    $display("\n[Test 1] System initialization...");
    $display("Status LEDs: %b", status_led);
    $display("RF Ready: %b", rf_ready);
    $display("AXI resets: aresetn=%b rst_n=%b", s_axi_aresetn, rst_n);
    $display("Power enable: %b | ML power: %b", pwr_enable, pwr_ml_en);
    
    #15000;
    $display("Power-up settle: pwr_enable=%b pwr_ml_en=%b pwr_adc_en=%b pwr_ddr_en=%b", pwr_enable, pwr_ml_en, pwr_adc_en, pwr_ddr_en);
    
    $display("\n[Test 2] Process benign signal...");
    for (sample_count = 0; sample_count < 512; sample_count = sample_count + 1) begin
        @(posedge sys_clk_p);
        rf_i_data = 16'h4080 + sample_count[15:0];
        rf_q_data = 16'h4080 + sample_count[15:0];
        rf_valid = 1;
        if (sample_count < 8)
            $display("BENIGN IQ[%0d] I=%0d Q=%0d", sample_count, rf_i_data, rf_q_data);
    end
    @(posedge sys_clk_p);
    rf_valid = 0;
    
    #1000;
    
    if (result_valid) begin
        $display("Result received: 0x%h", result_data);
        $display("Decoded: pwr_status=%h pwr_ready=%b pwr_fault=%b num_tracks=%0d threat=%b jammer=%b type=%0d conf=%0d",
                 result_data[29:26], result_data[25], result_data[24], result_data[23:20], result_data[19], result_data[18], result_data[17:15], result_data[14:7]);
    end else begin
        $display("Waiting for result...");
    end
    
    #2000;
    
    $display("\n[Test 3] Process threat signal...");
    for (sample_count = 0; sample_count < 512; sample_count = sample_count + 1) begin
        @(posedge sys_clk_p);
        rf_i_data = 16'hC080;
        rf_q_data = 16'hC080;
        rf_valid = 1;
        if (sample_count < 8)
            $display("THREAT IQ[%0d] I=%0d Q=%0d", sample_count, rf_i_data, rf_q_data);
    end
    @(posedge sys_clk_p);
    rf_valid = 0;
    
    #2000;
    
    if (result_valid) begin
        $display("Threat result: 0x%h", result_data);
        $display("Status LEDs: %b", status_led);
        $display("Decoded: pwr_status=%h pwr_ready=%b pwr_fault=%b num_tracks=%0d threat=%b jammer=%b type=%0d conf=%0d",
                 result_data[29:26], result_data[25], result_data[24], result_data[23:20], result_data[19], result_data[18], result_data[17:15], result_data[14:7]);
    end
    
    #1000;
    
    $display("\n========================================");
    $display("Integrated System Testbench Complete");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_integrated_system.vcd");
    $dumpvars(0, tb_integrated_system);
end

endmodule
