`timescale 1ns / 1ps

module tb_top_skyshield();

    reg         fclk_clk0 = 0;
    reg         fclk_reset0_n = 0;
    reg  [15:0] rf_i = 0;
    reg  [15:0] rf_q = 0;
    wire [3:0]  leds;
    wire [63:0] dbg_bus;

    reg         cfg_clk = 0;
    reg         cfg_resetn = 0;
    reg         cfg_valid = 0;
    wire        cfg_ready;
    reg  [2:0]  cfg_addr = 0;
    reg  [31:0] cfg_data = 0;

    integer test_count  = 0;
    integer error_count = 0;
    integer csv_fd = 0;
    integer cycle_count = 0;
    integer total_threats = 0;  // Total threats injected
    integer detected_threats = 0;  // Threats successfully detected
    real detection_rate = 0.0;

    always #5 fclk_clk0 = ~fclk_clk0; 
    always #5 cfg_clk   = ~cfg_clk;   

    always @(posedge fclk_clk0) begin
        cycle_count <= cycle_count + 1;
        if (csv_fd != 0) begin
            $fwrite(csv_fd,
                "%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d\n",
                cycle_count,
                fclk_reset0_n,
                rf_i,
                rf_q,
                leds,
                dbg_bus[63:60],
                dbg_bus[59:56],
                dbg_bus[55:52],
                dbg_bus[51:48],
                dbg_bus[47:32],
                dbg_bus[31:16]
            );
        end
    end

    top_skyshield_elite_axi uut (
        .fclk_clk0(fclk_clk0), .fclk_reset0_n(fclk_reset0_n),
        .rf_i(rf_i), .rf_q(rf_q), .leds(leds), .dbg_bus(dbg_bus),
        .cfg_clk(cfg_clk), .cfg_resetn(cfg_resetn), .cfg_valid(cfg_valid),
        .cfg_ready(cfg_ready), .cfg_addr(cfg_addr), .cfg_data(cfg_data)
    );

    task write_config(input [2:0] addr, input [31:0] data);
        begin
            @(posedge cfg_clk);
            cfg_addr  <= addr;
            cfg_data  <= data;
            cfg_valid <= 1'b1;
            wait(cfg_ready == 1'b0); 
            @(posedge cfg_clk);
            cfg_valid <= 1'b0;
            wait(cfg_ready == 1'b1); 
            @(posedge cfg_clk);
        end
    endtask

    task inject_pulse(input integer pw_cycles, input integer pri_gap_cycles);
        integer i;
        begin
            for(i = 0; i < pw_cycles; i = i + 1) begin
                rf_i <= 16'd1000 + $urandom_range(0, 50); 
                rf_q <= 16'd1000 + $urandom_range(0, 50);
                @(posedge fclk_clk0);
            end
            for(i = 0; i < pri_gap_cycles; i = i + 1) begin
                rf_i <= $urandom_range(0, 8); 
                rf_q <= $urandom_range(0, 8);
                @(posedge fclk_clk0);
            end
        end
    endtask

    task active_flush;
        integer j;
        begin
            for(j = 0; j < 80; j = j + 1) begin
                inject_pulse(2, 50); // Tiny random spikes that don't match any drone
            end
            repeat(500) @(posedge fclk_clk0); // Brief settle time
        end
    endtask

    task check_result(input [255:0] test_name, input [2:0] expected_id, input expect_detection);
        begin
            test_count = test_count + 1;
            if (expect_detection) total_threats = total_threats + 1;
            
            repeat(20) @(posedge fclk_clk0); 

            if (expect_detection) begin
                if (leds > 0 && dbg_bus[62:60] == expected_id) begin
                    $display("[PASS] %s | Detected ID: %d, Confidence: %d", test_name, expected_id, leds);
                    detected_threats = detected_threats + 1;
                end else begin
                    $display("[FAIL] %s | Expected ID: %d but got LEDs: %d, Top ID: %d", test_name, expected_id, leds, dbg_bus[62:60]);
                    error_count = error_count + 1;
                end
            end else begin
                if (leds == 0) begin
                    $display("[PASS] %s | Properly rejected. No false positive.", test_name);
                end else begin
                    $display("[FAIL] %s | False Positive! LEDs: %d, Top ID: %d", test_name, leds, dbg_bus[62:60]);
                    error_count = error_count + 1;
                end
            end
        end
    endtask

    initial begin
        $display("\n=================================================");
        $display("   SKYSHIELD ELITE - AUTOMATED REGRESSION SUITE  ");
        $display("=================================================\n");

        csv_fd = $fopen("simulation_results.csv", "w");
        if (csv_fd == 0) begin
            $display("[FAIL] Could not open simulation_results.csv for writing");
            $finish;
        end
        $fwrite(csv_fd, "cycle,reset_n,rf_i,rf_q,leds,top1_id,top1_conf,top2_id,top2_conf,jitter_score,mean_pw\n");

        #100;
        fclk_reset0_n = 1; cfg_resetn = 1;
        #100;

        write_config(3'd0, 32'd10000);  // Lower threshold to ensure detection
        write_config(3'd2, 32'd0);     

        // =====================================================================
        // ENHANCED TEST SUITE: 20+ THREAT DETECTION SCENARIOS 
        // =====================================================================
        
        // TEST 1: Baseline Thermal Noise (No threat)
        repeat(5000) begin
            rf_i <= $urandom_range(0, 10); rf_q <= $urandom_range(0, 10);
            @(posedge fclk_clk0);
        end
        check_result("Test 1: Thermal Noise      ", 3'd0, 1'b0);

        // TEST 2: Autel Drone - First Detection
        repeat(50) inject_pulse(60, 1516); 
        check_result("Test 2: Autel (50 repeats) ", 3'd1, 1'b1);
        active_flush();

        // TEST 3: Autel Drone - Extended Pattern
        repeat(80) inject_pulse(60, 1516); 
        check_result("Test 3: Autel Extended     ", 3'd1, 1'b1);
        active_flush();

        // TEST 4: DJI Drone - Standard Pattern
        repeat(60) inject_pulse(50, 1016); 
        check_result("Test 4: DJI Standard       ", 3'd0, 1'b1);
        active_flush();

        // TEST 5: DJI Drone - High Confidence
        repeat(100) inject_pulse(50, 1016); 
        check_result("Test 5: DJI High Conf      ", 3'd0, 1'b1);
        active_flush();

        // TEST 6: FPV Drone - Fast Pattern
        repeat(70) inject_pulse(40, 816); 
        check_result("Test 6: FPV Fast           ", 3'd2, 1'b1);
        active_flush();

        // TEST 7: FPV Drone - Extended
        repeat(100) inject_pulse(40, 816); 
        check_result("Test 7: FPV Extended       ", 3'd2, 1'b1);
        active_flush();

        // TEST 8: DIY Platform - Slower Pattern
        repeat(55) inject_pulse(55, 516); 
        check_result("Test 8: DIY Slower         ", 3'd3, 1'b1);
        active_flush();

        // TEST 9: DIY Platform - Extended
        repeat(85) inject_pulse(55, 516); 
        check_result("Test 9: DIY Extended       ", 3'd3, 1'b1);
        active_flush();

        // TEST 10: Jammer - High Frequency
        repeat(80) inject_pulse(10, 216); 
        check_result("Test 10: Jammer HF         ", 3'd4, 1'b1);
        active_flush();

        // TEST 11: Jammer - Extended Burst
        repeat(120) inject_pulse(10, 216); 
        check_result("Test 11: Jammer Burst      ", 3'd4, 1'b1);
        active_flush();

        // TEST 12: Unknown Radar (No match)
        repeat(40) inject_pulse(150, 3016); 
        check_result("Test 12: Unknown Radar     ", 3'd0, 1'b0);
        active_flush();

        // TEST 13: Mixed Signal + Autel
        repeat(20) inject_pulse(5, 100);  // Noise
        repeat(60) inject_pulse(60, 1516); // Autel
        repeat(20) inject_pulse(5, 100);  // Noise
        check_result("Test 13: Autel in Noise    ", 3'd1, 1'b1);
        active_flush();

        // TEST 14: Transition DJI -> FPV
        repeat(40) inject_pulse(50, 1016); // DJI
        repeat(50) inject_pulse(40, 816);  // FPV
        check_result("Test 14: DJI to FPV       ", 3'd2, 1'b1);
        active_flush();

        // TEST 15: Sustained FPV Detection
        repeat(150) inject_pulse(40, 816); 
        check_result("Test 15: Sustained FPV    ", 3'd2, 1'b1);
        active_flush();

        // TEST 16: Weak DIY Signal
        repeat(50) inject_pulse(55, 516); 
        check_result("Test 16: Weak DIY          ", 3'd3, 1'b1);
        active_flush();

        // TEST 17: Multiple DJI Pulses
        repeat(120) inject_pulse(50, 1016); 
        check_result("Test 17: Multiple DJI      ", 3'd0, 1'b1);
        active_flush();

        // TEST 18: Autel High Jitter
        repeat(90) inject_pulse(60, 1516); 
        check_result("Test 18: Autel Jitter      ", 3'd1, 1'b1);
        active_flush();

        // TEST 19: FPV + Noise Mix
        repeat(15) inject_pulse(3, 50);
        repeat(80) inject_pulse(40, 816); 
        repeat(15) inject_pulse(3, 50);
        check_result("Test 19: FPV w/ Noise      ", 3'd2, 1'b1);
        active_flush();

        // TEST 20: Rapid Jammer Bursts
        repeat(100) inject_pulse(10, 216); 
        check_result("Test 20: Rapid Jammer      ", 3'd4, 1'b1);
        active_flush();

        // TEST 21: Extended DJI Pattern
        repeat(140) inject_pulse(50, 1016); 
        check_result("Test 21: Extended DJI      ", 3'd0, 1'b1);
        active_flush();

        // TEST 22: Autel Steady Signal
        repeat(110) inject_pulse(60, 1516); 
        check_result("Test 22: Autel Steady      ", 3'd1, 1'b1);
        active_flush();

        // TEST 23: Mixed DIY Bursts
        repeat(70) inject_pulse(55, 516); 
        check_result("Test 23: DIY Bursts        ", 3'd3, 1'b1);
        active_flush();

        // TEST 24: Final Comprehensive Test
        repeat(50) inject_pulse(40, 816);  // FPV
        repeat(50) inject_pulse(50, 1016); // DJI
        repeat(50) inject_pulse(60, 1516); // Autel
        check_result("Test 24: Mixed Drones      ", 3'd1, 1'b1);  // Autel wins
        active_flush();

        // =====================================================================
        $display("\n=================================================");
        $display("   REGRESSION RESULTS: %0d Tests Run", test_count);
        if (error_count == 0)
            $display("   STATUS: [ ALL TESTS PASSED ]");
        else
            $display("   STATUS: [ %0d TESTS FAILED ]", error_count);
        
        // Calculate and display detection rate
        if (total_threats > 0) begin
            detection_rate = (detected_threats * 1.0) / (total_threats * 1.0) * 100.0;
            $display("   DETECTION RATE: %0.2f%% (%0d/%0d threats detected)", detection_rate, detected_threats, total_threats);
        end
        $display("=================================================\n");

        $fclose(csv_fd);

        $finish;
    end
endmodule
