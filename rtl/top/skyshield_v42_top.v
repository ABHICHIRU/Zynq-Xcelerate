`timescale 1ns / 1ps
// ============================================================================
// SkyShield v4.2 - RTL Inference Top
// Shared 1D backbone + 3 heads (6-class type head) + deterministic voting
// Streaming I/Q input: (2, 512)
// ============================================================================

module skyshield_v42_top (
    input  wire               clk,
    input  wire               rst_n,
    input  wire               sample_valid,
    input  wire signed [15:0]  i_sample,
    input  wire signed [15:0]  q_sample,

    output wire               sample_ready,
    output reg                result_valid,
    output reg                threat_flag,
    output reg                jammer_flag,
    output reg  [2:0]        type_id,
    output reg  [3:0]        action_code,
    output reg  [7:0]        confidence,
    output reg  [31:0]       result_data
);

    localparam WINDOW_SIZE = 512;

    reg signed [15:0] i_buf [0:WINDOW_SIZE-1];
    reg signed [15:0] q_buf [0:WINDOW_SIZE-1];
    reg [8:0]         sample_count;
    reg               frame_pending;

    wire [WINDOW_SIZE*16-1:0] i_window_bus;
    wire [WINDOW_SIZE*16-1:0] q_window_bus;

    wire [64*16-1:0] feature_bus;

    wire [7:0] threat_prob_w;
    wire [7:0] type_prob_0_w;
    wire [7:0] type_prob_1_w;
    wire [7:0] type_prob_2_w;
    wire [7:0] jammer_prob_w;

    wire threat_flag_w;
    wire jammer_flag_w;
    wire [2:0] type_id_w;
    wire [3:0] action_code_w;
    wire [7:0] confidence_w;
    wire [31:0] result_data_w;
    wire [7:0] type_prob_3_w;
    wire [7:0] type_prob_4_w;
    wire [7:0] type_prob_5_w;
    wire       final_threat_flag_w;
    wire       final_jammer_flag_w;
    wire [2:0] final_type_id_w;

    integer pi;

    genvar gi;
    generate
        for (gi = 0; gi < WINDOW_SIZE; gi = gi + 1) begin : PACK_INPUTS
            assign i_window_bus[(gi*16) +: 16] = i_buf[gi];
            assign q_window_bus[(gi*16) +: 16] = q_buf[gi];
        end
    endgenerate

    assign sample_ready = ~frame_pending;

    skyshield_backbone_rtl u_backbone (
        .i_window_bus(i_window_bus),
        .q_window_bus(q_window_bus),
        .feature_bus(feature_bus)
    );

    skyshield_threat_head u_threat_head (
        .feature_bus(feature_bus),
        .threat_prob(threat_prob_w),
        .threat_flag(threat_flag_w)
    );

    skyshield_type_head u_type_head (
        .feature_bus(feature_bus),
        .type_prob_0(type_prob_0_w),
        .type_prob_1(type_prob_1_w),
        .type_prob_2(type_prob_2_w),
        .type_prob_3(type_prob_3_w),
        .type_prob_4(type_prob_4_w),
        .type_prob_5(type_prob_5_w),
        .type_id(type_id_w)
    );

    skyshield_jammer_head u_jammer_head (
        .feature_bus(feature_bus),
        .jammer_prob(jammer_prob_w),
        .jammer_flag(jammer_flag_w)
    );

    skyshield_voting_logic u_voting (
        .threat_prob(threat_prob_w),
        .threat_flag(threat_flag_w),
        .type_prob_0(type_prob_0_w),
        .type_prob_1(type_prob_1_w),
        .type_prob_2(type_prob_2_w),
        .type_prob_3(type_prob_3_w),
        .type_prob_4(type_prob_4_w),
        .type_prob_5(type_prob_5_w),
        .type_id(type_id_w),
        .jammer_prob(jammer_prob_w),
        .jammer_flag(jammer_flag_w),
        .action_code(action_code_w),
        .confidence(confidence_w),
        .final_threat_flag(final_threat_flag_w),
        .final_jammer_flag(final_jammer_flag_w),
        .final_type_id(final_type_id_w),
        .result_data(result_data_w)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            sample_count <= 9'd0;
            frame_pending <= 1'b0;
            result_valid <= 1'b0;
            threat_flag <= 1'b0;
            jammer_flag <= 1'b0;
            type_id <= 3'd0;
            action_code <= 4'd0;
            confidence <= 8'd0;
            result_data <= 32'd0;
            for (pi = 0; pi < WINDOW_SIZE; pi = pi + 1) begin
                i_buf[pi] <= 16'sd0;
                q_buf[pi] <= 16'sd0;
            end
        end else begin
            result_valid <= 1'b0;

            if (frame_pending) begin
                threat_flag <= final_threat_flag_w;
                jammer_flag <= final_jammer_flag_w;
                type_id <= final_type_id_w;
                action_code <= action_code_w;
                confidence <= confidence_w;
                result_data <= result_data_w;
                result_valid <= 1'b1;
                frame_pending <= 1'b0;
            end else if (sample_valid && sample_ready) begin
                i_buf[sample_count] <= i_sample;
                q_buf[sample_count] <= q_sample;

                if (sample_count == WINDOW_SIZE-1) begin
                    sample_count <= 9'd0;
                    frame_pending <= 1'b1;
                end else begin
                    sample_count <= sample_count + 9'd1;
                end
            end
        end
    end

endmodule

// ============================================================================
// Shared Backbone - Residual-Lite 1D feature extractor
// Produces 64 fixed-point features from a 2x512 I/Q window
// ============================================================================

module skyshield_backbone_rtl (
    input  wire [512*16-1:0] i_window_bus,
    input  wire [512*16-1:0] q_window_bus,
    output reg  [64*16-1:0]  feature_bus
);

    function signed [31:0] abs16;
        input signed [15:0] value;
        begin
            abs16 = value[15] ? -$signed({{16{value[15]}}, value}) : $signed({{16{value[15]}}, value});
        end
    endfunction

    function signed [15:0] sat16;
        input signed [31:0] value;
        begin
            if (value > 32'sd32767)
                sat16 = 16'sd32767;
            else if (value < -32'sd32768)
                sat16 = -16'sd32768;
            else
                sat16 = value[15:0];
        end
    endfunction

    integer seg;
    integer j;
    integer idx;
    reg signed [15:0] ii;
    reg signed [15:0] qq;
    reg signed [31:0] sum_i;
    reg signed [31:0] sum_q;
    reg signed [31:0] energy;
    reg signed [31:0] diff;
    reg signed [31:0] maxv;
    reg signed [31:0] minv;

    reg signed [15:0] base [0:31];
    reg signed [15:0] res1 [0:15];
    reg signed [15:0] res2 [0:7];
    reg signed [15:0] ctx  [0:7];

    always @(*) begin
        for (seg = 0; seg < 32; seg = seg + 1) begin
            sum_i = 32'sd0;
            sum_q = 32'sd0;
            energy = 32'sd0;
            diff = 32'sd0;
            maxv = -32'sd32768;
            minv =  32'sd32767;

            for (j = 0; j < 16; j = j + 1) begin
                idx = (seg * 16) + j;
                ii = $signed(i_window_bus[(idx*16) +: 16]);
                qq = $signed(q_window_bus[(idx*16) +: 16]);

                sum_i = sum_i + abs16(ii);
                sum_q = sum_q + abs16(qq);
                diff  = diff  + abs16(ii - qq);
                energy = energy + (((ii * ii) + (qq * qq)) >>> 6);

                if (ii > maxv)
                    maxv = ii;
                if (ii < minv)
                    minv = ii;
            end

            base[seg] = sat16((sum_i + sum_q + energy - diff + maxv - minv) >>> 3);
        end

        for (seg = 0; seg < 16; seg = seg + 1) begin
            res1[seg] = sat16(((base[seg*2] + base[seg*2 + 1]) + (base[seg*2] >>> 1) - (base[seg*2 + 1] >>> 2)) >>> 1);
        end

        for (seg = 0; seg < 8; seg = seg + 1) begin
            res2[seg] = sat16(((res1[seg*2] + res1[seg*2 + 1]) + (base[seg*4] >>> 1)) >>> 1);
        end

        for (seg = 0; seg < 8; seg = seg + 1) begin
            ctx[seg] = sat16(((res2[seg] + base[seg] - base[31 - seg])) >>> 1);
        end

        for (seg = 0; seg < 32; seg = seg + 1) begin
            feature_bus[(seg*16) +: 16] = base[seg];
        end

        for (seg = 0; seg < 16; seg = seg + 1) begin
            feature_bus[((32 + seg)*16) +: 16] = res1[seg];
        end

        for (seg = 0; seg < 8; seg = seg + 1) begin
            feature_bus[((48 + seg)*16) +: 16] = res2[seg];
        end

        for (seg = 0; seg < 8; seg = seg + 1) begin
            feature_bus[((56 + seg)*16) +: 16] = ctx[seg];
        end
    end

endmodule

// ============================================================================
// Threat Head - Binary threat / benign
// ============================================================================

module skyshield_threat_head (
    input  wire [64*16-1:0] feature_bus,
    output reg  [7:0]       threat_prob,
    output reg              threat_flag
);

    function [7:0] clamp_u8;
        input signed [31:0] value;
        begin
            if (value < 0)
                clamp_u8 = 8'd0;
            else if (value > 255)
                clamp_u8 = 8'd255;
            else
                clamp_u8 = value[7:0];
        end
    endfunction

    integer k;
    reg signed [31:0] acc;

    always @(*) begin
        acc = 32'sd64;

        for (k = 0; k < 16; k = k + 1)
            acc = acc + ($signed(feature_bus[(k*16) +: 16]) >>> 3);

        for (k = 16; k < 32; k = k + 1)
            acc = acc + ($signed(feature_bus[(k*16) +: 16]) >>> 4);

        for (k = 32; k < 48; k = k + 1)
            acc = acc - ($signed(feature_bus[(k*16) +: 16]) >>> 5);

        for (k = 48; k < 64; k = k + 1)
            acc = acc + ($signed(feature_bus[(k*16) +: 16]) >>> 5);

        threat_prob = clamp_u8(32'sd128 + (acc >>> 2));
        threat_flag = (threat_prob >= 8'd180);
    end

endmodule

// ============================================================================
// Type Head - 6-class output (benign / DJI / FPV / Autel / DIY / jammer)
// ============================================================================

module skyshield_type_head (
    input  wire [64*16-1:0] feature_bus,
    output reg  [7:0]       type_prob_0,
    output reg  [7:0]       type_prob_1,
    output reg  [7:0]       type_prob_2,
    output reg  [7:0]       type_prob_3,
    output reg  [7:0]       type_prob_4,
    output reg  [7:0]       type_prob_5,
    output reg  [2:0]       type_id
);

    localparam [2:0] TYPE_BENIGN = 3'd0;
    localparam [2:0] TYPE_DJI    = 3'd1;
    localparam [2:0] TYPE_FPV    = 3'd2;
    localparam [2:0] TYPE_AUTEL  = 3'd3;
    localparam [2:0] TYPE_DIY    = 3'd4;
    localparam [2:0] TYPE_JAMMER = 3'd5;

    function signed [31:0] abs16;
        input signed [15:0] value;
        begin
            abs16 = value[15] ? -$signed({{16{value[15]}}, value}) : $signed({{16{value[15]}}, value});
        end
    endfunction

    function [7:0] clamp_u8;
        input signed [31:0] value;
        begin
            if (value < 0)
                clamp_u8 = 8'd0;
            else if (value > 255)
                clamp_u8 = 8'd255;
            else
                clamp_u8 = value[7:0];
        end
    endfunction

    integer k;
    reg [7:0] type_max;
    reg signed [31:0] benign_acc;
    reg signed [31:0] dji_acc;
    reg signed [31:0] fpv_acc;
    reg signed [31:0] autel_acc;
    reg signed [31:0] diy_acc;
    reg signed [31:0] jam_acc;

    always @(*) begin
        benign_acc = 32'sd180;
        dji_acc    = 32'sd120;
        fpv_acc    = 32'sd120;
        autel_acc  = 32'sd120;
        diy_acc    = 32'sd120;
        jam_acc    = 32'sd80;

        for (k = 0; k < 16; k = k + 1)
            benign_acc = benign_acc - (abs16($signed(feature_bus[(k*16) +: 16])) >>> 4);

        for (k = 16; k < 32; k = k + 1)
            benign_acc = benign_acc - (abs16($signed(feature_bus[(k*16) +: 16])) >>> 4);

        for (k = 0; k < 16; k = k + 1)
            dji_acc = dji_acc + ($signed(feature_bus[(k*16) +: 16]) >>> 3);

        for (k = 32; k < 40; k = k + 1)
            dji_acc = dji_acc + ($signed(feature_bus[(k*16) +: 16]) >>> 4);

        for (k = 16; k < 24; k = k + 1)
            fpv_acc = fpv_acc + ($signed(feature_bus[(k*16) +: 16]) >>> 3);

        for (k = 48; k < 56; k = k + 1)
            fpv_acc = fpv_acc + (abs16($signed(feature_bus[(k*16) +: 16])) >>> 2);

        for (k = 24; k < 32; k = k + 1)
            autel_acc = autel_acc + ($signed(feature_bus[(k*16) +: 16]) >>> 3);

        for (k = 56; k < 64; k = k + 1)
            autel_acc = autel_acc + ($signed(feature_bus[(k*16) +: 16]) >>> 3);

        for (k = 32; k < 48; k = k + 1)
            diy_acc = diy_acc + (abs16($signed(feature_bus[(k*16) +: 16])) >>> 3);

        for (k = 0; k < 8; k = k + 1)
            diy_acc = diy_acc + ($signed(feature_bus[(k*16) +: 16]) >>> 4);

        for (k = 48; k < 64; k = k + 1)
            jam_acc = jam_acc + (abs16($signed(feature_bus[(k*16) +: 16])) >>> 5);

        for (k = 0; k < 16; k = k + 1)
            jam_acc = jam_acc + (abs16($signed(feature_bus[(k*16) +: 16])) >>> 6);

        type_prob_0 = clamp_u8(32'sd128 + (benign_acc >>> 2));
        type_prob_1 = clamp_u8(32'sd128 + (dji_acc    >>> 2));
        type_prob_2 = clamp_u8(32'sd128 + (fpv_acc    >>> 2));
        type_prob_3 = clamp_u8(32'sd128 + (autel_acc  >>> 2));
        type_prob_4 = clamp_u8(32'sd128 + (diy_acc    >>> 2));
        type_prob_5 = clamp_u8(32'sd128 + (jam_acc    >>> 2));
        type_max = type_prob_0;
        if (type_prob_1 > type_max) type_max = type_prob_1;
        if (type_prob_2 > type_max) type_max = type_prob_2;
        if (type_prob_3 > type_max) type_max = type_prob_3;
        if (type_prob_4 > type_max) type_max = type_prob_4;

        if ((type_prob_5 >= (type_max + 8'd24)) || (type_prob_5 >= 8'd230)) begin
            type_id = TYPE_JAMMER;
        end else if (type_prob_0 == type_max) begin
            type_id = TYPE_BENIGN;
        end else if (type_prob_1 == type_max) begin
            type_id = TYPE_DJI;
        end else if (type_prob_2 == type_max) begin
            type_id = TYPE_FPV;
        end else if (type_prob_3 == type_max) begin
            type_id = TYPE_AUTEL;
        end else begin
            type_id = TYPE_DIY;
        end
    end

endmodule

// ============================================================================
// Jammer Head - Binary jammer / no jammer
// ============================================================================

module skyshield_jammer_head (
    input  wire [64*16-1:0] feature_bus,
    output reg  [7:0]       jammer_prob,
    output reg              jammer_flag
);

    function signed [31:0] abs16;
        input signed [15:0] value;
        begin
            abs16 = value[15] ? -$signed({{16{value[15]}}, value}) : $signed({{16{value[15]}}, value});
        end
    endfunction

    function [7:0] clamp_u8;
        input signed [31:0] value;
        begin
            if (value < 0)
                clamp_u8 = 8'd0;
            else if (value > 255)
                clamp_u8 = 8'd255;
            else
                clamp_u8 = value[7:0];
        end
    endfunction

    integer k;
    reg signed [31:0] acc;

    always @(*) begin
        acc = 32'sd64;

        for (k = 56; k < 64; k = k + 1)
            acc = acc + (abs16($signed(feature_bus[(k*16) +: 16])) >>> 2);

        for (k = 0; k < 16; k = k + 1)
            acc = acc - ($signed(feature_bus[(k*16) +: 16]) >>> 5);

        for (k = 16; k < 32; k = k + 1)
            acc = acc + (abs16($signed(feature_bus[(k*16) +: 16])) >>> 4);

        jammer_prob = clamp_u8(32'sd96 + (acc >>> 2));
        jammer_flag = (jammer_prob >= 8'd240);
    end

endmodule

// ============================================================================
// Deterministic Voting Logic
// ============================================================================

module skyshield_voting_logic (
    input  wire [7:0]  threat_prob,
    input  wire        threat_flag,
    input  wire [7:0]  type_prob_0,
    input  wire [7:0]  type_prob_1,
    input  wire [7:0]  type_prob_2,
    input  wire [7:0]  type_prob_3,
    input  wire [7:0]  type_prob_4,
    input  wire [7:0]  type_prob_5,
    input  wire [2:0]  type_id,
    input  wire [7:0]  jammer_prob,
    input  wire        jammer_flag,

    output reg  [3:0]  action_code,
    output reg  [7:0]  confidence,
    output reg         final_threat_flag,
    output reg         final_jammer_flag,
    output reg  [2:0]  final_type_id,
    output reg  [31:0] result_data
);

    // Output fields are encoded for later CSV testbench decoding:
    // result_data[31:24]=confidence, [23:20]=action_code, [19:17]=type_id,
    // [16]=threat, [15]=jammer, [14:0]=reserved.

    localparam [2:0] TYPE_BENIGN = 3'd0;
    localparam [2:0] TYPE_DJI    = 3'd1;
    localparam [2:0] TYPE_FPV    = 3'd2;
    localparam [2:0] TYPE_AUTEL  = 3'd3;
    localparam [2:0] TYPE_DIY    = 3'd4;
    localparam [2:0] TYPE_JAMMER = 3'd5;

    localparam [7:0] THREAT_THRESHOLD = 8'd180;
    localparam [7:0] JAMMER_THRESHOLD = 8'd200;

    function [7:0] max6;
        input [7:0] a;
        input [7:0] b;
        input [7:0] c;
        input [7:0] d;
        input [7:0] e;
        input [7:0] f;
        reg [7:0] m;
        begin
            m = a;
            if (b > m) m = b;
            if (c > m) m = c;
            if (d > m) m = d;
            if (e > m) m = e;
            if (f > m) m = f;
            max6 = m;
        end
    endfunction

    function [7:0] max5;
        input [7:0] a;
        input [7:0] b;
        input [7:0] c;
        input [7:0] d;
        input [7:0] e;
        reg [7:0] m;
        begin
            m = a;
            if (b > m) m = b;
            if (c > m) m = c;
            if (d > m) m = d;
            if (e > m) m = e;
            max5 = m;
        end
    endfunction

    reg [7:0] type_max;
    reg [7:0] nonjam_max;
    reg [31:0] weighted_sum;
    reg threat_vote;
    reg jammer_vote;
    reg type_jammer_vote;
    reg [2:0] nonjam_type_id;

    always @(*) begin
        type_max = max6(type_prob_0, type_prob_1, type_prob_2, type_prob_3, type_prob_4, type_prob_5);
        nonjam_max = max5(type_prob_0, type_prob_1, type_prob_2, type_prob_3, type_prob_4);
        weighted_sum = ((threat_prob * 5) + (type_max * 2) + (jammer_prob * 3)) / 10;
        type_jammer_vote = (type_id == TYPE_JAMMER) && (type_prob_5 >= 8'd220);
        threat_vote = threat_flag || (type_id != TYPE_BENIGN) || (weighted_sum >= THREAT_THRESHOLD);
        jammer_vote = jammer_flag || (jammer_prob >= JAMMER_THRESHOLD) || type_jammer_vote;

        if (type_prob_0 == nonjam_max)
            nonjam_type_id = TYPE_BENIGN;
        else if (type_prob_1 == nonjam_max)
            nonjam_type_id = TYPE_DJI;
        else if (type_prob_2 == nonjam_max)
            nonjam_type_id = TYPE_FPV;
        else if (type_prob_3 == nonjam_max)
            nonjam_type_id = TYPE_AUTEL;
        else
            nonjam_type_id = TYPE_DIY;

        if (jammer_vote) begin
            action_code = 4'd3;
            final_threat_flag = 1'b1;
            final_jammer_flag = 1'b1;
            final_type_id = TYPE_JAMMER;
            confidence = weighted_sum[7:0];
        end else if (!threat_vote) begin
            action_code = 4'd0;
            final_threat_flag = 1'b0;
            final_jammer_flag = 1'b0;
            final_type_id = TYPE_BENIGN;
            confidence = weighted_sum[7:0];
        end else begin
            action_code = 4'd1;
            final_threat_flag = 1'b1;
            final_jammer_flag = 1'b0;
            if (type_id == TYPE_JAMMER)
                final_type_id = nonjam_type_id;
            else
                final_type_id = type_id;
            confidence = weighted_sum[7:0];
        end

        result_data = {confidence, action_code, final_type_id, final_threat_flag, final_jammer_flag, 15'h0000};
    end

endmodule
