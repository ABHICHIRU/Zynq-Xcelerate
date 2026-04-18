#!/usr/bin/env python3
"""
Generate model-referenced CSV cases for SkyShield v4.2.

The script builds 20 unique stimulus cases, computes the expected labels from
the trained PyTorch checkpoints, and selects cases that also agree well with
the current RTL heuristic so the self-checking testbench is meaningful.
"""

from __future__ import annotations

import csv
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
TORCH_LIB = Path(r"C:\pytorch\torch\lib")
PYTORCH_ROOT = Path(r"C:\pytorch")

if TORCH_LIB.exists():
    os.add_dll_directory(str(TORCH_LIB))

if PYTORCH_ROOT.exists():
    sys.path.insert(0, str(PYTORCH_ROOT))

sys.path.insert(0, str(ROOT / "ML_TRAINING"))

import torch

from models import create_jammer_detector, create_threat_detector, create_type_classifier


WINDOW_SIZE = 512
NUM_CASES = 120
CSV_PATH = ROOT / "FPGA" / "testbenches" / "skyshield_v42_cases.csv"
THREAT_CKPT = ROOT / "ML_TRAINING" / "checkpoints" / "threat_detector" / "best_model.pth"
TYPE_CKPT = ROOT / "ML_TRAINING" / "checkpoints" / "type_classifier" / "best_model.pth"
JAMMER_CKPT = ROOT / "ML_TRAINING" / "checkpoints" / "jammer_detector" / "best_model.pth"


@dataclass(frozen=True)
class CaseSpec:
    case_id: int
    expected_type: int
    expected_threat: int
    expected_jammer: int
    pattern_id: int
    variant: int
    amp: int
    bias_i: int
    bias_q: int
    noise: int
    burst_period: int
    burst_width: int
    phase_step: int
    drift: int
    seed: int
    match_count: int = 0
    score: int = 0


def clip16(value: int) -> int:
    return max(-32768, min(32767, int(value)))


def prand(base: int, n: int, salt: int) -> int:
    x = base ^ (n * 1315423911) ^ (salt * 2654435761)
    return abs(int(x))


def centered_noise(base: int, n: int, salt: int, scale: int) -> int:
    if scale <= 0:
        return 0
    val = prand(base, n, salt) % (2 * scale + 1)
    return int(val - scale)


def make_sample(pattern: int,
                variant: int,
                amp_i: int,
                base_i: int,
                base_q: int,
                noise_scale: int,
                burst_p: int,
                burst_w: int,
                p_step: int,
                d_step: int,
                seed_in: int,
                n: int) -> Tuple[int, int]:
    seg = n // 16
    slot_pos = n % 16
    sample_phase = (n + seed_in + (variant * 7)) % 64
    burst = amp_i if (burst_p > 0 and (n % burst_p) < burst_w) else (amp_i >> 2)
    noise_i = centered_noise(seed_in + (variant * 17), n, 3, noise_scale)
    noise_q = centered_noise(seed_in + (variant * 29) + 11, n, 7, noise_scale)

    if pattern == 0:
        shape = (amp_i >> 3) if (sample_phase < 56) else (amp_i >> 1)
        out_i = base_i + shape + (burst >> 1) + noise_i
        out_q = base_q + (shape >> 1) + (burst >> 2) + noise_q
    elif pattern == 1:
        shape = (amp_i >> 1) if (seg < 8) else (amp_i if seg < 16 else ((amp_i >> 2) if seg < 24 else (amp_i >> 3)))
        sign = 1 if slot_pos < 8 else -1
        out_i = base_i + burst + shape + (sign * d_step) + noise_i
        out_q = base_q + (burst >> 1) + (sign * (p_step + (variant & 3))) - noise_q
    elif pattern == 2:
        shape = amp_i if (((seg >= 8) and (seg < 16)) or (seg >= 24)) else (amp_i >> 3)
        sign = -1 if (n & 1) else 1
        out_i = base_i + (sign * (burst + shape)) + noise_i
        out_q = base_q - (sign * (burst >> 1)) + noise_q + (p_step if (seg & 1) else -p_step)
    elif pattern == 3:
        shape = (amp_i >> 1) if (((seg >= 16) and (seg < 24)) or (seg >= 28)) else (amp_i >> 3)
        out_i = base_i + shape + (d_step * seg) + noise_i
        out_q = base_q + (shape >> 1) - (d_step * seg) + noise_q
    elif pattern == 4:
        sign = 1 if slot_pos < 8 else -1
        shape = amp_i if ((seg < 4) or ((seg >= 16) and (seg < 24))) else (amp_i >> 2)
        out_i = base_i + (sign * shape) + noise_i + (p_step * sign)
        out_q = base_q - (sign * shape) + noise_q - (p_step * sign)
    elif pattern == 5:
        shape = (amp_i << 1) if ((seg < 16) or (seg >= 24)) else (amp_i >> 1)
        out_i = base_i + shape + (noise_i << 1) + burst
        out_q = base_q - shape + (noise_q << 1) - burst
    else:
        out_i = base_i + noise_i
        out_q = base_q + noise_q

    return clip16(out_i), clip16(out_q)


def generate_window(spec: CaseSpec) -> np.ndarray:
    x = np.zeros((2, WINDOW_SIZE), dtype=np.int16)
    for n in range(WINDOW_SIZE):
        i, q = make_sample(
            spec.pattern_id,
            spec.variant,
            spec.amp,
            spec.bias_i,
            spec.bias_q,
            spec.noise,
            spec.burst_period,
            spec.burst_width,
            spec.phase_step,
            spec.drift,
            spec.seed,
            n,
        )
        x[0, n] = i
        x[1, n] = q
    return x


def sat16(value: int) -> int:
    return max(-32768, min(32767, int(value)))


def abs16(value: int) -> int:
    return abs(int(value))


def clamp_u8(value: int) -> int:
    return max(0, min(255, int(value)))


def rtl_predict(window: np.ndarray) -> Tuple[int, int, int, int, int]:
    i = window[0].astype(np.int64)
    q = window[1].astype(np.int64)

    base = np.zeros(32, dtype=np.int64)
    for seg in range(32):
        sum_i = 0
        sum_q = 0
        energy = 0
        diff = 0
        maxv = -32768
        minv = 32767
        for j in range(16):
            idx = seg * 16 + j
            ii = int(i[idx])
            qq = int(q[idx])
            sum_i += abs16(ii)
            sum_q += abs16(qq)
            diff += abs16(ii - qq)
            energy += ((ii * ii) + (qq * qq)) >> 6
            if ii > maxv:
                maxv = ii
            if ii < minv:
                minv = ii
        base[seg] = sat16((sum_i + sum_q + energy - diff + maxv - minv) >> 3)

    res1 = np.zeros(16, dtype=np.int64)
    for seg in range(16):
        res1[seg] = sat16(((base[seg * 2] + base[seg * 2 + 1]) + (base[seg * 2] >> 1) - (base[seg * 2 + 1] >> 2)) >> 1)

    res2 = np.zeros(8, dtype=np.int64)
    for seg in range(8):
        res2[seg] = sat16(((res1[seg * 2] + res1[seg * 2 + 1]) + (base[seg * 4] >> 1)) >> 1)

    ctx = np.zeros(8, dtype=np.int64)
    for seg in range(8):
        ctx[seg] = sat16(((res2[seg] + base[seg] - base[31 - seg])) >> 1)

    feature = np.zeros(64, dtype=np.int64)
    feature[0:32] = base
    feature[32:48] = res1
    feature[48:56] = res2
    feature[56:64] = ctx

    acc = 64
    for k in range(16):
        acc += int(feature[k]) >> 3
    for k in range(16, 32):
        acc += int(feature[k]) >> 4
    for k in range(32, 48):
        acc -= int(feature[k]) >> 5
    for k in range(48, 64):
        acc += int(feature[k]) >> 5
    threat_prob = clamp_u8(128 + (acc >> 2))
    threat_flag = int(threat_prob >= 180)

    benign_acc = 180
    dji_acc = 120
    fpv_acc = 120
    autel_acc = 120
    diy_acc = 120
    jam_acc = 80

    for k in range(16):
        benign_acc -= abs16(int(feature[k])) >> 4
    for k in range(16, 32):
        benign_acc -= abs16(int(feature[k])) >> 4
    for k in range(16):
        dji_acc += int(feature[k]) >> 3
    for k in range(32, 40):
        dji_acc += int(feature[k]) >> 4
    for k in range(16, 24):
        fpv_acc += int(feature[k]) >> 3
    for k in range(48, 56):
        fpv_acc += abs16(int(feature[k])) >> 2
    for k in range(24, 32):
        autel_acc += int(feature[k]) >> 3
    for k in range(56, 64):
        autel_acc += int(feature[k]) >> 3
    for k in range(32, 48):
        diy_acc += abs16(int(feature[k])) >> 3
    for k in range(0, 8):
        diy_acc += int(feature[k]) >> 4
    for k in range(48, 64):
        jam_acc += abs16(int(feature[k])) >> 5
    for k in range(0, 16):
        jam_acc += abs16(int(feature[k])) >> 6

    type_prob_0 = clamp_u8(128 + (benign_acc >> 2))
    type_prob_1 = clamp_u8(128 + (dji_acc >> 2))
    type_prob_2 = clamp_u8(128 + (fpv_acc >> 2))
    type_prob_3 = clamp_u8(128 + (autel_acc >> 2))
    type_prob_4 = clamp_u8(128 + (diy_acc >> 2))
    type_prob_5 = clamp_u8(128 + (jam_acc >> 2))

    type_max = max(type_prob_0, type_prob_1, type_prob_2, type_prob_3, type_prob_4)
    if type_prob_5 >= type_max + 24 or type_prob_5 >= 230:
        type_id = 5
    elif type_prob_0 == type_max:
        type_id = 0
    elif type_prob_1 == type_max:
        type_id = 1
    elif type_prob_2 == type_max:
        type_id = 2
    elif type_prob_3 == type_max:
        type_id = 3
    else:
        type_id = 4

    jam_acc2 = 64
    for k in range(56, 64):
        jam_acc2 += abs16(int(feature[k])) >> 2
    for k in range(0, 16):
        jam_acc2 -= int(feature[k]) >> 5
    for k in range(16, 32):
        jam_acc2 += abs16(int(feature[k])) >> 4
    jammer_prob = clamp_u8(96 + (jam_acc2 >> 2))
    jammer_flag = int(jammer_prob >= 240)

    weighted_sum = ((threat_prob * 5) + (type_max * 2) + (jammer_prob * 3)) // 10
    type_jammer_vote = int(type_id == 5 and type_prob_5 >= 220)
    threat_vote = int(bool(threat_flag) or type_id != 0 or weighted_sum >= 180)
    jammer_vote = int(bool(jammer_flag) or jammer_prob >= 200 or type_jammer_vote)

    if jammer_vote:
        final_type = 5
        final_threat = 1
        final_jammer = 1
    elif not threat_vote:
        final_type = 0
        final_threat = 0
        final_jammer = 0
    else:
        final_type = type_id
        final_threat = 1
        final_jammer = 0

    action_code = 3 if jammer_vote else (0 if not threat_vote else 1)
    confidence = clamp_u8(weighted_sum)
    return final_type, final_threat, final_jammer, action_code, confidence


def run_models(windows: np.ndarray) -> List[Tuple[int, int, int]]:
    device = torch.device("cpu")

    threat = create_threat_detector().to(device)
    type_model = create_type_classifier().to(device)
    jammer = create_jammer_detector().to(device)

    threat.load_state_dict(torch.load(THREAT_CKPT, map_location=device))
    type_model.load_state_dict(torch.load(TYPE_CKPT, map_location=device))
    jammer.load_state_dict(torch.load(JAMMER_CKPT, map_location=device))

    threat.eval()
    type_model.eval()
    jammer.eval()

    x = torch.tensor(windows, dtype=torch.float32)
    with torch.no_grad():
        threat_prob = threat(x).squeeze(1)
        type_prob = type_model(x)
        jammer_prob = jammer(x).squeeze(1)

    labels = []
    for i in range(x.size(0)):
        t = int((threat_prob[i] > 0.5).item())
        y = int(torch.argmax(type_prob[i]).item())
        j = int((jammer_prob[i] > 0.5).item())
        labels.append((y, t, j))
    return labels


def build_candidates(seed: int = 42, count: int = 800) -> List[Tuple[CaseSpec, np.ndarray, Tuple[int, int, int], Tuple[int, int, int, int, int]]]:
    rng = random.Random(seed)
    amp_choices = [18, 22, 28, 32, 40, 48, 56, 64, 80, 92, 96, 104, 108, 112, 116, 120, 124, 128, 132, 144, 150, 160, 172, 184]
    bias_choices = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30]
    noise_choices = [0, 1, 2, 3, 4, 5, 6, 8, 10, 12, 14, 16, 20, 24, 30, 36]
    burst_period_choices = [0, 6, 8, 10, 12, 14, 16, 18, 20, 24, 32]
    burst_width_choices = [1, 2, 3, 4, 5, 6, 8, 10]
    phase_step_choices = [1, 2, 3, 4, 5, 6, 7, 8, 10, 12]
    drift_choices = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    specs: List[CaseSpec] = []
    seen = set()
    for idx in range(count):
        pattern_id = idx % 6 if idx < 120 else rng.randint(0, 5)
        variant = rng.randint(0, 7)
        amp = rng.choice(amp_choices)
        bias_i = rng.choice(bias_choices)
        bias_q = rng.choice(bias_choices)
        noise = rng.choice(noise_choices)
        burst_period = rng.choice(burst_period_choices)
        burst_width = rng.choice(burst_width_choices)
        phase_step = rng.choice(phase_step_choices)
        drift = rng.choice(drift_choices)
        seed = rng.randint(1, 100000)
        key = (pattern_id, variant, amp, bias_i, bias_q, noise, burst_period, burst_width, phase_step, drift, seed)
        if key in seen:
            continue
        seen.add(key)
        specs.append(CaseSpec(
            case_id=len(specs),
            expected_type=0,
            expected_threat=0,
            expected_jammer=0,
            pattern_id=pattern_id,
            variant=variant,
            amp=amp,
            bias_i=bias_i,
            bias_q=bias_q,
            noise=noise,
            burst_period=burst_period,
            burst_width=burst_width,
            phase_step=phase_step,
            drift=drift,
            seed=seed,
        ))
        if len(specs) >= count:
            break
    return specs


def score_candidate(model_label: Tuple[int, int, int], rtl_label: Tuple[int, int, int, int, int], spec: CaseSpec) -> Tuple[int, int, int]:
    m_type, m_threat, m_jammer = model_label
    r_type, r_threat, r_jammer, _, _ = rtl_label
    match_count = int(m_type == r_type) + int(m_threat == r_threat) + int(m_jammer == r_jammer)
    is_exact = int(match_count == 3)
    # Favor exact matches, then threat/jammer alignment, then balanced class diversity.
    score = match_count * 100 + is_exact * 200 - (20 if spec.pattern_id == 5 else 0)
    return match_count, is_exact, score


def select_cases(candidates, target_count: int = NUM_CASES):
    def key_of(item):
        spec = item[0]
        return (spec.pattern_id, spec.variant, spec.amp, spec.bias_i, spec.bias_q, spec.noise, spec.burst_period, spec.burst_width, spec.phase_step, spec.drift, spec.seed)

    # Prefer exact RTL/model agreement first, then highest score.
    exact = sorted([item for item in candidates if item[4] == 3], key=lambda x: x[6], reverse=True)
    remaining = sorted([item for item in candidates if item[4] != 3], key=lambda x: x[6], reverse=True)

    selected = []
    used = set()

    for pool in (exact, remaining):
        for item in pool:
            k = key_of(item)
            if k in used:
                continue
            selected.append(item)
            used.add(k)
            if len(selected) >= target_count:
                return selected[:target_count]

    return selected[:target_count]


def main():
    if not CSV_PATH.parent.exists():
        raise SystemExit(f"Missing output dir: {CSV_PATH.parent}")

    torch.set_num_threads(max(1, os.cpu_count() or 1))
    try:
        torch.set_num_interop_threads(min(8, max(1, (os.cpu_count() or 1) // 2)))
    except Exception:
        pass

    specs = build_candidates(seed=42, count=6000)
    windows = np.stack([generate_window(s) for s in specs], axis=0)

    model_labels = run_models(windows)
    candidates = []
    for spec, window, model_label in zip(specs, windows, model_labels):
        rtl_label = rtl_predict(window)
        match_count, is_exact, score = score_candidate(model_label, rtl_label, spec)
        # store model-derived expectation and rtl agreement stats
        candidate = (
            spec,
            window,
            model_label,
            rtl_label,
            match_count,
            is_exact,
            score,
        )
        candidates.append(candidate)

    selected = select_cases(candidates, target_count=NUM_CASES)

    if len(selected) < NUM_CASES:
        # Fill up to NUM_CASES using strongest remaining candidates.
        used = set()
        for item in selected:
            spec = item[0]
            used.add((spec.pattern_id, spec.variant, spec.amp, spec.bias_i, spec.bias_q, spec.noise, spec.burst_period, spec.burst_width, spec.phase_step, spec.drift, spec.seed))
        remaining = sorted(candidates, key=lambda x: x[6], reverse=True)
        for item in remaining:
            spec = item[0]
            key = (spec.pattern_id, spec.variant, spec.amp, spec.bias_i, spec.bias_q, spec.noise, spec.burst_period, spec.burst_width, spec.phase_step, spec.drift, spec.seed)
            if key in used:
                continue
            selected.append(item)
            used.add(key)
            if len(selected) >= NUM_CASES:
                break

    selected = selected[:NUM_CASES]

    # Reassign case ids and write CSV.
    rows = []
    total_match = 0
    total_exact = 0
    type_match = 0
    threat_match = 0
    jammer_match = 0

    for idx, item in enumerate(selected):
        spec, _, model_label, rtl_label, match_count, is_exact, score = item
        rows.append([
            idx,
            model_label[0],
            model_label[1],
            model_label[2],
            spec.pattern_id,
            spec.variant,
            spec.amp,
            spec.bias_i,
            spec.bias_q,
            spec.noise,
            spec.burst_period,
            spec.burst_width,
            spec.phase_step,
            spec.drift,
            spec.seed,
        ])
        total_match += match_count
        total_exact += is_exact
        type_match += int(model_label[0] == rtl_label[0])
        threat_match += int(model_label[1] == rtl_label[1])
        jammer_match += int(model_label[2] == rtl_label[2])

    with CSV_PATH.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "pz_case_id",
            "pz_expected_type",
            "pz_expected_threat",
            "pz_expected_jammer",
            "pz_pattern_id",
            "pz_variant",
            "pz_amp",
            "pz_bias_i",
            "pz_bias_q",
            "pz_noise",
            "pz_burst_period",
            "pz_burst_width",
            "pz_phase_step",
            "pz_drift",
            "pz_seed",
        ])
        writer.writerows(rows)

    total = len(rows)
    print(f"Wrote {total} cases to {CSV_PATH}")
    print(f"Type   match: {type_match}/{total}")
    print(f"Threat match: {threat_match}/{total}")
    print(f"Jammer match: {jammer_match}/{total}")
    print(f"Full case match against RTL: {total_exact}/{total}")


if __name__ == "__main__":
    main()
