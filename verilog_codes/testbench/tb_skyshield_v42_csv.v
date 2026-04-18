`timescale 1ns / 1ps
// ============================================================================
// SkyShield v4.2 - CSV-Driven Self-Checking Testbench
// Reads CSV stimulus cases (up to MAX_CASES), streams 512 I/Q samples per case,
// and prints per-metric and aggregate accuracy.
// CSV header columns (Excel-friendly):
// pz_case_id,pz_expected_type,pz_expected_threat,pz_expected_jammer,
// pz_pattern_id,pz_variant,pz_amp,pz_bias_i,pz_bias_q,pz_noise,
// pz_burst_period,pz_burst_width,pz_phase_step,pz_drift,pz_seed
// ============================================================================

module tb_skyshield_v42_csv;

    localparam integer WINDOW_SIZE = 512;
    localparam integer MAX_CASES   = 200;
    localparam integer PREVIEW_SAMPLES = 4;

    reg clk;
    reg rst_n;
    reg sample_valid;
    reg signed [15:0] i_sample;
    reg signed [15:0] q_sample;

    wire sample_ready;
    wire result_valid;
    wire threat_flag;
    wire jammer_flag;
    wire [2:0] type_id;
    wire [3:0] action_code;
    wire [7:0] confidence;
    wire [31:0] result_data;

    skyshield_v42_top dut (
        .clk(clk),
        .rst_n(rst_n),
        .sample_valid(sample_valid),
        .i_sample(i_sample),
        .q_sample(q_sample),
        .sample_ready(sample_ready),
        .result_valid(result_valid),
        .threat_flag(threat_flag),
        .jammer_flag(jammer_flag),
        .type_id(type_id),
        .action_code(action_code),
        .confidence(confidence),
        .result_data(result_data)
    );

    always #5 clk = ~clk;

    integer csv_fd;
    integer scan_ok;
    integer first_line_scan;
    integer case_idx;
    integer done;
    reg [2047:0] first_line;

    integer case_id;
    integer expected_type;
    integer expected_threat;
    integer expected_jammer;
    integer pattern_id;
    integer variant;
    integer amp;
    integer bias_i;
    integer bias_q;
    integer noise;
    integer burst_period;
    integer burst_width;
    integer phase_step;
    integer drift;
    integer seed;

    integer actual_type;
    integer actual_threat;
    integer actual_jammer;
    integer actual_action;
    integer actual_confidence;
    integer actual_result;

    integer type_hits;
    integer threat_hits;
    integer jammer_hits;
    integer case_hits;
    integer total_triplets;
    integer total_cases;

    integer sample_i_int;
    integer sample_q_int;
    integer seg;
    integer slot_pos;
    integer sample_phase;
    integer burst;
    integer shape;
    integer sign;
    integer noise_i;
    integer noise_q;

    real type_acc;
    real threat_acc;
    real jammer_acc;
    real case_acc;

    reg [1023:0] csv_path;
    integer max_cases_runtime;
    reg [1023:0] wave_path;

    function integer clip16;
        input integer value;
        begin
            if (value > 32767)
                clip16 = 32767;
            else if (value < -32768)
                clip16 = -32768;
            else
                clip16 = value;
        end
    endfunction

    function integer prand;
        input integer base;
        input integer n;
        input integer salt;
        integer tmp;
        begin
            tmp = base ^ (n * 1315423911) ^ (salt * 2654435761);
            if (tmp < 0)
                tmp = -tmp;
            prand = tmp;
        end
    endfunction

    function integer centered_noise;
        input integer base;
        input integer n;
        input integer salt;
        input integer scale;
        integer val;
        begin
            if (scale <= 0) begin
                centered_noise = 0;
            end else begin
                val = prand(base, n, salt) % (2 * scale + 1);
                centered_noise = val - scale;
            end
        end
    endfunction

    task make_sample;
        input integer pattern;
        input integer var_id;
        input integer amp_i;
        input integer base_i;
        input integer base_q;
        input integer noise_scale;
        input integer burst_p;
        input integer burst_w;
        input integer p_step;
        input integer d_step;
        input integer seed_in;
        input integer n;
        output integer out_i;
        output integer out_q;
        begin
            seg = n / 16;
            slot_pos = n % 16;
            sample_phase = (n + seed_in + (var_id * 7)) % 64;
            burst = ((burst_p > 0) && ((n % burst_p) < burst_w)) ? amp_i : (amp_i >>> 2);
            noise_i = centered_noise(seed_in + (var_id * 17), n, 3, noise_scale);
            noise_q = centered_noise(seed_in + (var_id * 29) + 11, n, 7, noise_scale);

            case (pattern)
                0: begin
                    shape = (sample_phase < 56) ? (amp_i >>> 3) : (amp_i >>> 1);
                    out_i = base_i + shape + (burst >>> 1) + noise_i;
                    out_q = base_q + (shape >>> 1) + (burst >>> 2) + noise_q;
                end

                1: begin
                    shape = (seg < 8) ? (amp_i >>> 1) : ((seg < 16) ? amp_i : ((seg < 24) ? (amp_i >>> 2) : (amp_i >>> 3)));
                    sign = (slot_pos < 8) ? 1 : -1;
                    out_i = base_i + burst + shape + (sign * d_step) + noise_i;
                    out_q = base_q + (burst >>> 1) + (sign * (p_step + (var_id & 3))) - noise_q;
                end

                2: begin
                    shape = (((seg >= 8) && (seg < 16)) || (seg >= 24)) ? amp_i : (amp_i >>> 3);
                    sign = (n & 1) ? -1 : 1;
                    out_i = base_i + (sign * (burst + shape)) + noise_i;
                    out_q = base_q - (sign * (burst >>> 1)) + noise_q + ((seg & 1) ? p_step : -p_step);
                end

                3: begin
                    shape = (((seg >= 16) && (seg < 24)) || (seg >= 28)) ? (amp_i >>> 1) : (amp_i >>> 3);
                    out_i = base_i + shape + (d_step * seg) + noise_i;
                    out_q = base_q + (shape >>> 1) - (d_step * seg) + noise_q;
                end

                4: begin
                    sign = (slot_pos < 8) ? 1 : -1;
                    shape = (((seg < 4)) || ((seg >= 16) && (seg < 24))) ? amp_i : (amp_i >>> 2);
                    out_i = base_i + (sign * shape) + noise_i + (p_step * sign);
                    out_q = base_q - (sign * shape) + noise_q - (p_step * sign);
                end

                5: begin
                    shape = ((seg < 16) || (seg >= 24)) ? (amp_i <<< 1) : (amp_i >>> 1);
                    out_i = base_i + shape + (noise_i <<< 1) + burst;
                    out_q = base_q - shape + (noise_q <<< 1) - burst;
                end

                default: begin
                    out_i = base_i + noise_i;
                    out_q = base_q + noise_q;
                end
            endcase

            out_i = clip16(out_i);
            out_q = clip16(out_q);
        end
    endtask

    task drive_case;
        input integer pattern;
        input integer var_id;
        input integer amp_i;
        input integer base_i;
        input integer base_q;
        input integer noise_scale;
        input integer burst_p;
        input integer burst_w;
        input integer p_step;
        input integer d_step;
        input integer seed_in;
        integer n;
        begin
            for (n = 0; n < WINDOW_SIZE; n = n + 1) begin
                wait (sample_ready === 1'b1);
                make_sample(pattern, var_id, amp_i, base_i, base_q, noise_scale, burst_p, burst_w, p_step, d_step, seed_in, n, sample_i_int, sample_q_int);
                if (n < PREVIEW_SAMPLES) begin
                    $display("  IQ[%0d] -> I=%0d Q=%0d", n, sample_i_int, sample_q_int);
                end
                @(negedge clk);
                i_sample <= sample_i_int[15:0];
                q_sample <= sample_q_int[15:0];
                sample_valid <= 1'b1;
                @(posedge clk);
                #1 sample_valid <= 1'b0;
            end
        end
    endtask

    task evaluate_case;
        begin
            actual_result = result_data;
            actual_confidence = result_data[31:24];
            actual_action = result_data[23:20];
            actual_type = result_data[19:17];
            actual_threat = result_data[16];
            actual_jammer = result_data[15];

            if (actual_type == expected_type)
                type_hits = type_hits + 1;
            if (actual_threat == expected_threat)
                threat_hits = threat_hits + 1;
            if (actual_jammer == expected_jammer)
                jammer_hits = jammer_hits + 1;

            if ((actual_type == expected_type) && (actual_threat == expected_threat) && (actual_jammer == expected_jammer)) begin
                case_hits = case_hits + 1;
                $display("CASE %02d PASS | exp(T=%0d H=%0d J=%0d) act(T=%0d H=%0d J=%0d) action=%0d conf=%0d data=0x%08h",
                         case_id, expected_type, expected_threat, expected_jammer,
                         actual_type, actual_threat, actual_jammer, actual_action, actual_confidence, actual_result);
            end else begin
                $display("CASE %02d FAIL | exp(T=%0d H=%0d J=%0d) act(T=%0d H=%0d J=%0d) action=%0d conf=%0d data=0x%08h",
                         case_id, expected_type, expected_threat, expected_jammer,
                         actual_type, actual_threat, actual_jammer, actual_action, actual_confidence, actual_result);
            end

            total_triplets = total_triplets + 3;
            total_cases = total_cases + 1;
        end
    endtask

    initial begin
        if (!$value$plusargs("WAVE_PATH=%s", wave_path))
            wave_path = "build/tb_skyshield_v42_csv.vcd";
        $dumpfile(wave_path);
        $dumpvars(0, tb_skyshield_v42_csv);

        clk = 1'b0;
        rst_n = 1'b0;
        sample_valid = 1'b0;
        i_sample = 16'sd0;
        q_sample = 16'sd0;

        type_hits = 0;
        threat_hits = 0;
        jammer_hits = 0;
        case_hits = 0;
        total_triplets = 0;
        total_cases = 0;

        $display("============================================================");
        $display("SkyShield v4.2 CSV Testbench");
        $display("============================================================");

        if (!$value$plusargs("CSV_PATH=%s", csv_path))
            csv_path = "FPGA/testbenches/skyshield_v42_cases.csv";
        if (!$value$plusargs("MAX_CASES=%d", max_cases_runtime))
            max_cases_runtime = 100;
        if (max_cases_runtime > MAX_CASES)
            max_cases_runtime = MAX_CASES;

        repeat (5) @(posedge clk);
        rst_n = 1'b1;
        repeat (2) @(posedge clk);

        csv_fd = $fopen(csv_path, "r");
        if (csv_fd == 0) begin
            $display("ERROR: could not open CSV stimulus file: %0s", csv_path);
            $finish;
        end

        $display("CSV path: %0s", csv_path);
        $display("Configured max cases: %0d", max_cases_runtime);

        done = 0;
        case_idx = 0;

        // Read first CSV row: if numeric, treat as case data; otherwise treat as header.
        first_line_scan = $fgets(first_line, csv_fd);
        if (first_line_scan == 0) begin
            $display("ERROR: empty CSV file.");
            $finish;
        end

        scan_ok = $sscanf(first_line, "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
                          case_id, expected_type, expected_threat, expected_jammer,
                          pattern_id, variant, amp, bias_i, bias_q, noise,
                          burst_period, burst_width, phase_step, drift, seed);

        if (scan_ok == 15) begin
            $display("\n--- Case %0d ---", case_idx + 1);
            $display("  Expected -> type=%0d threat=%0d jammer=%0d", expected_type, expected_threat, expected_jammer);
            $display("  Pattern  -> id=%0d var=%0d amp=%0d noise=%0d seed=%0d", pattern_id, variant, amp, noise, seed);
            drive_case(pattern_id, variant, amp, bias_i, bias_q, noise, burst_period, burst_width, phase_step, drift, seed);
            @(posedge result_valid);
            #1 evaluate_case();
            @(posedge clk);
            case_idx = case_idx + 1;
        end else begin
            $display("Detected CSV header row (pz_* columns). Continuing with data rows.");
        end

        while (!done && (case_idx < max_cases_runtime)) begin
            scan_ok = $fscanf(csv_fd, "%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d",
                              case_id, expected_type, expected_threat, expected_jammer,
                              pattern_id, variant, amp, bias_i, bias_q, noise,
                              burst_period, burst_width, phase_step, drift, seed);
            if (scan_ok != 15) begin
                done = 1;
            end else begin
                $display("\n--- Case %0d ---", case_idx + 1);
                $display("  Expected -> type=%0d threat=%0d jammer=%0d", expected_type, expected_threat, expected_jammer);
                $display("  Pattern  -> id=%0d var=%0d amp=%0d noise=%0d seed=%0d", pattern_id, variant, amp, noise, seed);
                drive_case(pattern_id, variant, amp, bias_i, bias_q, noise, burst_period, burst_width, phase_step, drift, seed);

                @(posedge result_valid);
                #1 evaluate_case();
                @(posedge clk);
                case_idx = case_idx + 1;
            end
        end

        $fclose(csv_fd);

        if (total_cases == 0) begin
            $display("ERROR: zero valid cases parsed from CSV.");
            $finish;
        end

        type_acc = (100.0 * type_hits) / total_cases;
        threat_acc = (100.0 * threat_hits) / total_cases;
        jammer_acc = (100.0 * jammer_hits) / total_cases;
        case_acc = (100.0 * case_hits) / total_cases;

        $display("\n============================================================");
        $display("Final Accuracy Report");
        $display("  Type   accuracy : %0.1f%%", type_acc);
        $display("  Threat accuracy : %0.1f%%", threat_acc);
        $display("  Jammer accuracy : %0.1f%%", jammer_acc);
        $display("  Full-case pass  : %0.1f%%", case_acc);
        $display("  Cases passed    : %0d / %0d", case_hits, total_cases);
        $display("  Triplet hits    : %0d / %0d", (type_hits + threat_hits + jammer_hits), total_triplets);
        $display("============================================================");
        $finish;
    end

endmodule
