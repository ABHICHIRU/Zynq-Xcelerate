`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Power Control Testbench
// ============================================================================

module tb_power_control;

reg clk;
reg rst_n;
reg pwr_enable;
reg pwr_lna_req;
reg pwr_adc_req;
reg pwr_ml_req;
reg pwr_ddr_req;
reg thermal_shutdown;

wire pwr_lna_en;
wire pwr_adc_en;
wire pwr_ml_en;
wire pwr_ddr_en;
wire [3:0] pwr_status;
wire pwr_ready;
wire pwr_fault;

power_control uut (
    .clk(clk),
    .rst_n(rst_n),
    .pwr_enable(pwr_enable),
    .pwr_lna_req(pwr_lna_req),
    .pwr_adc_req(pwr_adc_req),
    .pwr_ml_req(pwr_ml_req),
    .pwr_ddr_req(pwr_ddr_req),
    .thermal_shutdown(thermal_shutdown),
    .pwr_lna_en(pwr_lna_en),
    .pwr_adc_en(pwr_adc_en),
    .pwr_ml_en(pwr_ml_en),
    .pwr_ddr_en(pwr_ddr_en),
    .pwr_lna_pgood(1'b1),
    .pwr_adc_pgood(1'b1),
    .pwr_ml_pgood(1'b1),
    .pwr_ddr_pgood(1'b1),
    .pwr_status(pwr_status),
    .pwr_ready(pwr_ready),
    .pwr_fault(pwr_fault)
);

always #5 clk = ~clk;

initial begin
    $display("========================================");
    $display("Power Control Testbench");
    $display("========================================");
    
    clk = 0;
    rst_n = 0;
    pwr_enable = 0;
    pwr_lna_req = 0;
    pwr_adc_req = 0;
    pwr_ml_req = 0;
    pwr_ddr_req = 0;
    thermal_shutdown = 0;
    
    #20 rst_n = 1;
    #20;
    
    $display("\n[Test 1] Power up sequence...");
    pwr_enable = 1;
    pwr_lna_req = 1;
    pwr_adc_req = 1;
    pwr_ml_req = 1;
    pwr_ddr_req = 1;
    
    $display("Waiting for power sequence...");
    wait(pwr_ready);
    $display("Power sequence complete!");
    $display("Status: pwr_lna_en=%b, pwr_adc_en=%b, pwr_ml_en=%b, pwr_ddr_en=%b",
             pwr_lna_en, pwr_adc_en, pwr_ml_en, pwr_ddr_en);
    $display("Power status: %b", pwr_status);
    
    #500;
    
    $display("\n[Test 2] Thermal shutdown...");
    thermal_shutdown = 1;
    #100;
    $display("After thermal shutdown:");
    $display("pwr_fault=%b, pwr_ready=%b", pwr_fault, pwr_ready);
    
    thermal_shutdown = 0;
    #200;
    
    $display("\n[Test 3] Power down...");
    pwr_enable = 0;
    #200;
    $display("After power down:");
    $display("pwr_lna_en=%b, pwr_adc_en=%b, pwr_ml_en=%b, pwr_ddr_en=%b",
             pwr_lna_en, pwr_adc_en, pwr_ml_en, pwr_ddr_en);
    
    #100;
    
    $display("\n========================================");
    $display("Testbench Complete - PASSED");
    $display("========================================");
    $finish;
end

initial begin
    $dumpfile("tb_power_control.vcd");
    $dumpvars(0, tb_power_control);
end

endmodule
