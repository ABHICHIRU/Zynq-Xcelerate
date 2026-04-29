# AXI Interface Protocol Specification

## AXI-Stream Slave Interface

### Functional Description
Accepts RF signal samples (I/Q components) from upstream sources (ADC, software, or other FPGA modules).

### Signal Specifications

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `clk` | 1 | IN | System clock |
| `rst_n` | 1 | IN | Asynchronous active-low reset |
| `s_axis_tdata` | 16 | IN | Sample data (I or Q component) |
| `s_axis_tvalid` | 1 | IN | Input valid indicator |
| `s_axis_tready` | 1 | OUT | Ready for input data |

### Handshaking Protocol
- **Valid Transfer:** `s_axis_tvalid` AND `s_axis_tready` = 1
- **Data Acceptance:** Sampled on rising clock edge when both valid & ready are HIGH
- **Ready Behavior:** Module asserts `s_axis_tready=1` to accept data

### Data Format
- **Representation:** 16-bit signed 2's complement
- **Range:** -32768 to +32767
- **Unit:** Digital value from RF ADC
- **Endianness:** Little-endian (LSB first)

---

## AXI-Stream Master Interface

### Functional Description
Outputs convolution results with 3-cycle deterministic latency and AXI-compliant handshaking.

### Signal Specifications

| Signal | Width | Direction | Description |
|--------|-------|-----------|-------------|
| `clk` | 1 | IN | System clock (same as slave) |
| `rst_n` | 1 | IN | Asynchronous active-low reset |
| `m_axis_tdata` | 16 | OUT | Output convolution result |
| `m_axis_tvalid` | 1 | OUT | Output valid indicator |
| `m_axis_tready` | 1 | IN | Downstream ready signal |

### Handshaking Protocol
- **Valid Transfer:** `m_axis_tvalid` AND `m_axis_tready` = 1
- **Output Behavior:** Held stable until downstream accepts (`m_axis_tready=1`)
- **Backpressure:** Module respects `m_axis_tready` signal

### Data Format
- **Representation:** 16-bit signed 2's complement
- **Range:** -32768 to +32767 (with saturation)
- **Saturation Behavior:** Overflows clipped to min/max range
- **Latency:** Fixed 3 cycles after input valid

---

## AXI-Lite Slave Interface

### Functional Description
Allows ARM CPU to configure kernel coefficients and read status registers.

### Register Map

| Address | Name | Type | Width | Description |
|---------|------|------|-------|-------------|
| 0x00 | KERNEL_SEL | RW | 3 | Kernel size: 0=3-tap, 1=5-tap, 2=7-tap, 3=9-tap |
| 0x04 | COEFF_ADDR | RW | 4 | Target coefficient memory address |
| 0x08 | COEFF_DATA | RW | 16 | Coefficient value (read/write) |
| 0x0C | STATUS | RO | 8 | Module status flags |
| 0x10 | CONTROL | RW | 8 | Enable, reset, interrupt masks |

### Write Sequence (Loading Coefficients)
```
1. Set COEFF_ADDR = target address (0-15)
2. Set COEFF_DATA = coefficient value
3. Auto-write to BRAM on AXI write complete
4. Repeat for all coefficients
```

### Read Sequence (Status)
```
1. Read STATUS register
2. Monitor bit[0] = module_ready
3. Monitor bit[1] = output_valid
4. Monitor bit[2] = input_ready
```

### Timing
- **Write Latency:** 1-2 clock cycles
- **Read Latency:** 1 clock cycle
- **Response:** `OKAY` on successful transaction

---

## Clock Domain Crossing

### Single Clock Domain
All interfaces operate in same clock domain (`sys_clk`):
- Input AXI-Stream: `sys_clk`
- Output AXI-Stream: `sys_clk`
- AXI-Lite: `sys_clk`

### Synchronization
No CDC required. All transfers synchronized to rising edge of `sys_clk`.

---

## Reset Behavior

### Asynchronous Reset (Active-Low)
- **Signal:** `rst_n`
- **Type:** Asynchronous active-low
- **Action on Assert:** 
  - Shift registers cleared to 0
  - Accumulator reset to 0
  - Output registers reset to 0
  - Valid/ready signals deasserted

### Recovery Time
- Minimum recovery time before first data: 2 clock cycles

---

## Error Handling

### Saturation (Not an Error)
- Accumulator overflow triggers saturation
- Output clamped to ±32767
- No error flag set (saturations are expected in RF processing)

### Protocol Violations
- Unspecified behavior if AXI protocol rules violated
- Ensure `s_axis_tvalid`, `m_axis_tready` changes per AXI spec

---

## Example Transactions

### Single Input → Single Output
```
Cycle | Clk | ValidIN | ReadyIN | DataIN | ValidOUT | ReadyOUT | DataOUT | Notes
------|-----|---------|---------|--------|----------|----------|---------|-------
  1   | ↑   |    1    |    1    |  100   |    0     |    1     |    X    | Input captured, Stage 1
  2   | ↑   |    0    |    1    |   --   |    0     |    1     |    X    | Processing Stage 2
  3   | ↑   |    0    |    1    |   --   |    0     |    1     |    X    | Processing Stage 3
  4   | ↑   |    0    |    1    |   --   |    1     |    1     |  500    | Output valid (saturated)
  5   | ↑   |    0    |    1    |   --   |    0     |    1     |    X    | Output consumed
```

### Continuous Stream (100% Utilization)
```
Cycle | Clk | ValidIN | ReadyIN | DataIN | ValidOUT | ReadyOUT | DataOUT | Notes
------|-----|---------|---------|--------|----------|----------|---------|-------
  1   | ↑   |    1    |    1    |  100   |    0     |    1     |    X    | Sample 1, Stage 1
  2   | ↑   |    1    |    1    |  200   |    0     |    1     |    X    | Sample 2, Stage 2
  3   | ↑   |    1    |    1    |  300   |    0     |    1     |    X    | Sample 3, Stage 3
  4   | ↑   |    1    |    1    |  400   |    1     |    1     |  500    | Output[0], Stage 1 (Sample 4)
  5   | ↑   |    1    |    1    |  500   |    1     |    1     |  600    | Output[1], Stage 1 (Sample 5)
```

---

## Compliance & Standards
- **AXI Protocol:** AMBA AXI4-Lite (ARM AMBA 4.0)
- **AXI-Stream:** ARM AMBA 4.0 AXI4-Stream
- **Verilog:** IEEE 1364-2005 (Verilog HDL)
- **Tool:** Xilinx Vivado 2025.2

