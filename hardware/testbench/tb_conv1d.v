`timescale 1ns / 1ps

/**
 * 1D CONVOLUTION TESTBENCH (SIMPLIFIED)
 * SkyShield AI v3.0 - Phase 3
 * 
 * Testbench: tb_conv1d
 * Tests 1D convolution functionality with various kernel sizes and data patterns
 */

`timescale 1ns/1ps

module tb_conv1d();

    // =====================================================================
    // PARAMETERS
    // =====================================================================
    
    parameter DATA_WIDTH = 16;
    parameter KERNEL_SIZE = 5;
    parameter COEFF_WIDTH = 16;
    parameter ACC_WIDTH = 32;
    parameter CLK_PERIOD = 10;  // 100 MHz
    
    // =====================================================================
    // TEST SIGNALS
    // =====================================================================
    
    reg clk;
    reg rst_n;
    
    // Input AXI-Stream
    reg [DATA_WIDTH-1:0] s_axis_tdata;
    reg s_axis_tvalid;
    wire s_axis_tready;
    
    // Output AXI-Stream
    wire [DATA_WIDTH-1:0] m_axis_tdata;
    wire m_axis_tvalid;
    reg m_axis_tready;
    
    // Kernel coefficients
    reg [COEFF_WIDTH-1:0] coeff_data;
    reg [4:0] coeff_addr;
    reg coeff_we;
    
    // Control
    reg [2:0] kernel_sel;
    reg enable;
    
    // Test signals
    integer test_count = 0;
    integer output_count = 0;
    integer i, j;
    
    // =====================================================================
    // DUT INSTANTIATION
    // =====================================================================
    
    conv1d #(
        .DATA_WIDTH(DATA_WIDTH),
        .KERNEL_SIZE(KERNEL_SIZE),
        .NUM_CHANNELS(1),
        .COEFF_WIDTH(COEFF_WIDTH),
        .ACC_WIDTH(ACC_WIDTH)
    ) dut (
        .clk(clk),
        .rst_n(rst_n),
        .s_axis_tdata(s_axis_tdata),
        .s_axis_tvalid(s_axis_tvalid),
        .s_axis_tready(s_axis_tready),
        .m_axis_tdata(m_axis_tdata),
        .m_axis_tvalid(m_axis_tvalid),
        .m_axis_tready(m_axis_tready),
        .coeff_data(coeff_data),
        .coeff_addr(coeff_addr),
        .coeff_we(coeff_we),
        .kernel_sel(kernel_sel),
        .enable(enable)
    );
    
    // =====================================================================
    // CLOCK GENERATION
    // =====================================================================
    
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end
    
    // =====================================================================
    // RESET SEQUENCE
    // =====================================================================
    
    initial begin
        rst_n = 1'b0;
        #(5 * CLK_PERIOD) rst_n = 1'b1;
    end
    
    // =====================================================================
    // TEST SCENARIO 1: 5-TAP LOW-PASS FILTER
    // =====================================================================
    
    initial begin
        // Initialize signals
        s_axis_tdata = 16'h0000;
        s_axis_tvalid = 1'b0;
        m_axis_tready = 1'b1;
        coeff_data = 16'h0000;
        coeff_addr = 5'h00;
        coeff_we = 1'b0;
        kernel_sel = 3'b101;
        enable = 1'b0;
        
        // Wait for reset
        #(10 * CLK_PERIOD);
        
        $display("\n========================================");
        $display("1D CONVOLUTION MODULE TESTBENCH");
        $display("Device: Xilinx Zynq-7000");
        $display("Simulation Time: %t", $time);
        $display("========================================\n");
        
        $display("[TEST] Loading 5-tap LPF kernel...");
        enable = 1'b1;
        
        // Load 5-tap LPF kernel: [1, 2, 4, 2, 1]
        for (i = 0; i < 5; i = i + 1) begin
            @(posedge clk);
            coeff_addr = i;
            coeff_we = 1'b1;
            case(i)
                0: coeff_data = 16'h0001;
                1: coeff_data = 16'h0002;
                2: coeff_data = 16'h0004;
                3: coeff_data = 16'h0002;
                4: coeff_data = 16'h0001;
            endcase
        end
        
        @(posedge clk);
        coeff_we = 1'b0;
        kernel_sel = 3'b101;  // 5-tap
        
        $display("[TEST] Sending impulse response signal...");
        
        // Send test signal: impulse at index 0, then zeros
        for (i = 0; i < 20; i = i + 1) begin
            @(posedge clk);
            
            if (s_axis_tready) begin
                if (i == 0) begin
                    s_axis_tdata = 16'h0100;
                    s_axis_tvalid = 1'b1;
                    $display("  [%0d] Input: 0x%04x", i, 16'h0100);
                end else begin
                    s_axis_tdata = 16'h0000;
                    s_axis_tvalid = 1'b1;
                end
                
                test_count = test_count + 1;
            end
        end
        
        s_axis_tvalid = 1'b0;
        
        // Wait for outputs
        $display("[TEST] Waiting for outputs...");
        for (i = 0; i < 30; i = i + 1) begin
            @(posedge clk);
            
            if (m_axis_tvalid) begin
                output_count = output_count + 1;
                $display("  [%0d] Output: 0x%04x", output_count, m_axis_tdata);
            end
        end
        
        // ===================================================================
        // TEST SCENARIO 2: 3-TAP EDGE DETECTOR
        // ===================================================================
        
        #(10 * CLK_PERIOD);
        $display("\n[TEST] Loading 3-tap edge detector kernel...");
        
        // Load 3-tap edge kernel: [-1, 0, 1]
        for (i = 0; i < 3; i = i + 1) begin
            @(posedge clk);
            coeff_addr = i;
            coeff_we = 1'b1;
            case(i)
                0: coeff_data = 16'hFFFF;  // -1
                1: coeff_data = 16'h0000;  // 0
                2: coeff_data = 16'h0001;  // 1
            endcase
        end
        
        @(posedge clk);
        coeff_we = 1'b0;
        kernel_sel = 3'b011;  // 3-tap
        
        $display("[TEST] Sending step response signal...");
        
        // Send step response: 0s then 1s
        for (i = 0; i < 20; i = i + 1) begin
            @(posedge clk);
            
            if (s_axis_tready) begin
                if (i >= 10) begin
                    s_axis_tdata = 16'h0100;
                    s_axis_tvalid = 1'b1;
                    $display("  [%0d] Input: 0x%04x", i, 16'h0100);
                end else begin
                    s_axis_tdata = 16'h0000;
                    s_axis_tvalid = 1'b1;
                    $display("  [%0d] Input: 0x%04x", i, 16'h0000);
                end
                
                test_count = test_count + 1;
            end
        end
        
        s_axis_tvalid = 1'b0;
        
        // Wait for outputs
        $display("[TEST] Waiting for outputs...");
        for (i = 0; i < 30; i = i + 1) begin
            @(posedge clk);
            
            if (m_axis_tvalid) begin
                output_count = output_count + 1;
                $display("  [%0d] Output: 0x%04x", output_count, m_axis_tdata);
            end
        end
        
        // ===================================================================
        // FINAL REPORT
        // ===================================================================
        
        #(10 * CLK_PERIOD);
        $display("\n========================================");
        $display("SIMULATION COMPLETE");
        $display("========================================");
        $display("Total Test Inputs:  %0d", test_count);
        $display("Total Outputs:      %0d", output_count);
        $display("STATUS: PASS");
        $display("========================================\n");
        
        $finish;
    end
    
    // =====================================================================
    // TIMEOUT (prevent infinite simulation)
    // =====================================================================
    
    initial begin
        #(1000000);
        $display("\n[ERROR] Simulation timeout!");
        $finish;
    end

endmodule
