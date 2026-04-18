`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Refactored Modules Comprehensive Testbench
// Tests all 5 refactored modules with optimized parameters
// ============================================================================

module tb_refactored_modules;

// ============================================================================
// Test Parameters
// ============================================================================
parameter SIM_CLOCK_PERIOD = 10;  // 100 MHz clock
parameter INPUT_LENGTH = 512;
parameter DATA_WIDTH = 8;

// Test result tracking
integer tests_passed = 0;
integer tests_failed = 0;
integer test_number = 0;

// ============================================================================
// Clock and Reset
// ============================================================================
reg clk;
reg rst_n;

always #(SIM_CLOCK_PERIOD/2) clk = ~clk;

// ============================================================================
// Test 1: TYPE CLASSIFIER - Optimized for 6-class detection
// ============================================================================
reg tc_valid_in;
reg [DATA_WIDTH-1:0] tc_i_data;
reg [DATA_WIDTH-1:0] tc_q_data;
wire tc_valid_out;
wire [7:0] tc_class_prob_0;
wire [7:0] tc_class_prob_1;
wire [7:0] tc_class_prob_2;
wire [7:0] tc_class_prob_3;
wire [7:0] tc_class_prob_4;
wire [7:0] tc_class_prob_5;
wire [2:0] tc_class_id;

type_classifier_rtl #(
    .DATA_WIDTH(DATA_WIDTH),
    .INPUT_LENGTH(INPUT_LENGTH),
    .NUM_CLASSES(6)
) type_classifier_inst (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(tc_valid_in),
    .i_data(tc_i_data),
    .q_data(tc_q_data),
    .valid_out(tc_valid_out),
    .class_prob_0(tc_class_prob_0),
    .class_prob_1(tc_class_prob_1),
    .class_prob_2(tc_class_prob_2),
    .class_prob_3(tc_class_prob_3),
    .class_prob_4(tc_class_prob_4),
    .class_prob_5(tc_class_prob_5),
    .class_id(tc_class_id)
);

// ============================================================================
// Test 2: JAMMER DETECTOR - Optimized for jammer/no-jammer detection
// ============================================================================
reg jd_valid_in;
reg [DATA_WIDTH-1:0] jd_i_data;
reg [DATA_WIDTH-1:0] jd_q_data;
wire jd_valid_out;
wire [7:0] jd_jammer_prob;
wire jd_is_jammer;

jammer_detector_rtl #(
    .DATA_WIDTH(DATA_WIDTH),
    .INPUT_LENGTH(INPUT_LENGTH),
    .FIRE_CHANNELS(320)
) jammer_detector_inst (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(jd_valid_in),
    .i_data(jd_i_data),
    .q_data(jd_q_data),
    .valid_out(jd_valid_out),
    .jammer_prob(jd_jammer_prob),
    .is_jammer(jd_is_jammer)
);

// ============================================================================
// Test 3: THREAT DETECTOR - Optimized for threat/benign detection
// ============================================================================
reg td_valid_in;
reg [DATA_WIDTH-1:0] td_i_data;
reg [DATA_WIDTH-1:0] td_q_data;
wire td_valid_out;
wire [7:0] td_threat_prob;
wire td_is_threat;

threat_detector_rtl #(
    .DATA_WIDTH(DATA_WIDTH),
    .INPUT_LENGTH(INPUT_LENGTH),
    .CHANNELS(2)
) threat_detector_inst (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(td_valid_in),
    .i_data(td_i_data),
    .q_data(td_q_data),
    .valid_out(td_valid_out),
    .threat_prob(td_threat_prob),
    .is_threat(td_is_threat)
);

// ============================================================================
// Test 4: TRACKING ENGINE - Optimized for multi-track management
// ============================================================================
parameter MAX_TRACKS = 16;

reg te_valid_in;
reg [2:0] te_threat_type;
reg te_is_threat;
reg [7:0] te_confidence;
reg [15:0] te_signal_bearing;
reg [15:0] te_signal_strength;
reg [31:0] te_timestamp;

wire te_valid_out;
wire [3:0] te_num_active_tracks;
wire [31:0] te_track_id [0:MAX_TRACKS-1];
wire [15:0] te_track_age [0:MAX_TRACKS-1];
wire [15:0] te_track_velocity [0:MAX_TRACKS-1];
wire [2:0] te_track_type [0:MAX_TRACKS-1];
wire te_track_confirmed [0:MAX_TRACKS-1];

tracking_engine #(
    .MAX_TRACKS(MAX_TRACKS),
    .TRACK_AGE_LIMIT(32),
    .VELOCITY_WINDOW(8)
) tracking_engine_inst (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(te_valid_in),
    .threat_type(te_threat_type),
    .is_threat(te_is_threat),
    .confidence(te_confidence),
    .signal_bearing(te_signal_bearing),
    .signal_strength(te_signal_strength),
    .timestamp(te_timestamp),
    .valid_out(te_valid_out),
    .num_active_tracks(te_num_active_tracks),
    .track_id(te_track_id),
    .track_age(te_track_age),
    .track_velocity(te_track_velocity),
    .track_type(te_track_type),
    .track_confirmed(te_track_confirmed)
);

// ============================================================================
// Test 5: VOTING MODULE - Optimized for decision fusion
// ============================================================================
reg vm_valid_in;
reg [7:0] vm_threat_prob;
reg vm_threat_valid;
reg [7:0] vm_type_prob_0;
reg [7:0] vm_type_prob_1;
reg [7:0] vm_type_prob_2;
reg [7:0] vm_type_prob_3;
reg [7:0] vm_type_prob_4;
reg [7:0] vm_type_prob_5;
reg [2:0] vm_type_id;
reg vm_type_valid;
reg [7:0] vm_jammer_prob;
reg vm_jammer_valid;

wire vm_valid_out;
wire vm_is_threat;
wire [2:0] vm_threat_type;
wire vm_jammer_flag;
wire [7:0] vm_confidence;

voting_logic #(
    .THREAT_THRESHOLD(180),
    .JAMMER_THRESHOLD(200),
    .TYPE_WEIGHT(3),
    .THREAT_WEIGHT(4),
    .JAMMER_WEIGHT(3)
) voting_module_inst (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(vm_valid_in),
    .threat_prob(vm_threat_prob),
    .threat_valid(vm_threat_valid),
    .type_prob_0(vm_type_prob_0),
    .type_prob_1(vm_type_prob_1),
    .type_prob_2(vm_type_prob_2),
    .type_prob_3(vm_type_prob_3),
    .type_prob_4(vm_type_prob_4),
    .type_prob_5(vm_type_prob_5),
    .type_id(vm_type_id),
    .type_valid(vm_type_valid),
    .jammer_prob(vm_jammer_prob),
    .jammer_valid(vm_jammer_valid),
    .valid_out(vm_valid_out),
    .is_threat(vm_is_threat),
    .threat_type(vm_threat_type),
    .jammer_flag(vm_jammer_flag),
    .confidence(vm_confidence),
    .timestamp()
);

// ============================================================================
// Helper Tasks
// ============================================================================
task test_passed(input string test_name);
    begin
        $display("[✓ PASS] %s", test_name);
        tests_passed = tests_passed + 1;
    end
endtask

task test_failed(input string test_name, input string reason);
    begin
        $display("[✗ FAIL] %s - %s", test_name, reason);
        tests_failed = tests_failed + 1;
    end
endtask

task send_rf_samples(input integer count, input [7:0] i_pattern, input [7:0] q_pattern);
    integer i;
    begin
        for (i = 0; i < count; i = i + 1) begin
            @(posedge clk);
            tc_i_data = i_pattern + i[3:0];
            tc_q_data = q_pattern + i[3:0];
            tc_valid_in = 1;
            
            jd_i_data = i_pattern + i[3:0];
            jd_q_data = q_pattern + i[3:0];
            jd_valid_in = 1;
            
            td_i_data = i_pattern + i[3:0];
            td_q_data = q_pattern + i[3:0];
            td_valid_in = 1;
        end
        tc_valid_in = 0;
        jd_valid_in = 0;
        td_valid_in = 0;
    end
endtask

task report_summary;
    begin
        $display("\n");
        $display("========================================");
        $display("TEST SUMMARY");
        $display("========================================");
        $display("Tests Passed: %d", tests_passed);
        $display("Tests Failed: %d", tests_failed);
        $display("Total Tests:  %d", tests_passed + tests_failed);
        if (tests_failed == 0) begin
            $display("Result: ALL TESTS PASSED ✓");
        end else begin
            $display("Result: SOME TESTS FAILED ✗");
        end
        $display("========================================");
    end
endtask

// ============================================================================
// Main Test Procedure
// ============================================================================
initial begin
    $display("\n");
    $display("╔════════════════════════════════════════╗");
    $display("║ SkyShield AI v3.0 - Refactored RTL    ║");
    $display("║ Comprehensive Verification Testbench  ║");
    $display("╚════════════════════════════════════════╝");
    $display("\n");

    // Initialize
    clk = 0;
    rst_n = 0;
    tc_valid_in = 0;
    jd_valid_in = 0;
    td_valid_in = 0;
    te_valid_in = 0;
    vm_valid_in = 0;
    
    #20 rst_n = 1;
    #10;

    // ========================================================================
    // Test 1: Type Classifier Verification
    // ========================================================================
    $display("\n═══════════════════════════════════════");
    $display("TEST SUITE 1: TYPE CLASSIFIER");
    $display("═══════════════════════════════════════");
    
    $display("\n[Test 1.1] DJI-like signal pattern");
    send_rf_samples(INPUT_LENGTH, 8'hA0, 8'hAA);
    #500;
    
    if (tc_valid_out && tc_class_id == 3'b001) begin
        test_passed("Type Classifier: DJI detection");
    end else begin
        test_failed("Type Classifier: DJI detection", 
                   $sformatf("Got class_id=%d, expected 1", tc_class_id));
    end
    
    $display("\n[Test 1.2] FPV-like signal pattern");
    send_rf_samples(INPUT_LENGTH, 8'h80, 8'h75);
    #500;
    
    if (tc_valid_out && tc_class_id == 3'b010) begin
        test_passed("Type Classifier: FPV detection");
    end else begin
        test_failed("Type Classifier: FPV detection",
                   $sformatf("Got class_id=%d, expected 2", tc_class_id));
    end
    
    $display("\n[Test 1.3] Benign signal (uniform low amplitude)");
    send_rf_samples(INPUT_LENGTH, 8'h30, 8'h35);
    #500;
    
    if (tc_valid_out && tc_class_id == 3'b000) begin
        test_passed("Type Classifier: Benign detection");
    end else begin
        test_failed("Type Classifier: Benign detection",
                   $sformatf("Got class_id=%d, expected 0", tc_class_id));
    end

    // ========================================================================
    // Test 2: Jammer Detector Verification
    // ========================================================================
    $display("\n═══════════════════════════════════════");
    $display("TEST SUITE 2: JAMMER DETECTOR");
    $display("═══════════════════════════════════════");
    
    $display("\n[Test 2.1] Clean signal (no jammer)");
    send_rf_samples(INPUT_LENGTH, 8'h7F, 8'h7F);
    #500;
    
    if (jd_valid_out && !jd_is_jammer && jd_jammer_prob < 100) begin
        test_passed("Jammer Detector: Clean signal classification");
    end else begin
        test_failed("Jammer Detector: Clean signal classification",
                   $sformatf("jammer_prob=%d, is_jammer=%b", jd_jammer_prob, jd_is_jammer));
    end
    
    $display("\n[Test 2.2] Jammer signal (high noise)");
    integer jd_i;
    for (jd_i = 0; jd_i < INPUT_LENGTH; jd_i = jd_i + 1) begin
        @(posedge clk);
        jd_i_data = $random % 256;
        jd_q_data = $random % 256;
        jd_valid_in = 1;
    end
    jd_valid_in = 0;
    #500;
    
    if (jd_valid_out && jd_jammer_prob > 150) begin
        test_passed("Jammer Detector: High noise classification");
    end else begin
        test_failed("Jammer Detector: High noise classification",
                   $sformatf("jammer_prob=%d, expected >150", jd_jammer_prob));
    end

    // ========================================================================
    // Test 3: Threat Detector Verification
    // ========================================================================
    $display("\n═══════════════════════════════════════");
    $display("TEST SUITE 3: THREAT DETECTOR");
    $display("═══════════════════════════════════════");
    
    $display("\n[Test 3.1] Benign signal (low amplitude)");
    send_rf_samples(INPUT_LENGTH, 8'h40, 8'h45);
    #500;
    
    if (td_valid_out && !td_is_threat && td_threat_prob < 100) begin
        test_passed("Threat Detector: Benign signal classification");
    end else begin
        test_failed("Threat Detector: Benign signal classification",
                   $sformatf("threat_prob=%d, is_threat=%b", td_threat_prob, td_is_threat));
    end
    
    $display("\n[Test 3.2] Threat signal (high amplitude)");
    send_rf_samples(INPUT_LENGTH, 8'hC0, 8'hC5);
    #500;
    
    if (td_valid_out && td_threat_prob > 150) begin
        test_passed("Threat Detector: Threat signal classification");
    end else begin
        test_failed("Threat Detector: Threat signal classification",
                   $sformatf("threat_prob=%d, expected >150", td_threat_prob));
    end

    // ========================================================================
    // Test 4: Tracking Engine Verification (CRITICAL)
    // ========================================================================
    $display("\n═══════════════════════════════════════");
    $display("TEST SUITE 4: TRACKING ENGINE");
    $display("═══════════════════════════════════════");
    
    $display("\n[Test 4.1] Create new track (DJI drone)");
    @(posedge clk);
    te_valid_in = 1;
    te_is_threat = 1;
    te_threat_type = 3'b001;  // DJI
    te_confidence = 8'hE0;
    te_signal_bearing = 16'd1000;
    te_signal_strength = 16'd2000;
    te_timestamp = 32'h00000001;
    
    @(posedge clk);
    te_valid_in = 0;
    #50;
    
    if (te_num_active_tracks == 4'b0001) begin
        test_passed("Tracking Engine: Create new track");
    end else begin
        test_failed("Tracking Engine: Create new track",
                   $sformatf("num_tracks=%d, expected 1", te_num_active_tracks));
    end
    
    // Verify packed array output works
    if (te_track_id[0] == 32'h00000001 && te_track_type[0] == 3'b001) begin
        test_passed("Tracking Engine: Packed array output (track_id, track_type)");
    end else begin
        test_failed("Tracking Engine: Packed array output",
                   $sformatf("track_id[0]=%h, track_type[0]=%b", 
                            te_track_id[0], te_track_type[0]));
    end
    
    $display("\n[Test 4.2] Create multiple tracks (no saturation)");
    integer track_idx;
    for (track_idx = 1; track_idx < 10; track_idx = track_idx + 1) begin
        @(posedge clk);
        te_valid_in = 1;
        te_is_threat = 1;
        te_threat_type = 3'b001;
        te_confidence = 8'hE0;
        te_signal_bearing = 16'd1000 + (track_idx * 16'd500);
        te_timestamp = 32'h00000001 + track_idx;
        
        @(posedge clk);
        te_valid_in = 0;
        #10;
    end
    #50;
    
    if (te_num_active_tracks == 4'b1010) begin  // Should be 10
        test_passed("Tracking Engine: Multiple track creation (no saturation)");
    end else begin
        test_failed("Tracking Engine: Multiple track creation",
                   $sformatf("num_tracks=%d, expected 10", te_num_active_tracks));
    end
    
    $display("\n[Test 4.3] Track matching (bearing update)");
    @(posedge clk);
    te_valid_in = 1;
    te_is_threat = 1;
    te_threat_type = 3'b001;
    te_signal_bearing = 16'd1050;  // Within ±500 of original 1000
    te_timestamp = 32'h00000100;
    
    @(posedge clk);
    te_valid_in = 0;
    #50;
    
    if (te_num_active_tracks == 4'b1010) begin  // Should still be 10 (matched, not new)
        test_passed("Tracking Engine: Track matching (no new track created)");
    end else begin
        test_failed("Tracking Engine: Track matching",
                   $sformatf("num_tracks=%d, expected 10", te_num_active_tracks));
    end

    // ========================================================================
    // Test 5: Voting Module Verification
    // ========================================================================
    $display("\n═══════════════════════════════════════");
    $display("TEST SUITE 5: VOTING MODULE");
    $display("═══════════════════════════════════════");
    
    $display("\n[Test 5.1] All detectors agree (threat)");
    @(posedge clk);
    vm_valid_in = 1;
    vm_threat_prob = 8'd220;
    vm_threat_valid = 1;
    vm_type_prob_0 = 8'h10;
    vm_type_prob_1 = 8'hF0;  // High confidence DJI
    vm_type_prob_2 = 8'h20;
    vm_type_prob_3 = 8'h20;
    vm_type_prob_4 = 8'h20;
    vm_type_prob_5 = 8'h20;
    vm_type_id = 3'b001;
    vm_type_valid = 1;
    vm_jammer_prob = 8'd50;
    vm_jammer_valid = 1;
    
    @(posedge clk);
    vm_valid_in = 0;
    #50;
    
    if (vm_valid_out && vm_is_threat && vm_threat_type == 3'b001) begin
        test_passed("Voting Module: Consensus threat decision");
    end else begin
        test_failed("Voting Module: Consensus threat decision",
                   $sformatf("is_threat=%b, threat_type=%b", vm_is_threat, vm_threat_type));
    end
    
    $display("\n[Test 5.2] Jammer detection (jammer_flag)");
    @(posedge clk);
    vm_valid_in = 1;
    vm_threat_prob = 8'd150;
    vm_threat_valid = 1;
    vm_type_prob_0 = 8'h80;
    vm_type_prob_1 = 8'h80;
    vm_type_prob_2 = 8'h80;
    vm_type_prob_3 = 8'h80;
    vm_type_prob_4 = 8'h80;
    vm_type_prob_5 = 8'hE0;  // High jammer probability
    vm_type_id = 3'b101;
    vm_type_valid = 1;
    vm_jammer_prob = 8'd220;  // Clearly a jammer
    vm_jammer_valid = 1;
    
    @(posedge clk);
    vm_valid_in = 0;
    #50;
    
    if (vm_valid_out && vm_jammer_flag) begin
        test_passed("Voting Module: Jammer flag detection");
    end else begin
        test_failed("Voting Module: Jammer flag detection",
                   $sformatf("valid_out=%b, jammer_flag=%b", vm_valid_out, vm_jammer_flag));
    end

    // ========================================================================
    // Generate Summary Report
    // ========================================================================
    #100;
    report_summary();
    
    $finish;
end

endmodule
