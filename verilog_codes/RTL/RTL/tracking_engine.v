`timescale 1ns / 1ps
// ============================================================================
// SkyShield AI v3.0 - Tracking Engine
// Multi-frame threat tracking with trajectory prediction
// ============================================================================

module tracking_engine #(
    parameter MAX_TRACKS = 16,
    parameter TRACK_AGE_LIMIT = 32,
    parameter VELOCITY_WINDOW = 8
)(
    input  wire              clk,
    input  wire              rst_n,
    input  wire              valid_in,
    
    // Detection Input
    input  wire [2:0]       threat_type,
    input  wire              is_threat,
    input  wire [7:0]       confidence,
    input  wire [15:0]      signal_bearing,   // Direction estimate
    input  wire [15:0]      signal_strength,  // RSSI estimate
    input  wire [31:0]      timestamp,
    
    // Track Output
    output reg              valid_out,
    output reg  [3:0]       num_active_tracks,
    output reg  [31:0]      track_id [0:MAX_TRACKS-1],
    output reg  [15:0]      track_age [0:MAX_TRACKS-1],
    output reg  [15:0]      track_velocity [0:MAX_TRACKS-1],
    output reg  [2:0]       track_type [0:MAX_TRACKS-1],
    output reg              track_confirmed [0:MAX_TRACKS-1]
);

// ============================================================================
// Track Entry Structure
// ============================================================================
typedef struct {
    reg [31:0] id;
    reg [15:0] age;
    reg [15:0] last_bearing;
    reg [15:0] velocity;
    reg [2:0]  threat_type;
    reg        confirmed;
    reg        active;
} track_t;

track_t tracks [0:MAX_TRACKS-1];

// ============================================================================
// Internal Signals
// ============================================================================
reg [3:0] next_track_idx;
reg match_found;
reg [3:0] match_idx;

// ============================================================================
// Track Management
// ============================================================================
integer i;
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
        for (i = 0; i < MAX_TRACKS; i = i + 1) begin
            tracks[i].active <= 0;
            tracks[i].confirmed <= 0;
            tracks[i].age <= 0;
        end
        num_active_tracks <= 0;
        valid_out <= 0;
        next_track_idx <= 0;
    end else if (valid_in && is_threat) begin
        valid_out <= 1'b1;
        
        // Try to match with existing track
        match_found <= 0;
        for (i = 0; i < MAX_TRACKS; i = i + 1) begin
            if (tracks[i].active && 
                (tracks[i].threat_type == threat_type) &&
                ($abs($signed(tracks[i].last_bearing) - $signed(signal_bearing)) < 16'd500)) begin
                match_found <= 1;
                match_idx <= i;
            end
        end
        
        if (match_found) begin
            // Update existing track
            tracks[match_idx].age <= tracks[match_idx].age + 1;
            tracks[match_idx].velocity <= $abs($signed(signal_bearing) - $signed(tracks[match_idx].last_bearing));
            tracks[match_idx].last_bearing <= signal_bearing;
            
            // Confirm track after 3 detections
            if (tracks[match_idx].age >= 3) begin
                tracks[match_idx].confirmed <= 1;
            end
        end else begin
            // Create new track
            tracks[next_track_idx].id <= timestamp;
            tracks[next_track_idx].age <= 1;
            tracks[next_track_idx].last_bearing <= signal_bearing;
            tracks[next_track_idx].velocity <= 0;
            tracks[next_track_idx].threat_type <= threat_type;
            tracks[next_track_idx].confirmed <= 0;
            tracks[next_track_idx].active <= 1;
            
            next_track_idx <= next_track_idx + 1;
        end
        
        // Age out old tracks
        for (i = 0; i < MAX_TRACKS; i = i + 1) begin
            if (tracks[i].active && (tracks[i].age > TRACK_AGE_LIMIT)) begin
                tracks[i].active <= 0;
            end
        end
        
        // Count active tracks
        num_active_tracks <= 0;
        for (i = 0; i < MAX_TRACKS; i = i + 1) begin
            if (tracks[i].active) begin
                num_active_tracks <= num_active_tracks + 1;
            end
        end
    end else begin
        valid_out <= 1'b0;
    end
end

// ============================================================================
// Output Assignment
// ============================================================================
always @(posedge clk) begin
    for (i = 0; i < MAX_TRACKS; i = i + 1) begin
        track_id[i] <= tracks[i].id;
        track_age[i] <= tracks[i].age;
        track_velocity[i] <= tracks[i].velocity;
        track_type[i] <= tracks[i].threat_type;
        track_confirmed[i] <= tracks[i].confirmed;
    end
end

endmodule
