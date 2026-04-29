`timescale 1ns / 1ps

module tb_conv1d_iq_exhaustive();
    parameter DATA_WIDTH = 16;
    parameter KERNEL_SIZE = 9;
    parameter COEFF_WIDTH = 16;
    parameter ACC_WIDTH = 32;

    // Clock & Reset
    reg clk;
    reg rst_n;

    // I-Channel Signals
    reg signed [DATA_WIDTH-1:0] s_axi_i_tdata;
    reg s_axi_i_tvalid;
    wire s_axi_i_tready;
    wire signed [DATA_WIDTH-1:0] m_axi_i_tdata;
    wire m_axi_i_tvalid;
    reg m_axi_i_tready;
    
    // Q-Channel Signals
    reg signed [DATA_WIDTH-1:0] s_axi_q_tdata;
    reg s_axi_q_tvalid;
    wire s_axi_q_tready;
    wire signed [DATA_WIDTH-1:0] m_axi_q_tdata;
    wire m_axi_q_tvalid;
    reg m_axi_q_tready;

    // Kernel Signals (Shared logic, dedicated pins)
    reg signed [COEFF_WIDTH-1:0] coeff_data_i, coeff_data_q;
    reg [4:0] coeff_addr;
    reg coeff_we_i, coeff_we_q;
    reg [2:0] kernel_sel;
    reg enable;

    integer fd;

    // I-Channel Conv1d Under Test (UUT)
    conv1d #(
        .DATA_WIDTH(DATA_WIDTH), .KERNEL_SIZE(KERNEL_SIZE),
        .COEFF_WIDTH(COEFF_WIDTH), .ACC_WIDTH(ACC_WIDTH)
    ) uut_i (
        .clk(clk), .rst_n(rst_n),
        .s_axis_tdata(s_axi_i_tdata), .s_axis_tvalid(s_axi_i_tvalid), .s_axis_tready(s_axi_i_tready),
        .m_axis_tdata(m_axi_i_tdata), .m_axis_tvalid(m_axi_i_tvalid), .m_axis_tready(m_axi_i_tready),
        .coeff_data(coeff_data_i), .coeff_addr(coeff_addr), .coeff_we(coeff_we_i),
        .kernel_sel(kernel_sel), .enable(enable)
    );

    // Q-Channel Conv1d Under Test (UUT)
    conv1d #(
        .DATA_WIDTH(DATA_WIDTH), .KERNEL_SIZE(KERNEL_SIZE),
        .COEFF_WIDTH(COEFF_WIDTH), .ACC_WIDTH(ACC_WIDTH)
    ) uut_q (
        .clk(clk), .rst_n(rst_n),
        .s_axis_tdata(s_axi_q_tdata), .s_axis_tvalid(s_axi_q_tvalid), .s_axis_tready(s_axi_q_tready),
        .m_axis_tdata(m_axi_q_tdata), .m_axis_tvalid(m_axi_q_tvalid), .m_axis_tready(m_axi_q_tready),
        .coeff_data(coeff_data_q), .coeff_addr(coeff_addr), .coeff_we(coeff_we_q),
        .kernel_sel(kernel_sel), .enable(enable)
    );

    // Clock gen
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // File Logger
    always @(posedge clk) begin
        if (fd) begin
            $fdisplay(fd, "%0t,%b,%b,%b,%d,%d,%b,%d,%d,%b,%b", 
                $time, rst_n, enable, kernel_sel, 
                s_axi_i_tdata, s_axi_q_tdata, 
                s_axi_i_tvalid, 
                m_axi_i_tdata, m_axi_q_tdata, 
                m_axi_i_tvalid, s_axi_i_tready);
        end
    end

    // Tasks for Loading Coeffs and Feed
    integer idx;
    task load_kernel;
        input [2:0] k_sel;
        input integer size;
        begin
            kernel_sel = k_sel;
            coeff_we_i = 1; coeff_we_q = 1;
            for (idx=0; idx<size; idx=idx+1) begin
                coeff_addr = idx[4:0];
                coeff_data_i = (idx+1) * 10; // I-coeff: 10, 20...
                coeff_data_q = (idx+1) * 15; // Q-coeff: 15, 30...
                @(posedge clk);
            end
            coeff_we_i = 0; coeff_we_q = 0;
            @(posedge clk);
        end
    endtask

    task feed_iq_data;
        input integer count;
        input integer kind;
        begin
            s_axi_i_tvalid = 1; s_axi_q_tvalid = 1;
            for (idx=0; idx<count; idx=idx+1) begin
                // Kind 0: Impulse
                if (kind == 0) begin
                    s_axi_i_tdata = (idx == 2) ? 16'h0100 : 16'h0;
                    s_axi_q_tdata = (idx == 2) ? 16'h0100 : 16'h0;
                end
                // Kind 1: Random Complex signals
                else if (kind == 1) begin
                    s_axi_i_tdata = $random % 16'h0FFF;
                    s_axi_q_tdata = $random % 16'h0FFF;
                end
                // Kind 2: Max Threshold Saturation
                else if (kind == 2) begin
                    s_axi_i_tdata = (idx%2==0) ? 16'h7FFF : 16'h8000;
                    s_axi_q_tdata = (idx%2==0) ? 16'h7FFF : 16'h8000;
                end
                
                @(posedge clk);
                while (!s_axi_i_tready || !s_axi_q_tready) @(posedge clk);
            end
            s_axi_i_tvalid = 0; s_axi_q_tvalid = 0;
            s_axi_i_tdata = 0; s_axi_q_tdata = 0;
        end
    endtask

    initial begin
        fd = $fopen("conv1d_iq_exhaustive_results.csv", "w");
        if (!fd) $finish;
        $fdisplay(fd, "Time_ns,Reset_n,Enable,Kernel_Sel,In_I_Data,In_Q_Data,In_Valid,Out_I_Data,Out_Q_Data,Out_Valid,System_Ready");

        rst_n=0; enable=0; kernel_sel=3'b011;
        s_axi_i_tvalid=0; s_axi_q_tvalid=0;
        m_axi_i_tready=1; m_axi_q_tready=1;
        s_axi_i_tdata=0; s_axi_q_tdata=0;
        coeff_data_i=0; coeff_data_q=0; coeff_addr=0;
        coeff_we_i=0; coeff_we_q=0;

        #20 rst_n = 1; enable = 1; #20;

        $display("Starting I/Q Exhaustive System Test...");

        // Exhaustive dual-channel stimulus
        load_kernel(3'b011, 3); feed_iq_data(10, 0); #100;
        load_kernel(3'b101, 5); feed_iq_data(20, 1); #100;
        load_kernel(3'b111, 7); feed_iq_data(20, 1); #100;
        load_kernel(3'b001, 9); feed_iq_data(30, 2); #100;
        
        #200;
        $display("I/Q Simulation Complete. Logged to conv1d_iq_exhaustive_results.csv.");
        $fclose(fd);
        $finish;
    end
endmodule
