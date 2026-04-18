`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Tracking Engine Testbench
// ============================================================================

module tb_tracking_engine;

parameter MAX_TRACKS = 16;

reg clk;
reg rst_n;
reg valid_in;
reg [2:0] threat_type;
reg is_threat;
reg [7:0] confidence;
reg [15:0] signal_bearing;
reg [15:0] signal_strength;
reg [31:0] timestamp;

wire valid_out;
wire [3:0] num_active_tracks;
wire [31:0] track_id_0;
wire [15:0] track_age_0;
wire [15:0] track_velocity_0;
wire [2:0] track_type_0;
wire track_confirmed_0;

tracking_engine #(
    .MAX_TRACKS(MAX_TRACKS)
) uut (
    .clk(clk),
    .rst_n(rst_n),
    .valid_in(valid_in),
    .threat_type(threat_type),
    .is_threat(is_threat),
    .confidence(confidence),
    .signal_bearing(signal_bearing),
    .signal_strength(signal_strength),
    .timestamp(timestamp),
    .valid_out(valid_out),
    .num_active_tracks(num_active_tracks),
    .track_id_0(track_id_0),
    .track_id_1(),
    .track_id_2(),
    .track_id_3(),
    .track_id_4(),
    .track_id_5(),
    .track_id_6(),
    .track_id_7(),
    .track_id_8(),
    .track_id_9(),
    .track_id_10(),
    .track_id_11(),
    .track_id_12(),
    .track_id_13(),
    .track_id_14(),
    .track_id_15(),
    .track_age_0(track_age_0),
    .track_age_1(),
    .track_age_2(),
    .track_age_3(),
    .track_age_4(),
    .track_age_5(),
    .track_age_6(),
    .track_age_7(),
    .track_age_8(),
    .track_age_9(),
    .track_age_10(),
    .track_age_11(),
    .track_age_12(),
    .track_age_13(),
    .track_age_14(),
    .track_age_15(),
    .track_velocity_0(track_velocity_0),
    .track_velocity_1(),
    .track_velocity_2(),
    .track_velocity_3(),
    .track_velocity_4(),
    .track_velocity_5(),
    .track_velocity_6(),
    .track_velocity_7(),
    .track_velocity_8(),
    .track_velocity_9(),
    .track_velocity_10(),
    .track_velocity_11(),
    .track_velocity_12(),
    .track_velocity_13(),
    .track_velocity_14(),
    .track_velocity_15(),
    .track_type_0(track_type_0),
    .track_type_1(),
    .track_type_2(),
    .track_type_3(),
    .track_type_4(),
    .track_type_5(),
    .track_type_6(),
    .track_type_7(),
    .track_type_8(),
    .track_type_9(),
    .track_type_10(),
    .track_type_11(),
    .track_type_12(),
    .track_type_13(),
    .track_type_14(),
    .track_type_15(),
    .track_confirmed_0(track_confirmed_0),
    .track_confirmed_1(),
    .track_confirmed_2(),
    .track_confirmed_3(),
    .track_confirmed_4(),
    .track_confirmed_5(),
    .track_confirmed_6(),
    .track_confirmed_7(),
    .track_confirmed_8(),
    .track_confirmed_9(),
    .track_confirmed_10(),
    .track_confirmed_11(),
    .track_confirmed_12(),
    .track_confirmed_13(),
    .track_confirmed_14(),
    .track_confirmed_15()
);

always #5 clk = ~clk;

initial begin
    $display("========================================");
    $display("Tracking Engine Testbench");
    $display("========================================");
    
    clk = 0;
    rst_n = 0;
    valid_in = 0;
    threat_type = 0;
    is_threat = 0;
    confidence = 0;
    signal_bearing = 0;
    signal_strength = 0;
    timestamp = 0;
    
    #20 rst_n = 1;
    #20;
    
    $display("\n[Test 1] Create first track (DJI drone)...");
    is_threat = 1;
    threat_type = 1;  // DJI
    confidence = 8'hE0;
    signal_bearing = 16'd1000;
    signal_strength = 16'd2000;
    timestamp = 32'h00000001;
    
    // Inject 5 consecutive detections to build up track age and confidence
    repeat(5) begin
        @(posedge clk);
        timestamp = timestamp + 32'h00000001;
        signal_bearing = signal_bearing + 16'd10;  // Slight movement
        valid_in = 1;
        @(posedge clk);
        valid_in = 0;
        #20;
    end
    
    $display("[Track 0] ID=0x%h, Age=%d, Velocity=%d, Type=%d, Confirmed=%b",
             track_id_0, track_age_0, track_velocity_0, track_type_0, track_confirmed_0);
    
    #20;
    $display("\n[Test 2] Create second track (Parrot drone)...");
    is_threat = 1;
    threat_type = 2;  // Parrot
    confidence = 8'hD0;
    signal_bearing = 16'd500;
    signal_strength = 16'd1500;
    timestamp = 32'h00000010;
    
    repeat(4) begin
        @(posedge clk);
        timestamp = timestamp + 32'h00000001;
        signal_bearing = signal_bearing - 16'd5;  // Moving
        valid_in = 1;
        @(posedge clk);
        valid_in = 0;
        #20;
    end
    
    $display("[Test 3] Active tracks: %d", num_active_tracks);
    
    #40;
    $display("\n========================================");
    $display("Testbench Complete");
    $display("========================================");
    $finish;
end

endmodule
