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
    
    // Track Output (flattened for Verilog)
    output reg              valid_out,
    output reg  [3:0]       num_active_tracks,
    output wire [31:0]      track_id_0,
    output wire [31:0]      track_id_1,
    output wire [31:0]      track_id_2,
    output wire [31:0]      track_id_3,
    output wire [31:0]      track_id_4,
    output wire [31:0]      track_id_5,
    output wire [31:0]      track_id_6,
    output wire [31:0]      track_id_7,
    output wire [31:0]      track_id_8,
    output wire [31:0]      track_id_9,
    output wire [31:0]      track_id_10,
    output wire [31:0]      track_id_11,
    output wire [31:0]      track_id_12,
    output wire [31:0]      track_id_13,
    output wire [31:0]      track_id_14,
    output wire [31:0]      track_id_15,
    
    output wire [15:0]      track_age_0,
    output wire [15:0]      track_age_1,
    output wire [15:0]      track_age_2,
    output wire [15:0]      track_age_3,
    output wire [15:0]      track_age_4,
    output wire [15:0]      track_age_5,
    output wire [15:0]      track_age_6,
    output wire [15:0]      track_age_7,
    output wire [15:0]      track_age_8,
    output wire [15:0]      track_age_9,
    output wire [15:0]      track_age_10,
    output wire [15:0]      track_age_11,
    output wire [15:0]      track_age_12,
    output wire [15:0]      track_age_13,
    output wire [15:0]      track_age_14,
    output wire [15:0]      track_age_15,
    
    output wire [15:0]      track_velocity_0,
    output wire [15:0]      track_velocity_1,
    output wire [15:0]      track_velocity_2,
    output wire [15:0]      track_velocity_3,
    output wire [15:0]      track_velocity_4,
    output wire [15:0]      track_velocity_5,
    output wire [15:0]      track_velocity_6,
    output wire [15:0]      track_velocity_7,
    output wire [15:0]      track_velocity_8,
    output wire [15:0]      track_velocity_9,
    output wire [15:0]      track_velocity_10,
    output wire [15:0]      track_velocity_11,
    output wire [15:0]      track_velocity_12,
    output wire [15:0]      track_velocity_13,
    output wire [15:0]      track_velocity_14,
    output wire [15:0]      track_velocity_15,
    
    output wire [2:0]       track_type_0,
    output wire [2:0]       track_type_1,
    output wire [2:0]       track_type_2,
    output wire [2:0]       track_type_3,
    output wire [2:0]       track_type_4,
    output wire [2:0]       track_type_5,
    output wire [2:0]       track_type_6,
    output wire [2:0]       track_type_7,
    output wire [2:0]       track_type_8,
    output wire [2:0]       track_type_9,
    output wire [2:0]       track_type_10,
    output wire [2:0]       track_type_11,
    output wire [2:0]       track_type_12,
    output wire [2:0]       track_type_13,
    output wire [2:0]       track_type_14,
    output wire [2:0]       track_type_15,
    
    output wire             track_confirmed_0,
    output wire             track_confirmed_1,
    output wire             track_confirmed_2,
    output wire             track_confirmed_3,
    output wire             track_confirmed_4,
    output wire             track_confirmed_5,
    output wire             track_confirmed_6,
    output wire             track_confirmed_7,
    output wire             track_confirmed_8,
    output wire             track_confirmed_9,
    output wire             track_confirmed_10,
    output wire             track_confirmed_11,
    output wire             track_confirmed_12,
    output wire             track_confirmed_13,
    output wire             track_confirmed_14,
    output wire             track_confirmed_15
);

// ============================================================================
// Track Storage (Single-dimensional arrays in Verilog)
// ============================================================================
reg [31:0] track_id_mem [0:MAX_TRACKS-1];
reg [15:0] track_age_mem [0:MAX_TRACKS-1];
reg [15:0] track_last_bearing [0:MAX_TRACKS-1];
reg [15:0] track_velocity_mem [0:MAX_TRACKS-1];
reg [2:0]  track_type_mem [0:MAX_TRACKS-1];
reg        track_confirmed_mem [0:MAX_TRACKS-1];
reg        track_active [0:MAX_TRACKS-1];

reg [3:0]  next_track_idx;
reg        match_found;
reg [3:0]  match_idx;
integer i;
integer k;
integer active_count;

// ============================================================================
// Output Assignment (Flattened)
// ============================================================================
(* keep = "true" *) assign track_id_0       = track_id_mem[0];
(* keep = "true" *) assign track_id_1       = track_id_mem[1];
(* keep = "true" *) assign track_id_2       = track_id_mem[2];
(* keep = "true" *) assign track_id_3       = track_id_mem[3];
(* keep = "true" *) assign track_id_4       = track_id_mem[4];
(* keep = "true" *) assign track_id_5       = track_id_mem[5];
(* keep = "true" *) assign track_id_6       = track_id_mem[6];
(* keep = "true" *) assign track_id_7       = track_id_mem[7];
(* keep = "true" *) assign track_id_8       = track_id_mem[8];
(* keep = "true" *) assign track_id_9       = track_id_mem[9];
(* keep = "true" *) assign track_id_10      = track_id_mem[10];
(* keep = "true" *) assign track_id_11      = track_id_mem[11];
(* keep = "true" *) assign track_id_12      = track_id_mem[12];
(* keep = "true" *) assign track_id_13      = track_id_mem[13];
(* keep = "true" *) assign track_id_14      = track_id_mem[14];
(* keep = "true" *) assign track_id_15      = track_id_mem[15];

(* keep = "true" *) assign track_age_0      = track_age_mem[0];
(* keep = "true" *) assign track_age_1      = track_age_mem[1];
(* keep = "true" *) assign track_age_2      = track_age_mem[2];
(* keep = "true" *) assign track_age_3      = track_age_mem[3];
(* keep = "true" *) assign track_age_4      = track_age_mem[4];
(* keep = "true" *) assign track_age_5      = track_age_mem[5];
(* keep = "true" *) assign track_age_6      = track_age_mem[6];
(* keep = "true" *) assign track_age_7      = track_age_mem[7];
(* keep = "true" *) assign track_age_8      = track_age_mem[8];
(* keep = "true" *) assign track_age_9      = track_age_mem[9];
(* keep = "true" *) assign track_age_10     = track_age_mem[10];
(* keep = "true" *) assign track_age_11     = track_age_mem[11];
(* keep = "true" *) assign track_age_12     = track_age_mem[12];
(* keep = "true" *) assign track_age_13     = track_age_mem[13];
(* keep = "true" *) assign track_age_14     = track_age_mem[14];
(* keep = "true" *) assign track_age_15     = track_age_mem[15];

(* keep = "true" *) assign track_velocity_0  = track_velocity_mem[0];
(* keep = "true" *) assign track_velocity_1  = track_velocity_mem[1];
(* keep = "true" *) assign track_velocity_2  = track_velocity_mem[2];
(* keep = "true" *) assign track_velocity_3  = track_velocity_mem[3];
(* keep = "true" *) assign track_velocity_4  = track_velocity_mem[4];
(* keep = "true" *) assign track_velocity_5  = track_velocity_mem[5];
(* keep = "true" *) assign track_velocity_6  = track_velocity_mem[6];
(* keep = "true" *) assign track_velocity_7  = track_velocity_mem[7];
(* keep = "true" *) assign track_velocity_8  = track_velocity_mem[8];
(* keep = "true" *) assign track_velocity_9  = track_velocity_mem[9];
(* keep = "true" *) assign track_velocity_10 = track_velocity_mem[10];
(* keep = "true" *) assign track_velocity_11 = track_velocity_mem[11];
(* keep = "true" *) assign track_velocity_12 = track_velocity_mem[12];
(* keep = "true" *) assign track_velocity_13 = track_velocity_mem[13];
(* keep = "true" *) assign track_velocity_14 = track_velocity_mem[14];
(* keep = "true" *) assign track_velocity_15 = track_velocity_mem[15];

(* keep = "true" *) assign track_type_0     = track_type_mem[0];
(* keep = "true" *) assign track_type_1     = track_type_mem[1];
(* keep = "true" *) assign track_type_2     = track_type_mem[2];
(* keep = "true" *) assign track_type_3     = track_type_mem[3];
(* keep = "true" *) assign track_type_4     = track_type_mem[4];
(* keep = "true" *) assign track_type_5     = track_type_mem[5];
(* keep = "true" *) assign track_type_6     = track_type_mem[6];
(* keep = "true" *) assign track_type_7     = track_type_mem[7];
(* keep = "true" *) assign track_type_8     = track_type_mem[8];
(* keep = "true" *) assign track_type_9     = track_type_mem[9];
(* keep = "true" *) assign track_type_10    = track_type_mem[10];
(* keep = "true" *) assign track_type_11    = track_type_mem[11];
(* keep = "true" *) assign track_type_12    = track_type_mem[12];
(* keep = "true" *) assign track_type_13    = track_type_mem[13];
(* keep = "true" *) assign track_type_14    = track_type_mem[14];
(* keep = "true" *) assign track_type_15    = track_type_mem[15];

(* keep = "true" *) assign track_confirmed_0  = track_confirmed_mem[0];
(* keep = "true" *) assign track_confirmed_1  = track_confirmed_mem[1];
(* keep = "true" *) assign track_confirmed_2  = track_confirmed_mem[2];
(* keep = "true" *) assign track_confirmed_3  = track_confirmed_mem[3];
(* keep = "true" *) assign track_confirmed_4  = track_confirmed_mem[4];
(* keep = "true" *) assign track_confirmed_5  = track_confirmed_mem[5];
(* keep = "true" *) assign track_confirmed_6  = track_confirmed_mem[6];
(* keep = "true" *) assign track_confirmed_7  = track_confirmed_mem[7];
(* keep = "true" *) assign track_confirmed_8  = track_confirmed_mem[8];
(* keep = "true" *) assign track_confirmed_9  = track_confirmed_mem[9];
(* keep = "true" *) assign track_confirmed_10 = track_confirmed_mem[10];
(* keep = "true" *) assign track_confirmed_11 = track_confirmed_mem[11];
(* keep = "true" *) assign track_confirmed_12 = track_confirmed_mem[12];
(* keep = "true" *) assign track_confirmed_13 = track_confirmed_mem[13];
(* keep = "true" *) assign track_confirmed_14 = track_confirmed_mem[14];
(* keep = "true" *) assign track_confirmed_15 = track_confirmed_mem[15];

// ============================================================================
// Track Management Logic
// ============================================================================
always @(posedge clk) begin
    if (!rst_n) begin
        for (i = 0; i < MAX_TRACKS; i = i + 1) begin
            track_active[i] <= 1'b0;
            track_confirmed_mem[i] <= 1'b0;
            track_age_mem[i] <= 16'h0000;
            track_velocity_mem[i] <= 16'h0000;
            track_type_mem[i] <= 3'b000;
            track_id_mem[i] <= 32'h00000000;
            track_last_bearing[i] <= 16'h0000;
        end
        num_active_tracks <= 4'b0000;
        valid_out <= 1'b0;
        next_track_idx <= 4'h0;
        match_found <= 1'b0;
        match_idx <= 4'h0;
    end else if (valid_in && is_threat) begin
        valid_out <= 1'b1;
        
        // ENHANCEMENT: Age out tracks that haven't been updated (prevent saturation)
        for (i = 0; i < MAX_TRACKS; i = i + 1) begin
            if (track_active[i]) begin
                // Increment age counter for all active tracks
                track_age_mem[i] <= track_age_mem[i] + 16'h0001;
                // Remove tracks older than 255 samples without update
                if (track_age_mem[i] >= 16'hFFFF) begin
                    track_active[i] <= 1'b0;
                    track_confirmed_mem[i] <= 1'b0;
                end
            end
        end
        
        // Matching logic: find existing track with same type and similar bearing
        match_found <= 1'b0;
        for (i = 0; i < MAX_TRACKS; i = i + 1) begin
            if (track_active[i] && (track_type_mem[i] == threat_type)) begin
                // Simplified bearing match: within ±500
                if ((signal_bearing >= track_last_bearing[i] - 16'd500) &&
                    (signal_bearing <= track_last_bearing[i] + 16'd500)) begin
                    match_found <= 1'b1;
                    match_idx <= i[3:0];
                end
            end
        end
        
        if (match_found) begin
            // Update existing track (reset age on update)
            track_age_mem[match_idx] <= 16'h0001;
            track_velocity_mem[match_idx] <= (signal_bearing > track_last_bearing[match_idx]) ?
                                             (signal_bearing - track_last_bearing[match_idx]) :
                                             (track_last_bearing[match_idx] - signal_bearing);
            track_last_bearing[match_idx] <= signal_bearing;
            
            // Confirm track after 3 detections
            if (track_age_mem[match_idx] >= 16'h0003) begin
                track_confirmed_mem[match_idx] <= 1'b1;
            end
        end else begin
            // Create new track if slot available
            // ENHANCEMENT: Find first inactive slot instead of linear increment
            for (i = 0; i < MAX_TRACKS; i = i + 1) begin
                if (!track_active[i]) begin
                    track_id_mem[i] <= timestamp;
                    track_age_mem[i] <= 16'h0001;
                    track_last_bearing[i] <= signal_bearing;
                    track_velocity_mem[i] <= 16'h0000;
                    track_type_mem[i] <= threat_type;
                    track_confirmed_mem[i] <= 1'b0;
                    track_active[i] <= 1'b1;
                    // Only increment next_track_idx if this was the next slot
                    if (i == next_track_idx && next_track_idx < (MAX_TRACKS - 1)) begin
                        next_track_idx <= next_track_idx + 4'h1;
                    end
                end
            end
        end
    end else begin
        valid_out <= 1'b0;
    end

    active_count = 0;
    for (k = 0; k < MAX_TRACKS; k = k + 1) begin
        if (track_active[k])
            active_count = active_count + 1;
    end
    num_active_tracks <= active_count[3:0];
end

endmodule
