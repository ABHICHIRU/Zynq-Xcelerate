`timescale 1ns / 1ps

module tb_conv1d_exhaustive();
    // Parameters
    parameter DATA_WIDTH = 16;
    parameter KERNEL_SIZE = 9; // Max supported size instantiated
    parameter COEFF_WIDTH = 16;
    parameter ACC_WIDTH = 32;

    // Clock and Reset Signals
    reg clk;
    reg rst_n;
    
    // AXI-Stream Input Signals
    reg signed [DATA_WIDTH-1:0] s_axis_tdata;
    reg s_axis_tvalid;
    wire s_axis_tready;
    
    // AXI-Stream Output Signals
    wire signed [DATA_WIDTH-1:0] m_axis_tdata;
    wire m_axis_tvalid;
    reg m_axis_tready;
    
    // Kernel Interface Signals
    reg signed [COEFF_WIDTH-1:0] coeff_data;
    reg [4:0] coeff_addr;
    reg coeff_we;
    
    // Control Signals
    reg [2:0] kernel_sel;
    reg enable;

    // Output File Handle
    integer fd;

    // Instantiate the Unit Under Test (UUT)
    conv1d #(
        .DATA_WIDTH(DATA_WIDTH),
        .KERNEL_SIZE(KERNEL_SIZE),
        .COEFF_WIDTH(COEFF_WIDTH),
        .ACC_WIDTH(ACC_WIDTH)
    ) uut (
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

    // Clock Generation (100MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // File writing & logging logic
    always @(posedge clk) begin
        if (fd) begin
            $fdisplay(fd, "%0t,%b,%b,%b,%d,%b,%d,%b,%d", 
                $time, rst_n, enable, kernel_sel, 
                s_axis_tdata, s_axis_tvalid, 
                m_axis_tdata, m_axis_tvalid, s_axis_tready);
        end
    end

    // Test Variables
    integer i;
    
    // Task to load kernel
    task load_kernel;
        input [2:0] k_sel;
        input integer size;
        begin
            kernel_sel = k_sel;
            coeff_we = 1;
            // Load a symmetric kernel
            for (i=0; i<size; i=i+1) begin
                coeff_addr = i[4:0];
                coeff_data = (i+1) * 10; // example: 10, 20, 30...
                @(posedge clk);
            end
            coeff_we = 0;
            @(posedge clk);
        end
    endtask

    // Task to feed data
    task feed_data;
        input integer count;
        input integer kind; // 0=impulse, 1=step, 2=random, 3=max_values
        begin
            s_axis_tvalid = 1;
            for (i=0; i<count; i=i+1) begin
                if (kind == 0)      s_axis_tdata = (i == 2) ? 16'h0100 : 16'h0;
                else if (kind == 1) s_axis_tdata = (i > 2) ? 16'h0050 : 16'h0;
                else if (kind == 2) s_axis_tdata = $random % 16'h0FFF;
                else if (kind == 3) s_axis_tdata = (i%2==0) ? 16'h7FFF : 16'h8000;
                
                @(posedge clk);
                while (!s_axis_tready) @(posedge clk); // wait for ready
            end
            s_axis_tvalid = 0;
            s_axis_tdata = 0;
        end
    endtask

    initial begin
        // Open CSV file
        fd = $fopen("conv1d_exhaustive_results.csv", "w");
        if (!fd) begin
            $display("ERROR: Could not open file conv1d_exhaustive_results.csv");
            $finish;
        end
        $fdisplay(fd, "Time_ns,Reset_n,Enable,Kernel_Sel,In_Data,In_Valid,Out_Data,Out_Valid,In_Ready");

        // Initialization
        rst_n = 0;
        s_axis_tdata = 0;
        s_axis_tvalid = 0;
        m_axis_tready = 1;
        coeff_data = 0;
        coeff_addr = 0;
        coeff_we = 0;
        kernel_sel = 3'b011; // 3-tap
        enable = 0;

        // Reset Sequence
        #20 rst_n = 1;
        enable = 1;
        #20;

        $display("Starting Exhaustive Testing Pipeline...");

        // === TEST PHASE 1: 3-TAP KERNEL ===
        $display("PHASE 1: 3-TAP KERNEL");
        load_kernel(3'b011, 3);
        feed_data(15, 0); // Impulse
        #100;
        feed_data(15, 1); // Step
        #100;

        // === TEST PHASE 2: 5-TAP KERNEL ===
        $display("PHASE 2: 5-TAP KERNEL");
        load_kernel(3'b101, 5);
        feed_data(20, 0); // Impulse
        #100;
        feed_data(100, 2); // Random bounds
        #100;

        // === TEST PHASE 3: 7-TAP KERNEL ===
        $display("PHASE 3: 7-TAP KERNEL");
        load_kernel(3'b111, 7);
        feed_data(25, 0); // Impulse
        #100;
        feed_data(100, 2); // Random
        #100;

        // === TEST PHASE 4: 9-TAP KERNEL ===
        $display("PHASE 4: 9-TAP KERNEL");
        load_kernel(3'b001, 9);
        feed_data(50, 0); // Impulse
        #100;
        feed_data(50, 3); // Max Value Sweeps to Test Saturation Logic!
        #100;
        
        // Let pipeline flush
        #200;

        $display("Simulation Complete. Results dumped to conv1d_exhaustive_results.csv");
        $fclose(fd);
        $finish;
    end

endmodule
