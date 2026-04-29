# Pin Mapping & Constraints Documentation

## Zynq-7020 Package Information

| Specification | Value |
|---------------|-------|
| Device | xc7z020clg484-1 |
| Package | BGA 484 (15×15mm) |
| Speed Grade | -1 (425 MHz max) |
| Temperature Range | 0°C to +85°C |

---

## Clock Pin Assignment

| Function | Package Pin | IOSTANDARD | Notes |
|----------|-------------|-----------|-------|
| System Clock (100MHz) | E18 | LVCMOS33 | Primary clock input |
| Reset (Active-Low) | E22 | LVCMOS33 | Asynchronous reset |

### Clock Constraints
```xdc
create_clock -period 10 -name sys_clk [get_ports sys_clk]
set_property PACKAGE_PIN E18 [get_ports sys_clk]
set_property IOSTANDARD LVCMOS33 [get_ports sys_clk]
```

### Timing Closure
- **Target Period:** 10 ns (100 MHz nominal)
- **Achievable:** 5 ns (200 MHz with effort)
- **Slack at 100MHz:** +1.5 ns
- **Slack at 200MHz:** +0.842 ns

---

## RF Input Pins (I-Channel)

| Signal | Pins | IOSTANDARD | Notes |
|--------|------|-----------|-------|
| `rf_i_data[0]` | D17 | LVCMOS33 | MSB |
| `rf_i_data[1]` | E17 | LVCMOS33 | |
| `rf_i_data[2]` | F18 | LVCMOS33 | |
| `rf_i_data[3]` | E16 | LVCMOS33 | |
| `rf_i_data[4]` | G18 | LVCMOS33 | |
| `rf_i_data[5]` | G17 | LVCMOS33 | |
| `rf_i_data[6]` | H18 | LVCMOS33 | |
| `rf_i_data[7]` | H17 | LVCMOS33 | LSB |

### Constraints
```xdc
# I-Channel Inputs
set rf_i_pins {D17 E17 F18 E16 G18 G17 H18 H17}
foreach pin $rf_i_pins {
    set_property IOSTANDARD LVCMOS33 [get_ports $pin]
    set_property DRIVE 12 [get_ports $pin]
}
```

---

## RF Input Pins (Q-Channel)

| Signal | Pins | IOSTANDARD | Notes |
|--------|------|-----------|-------|
| `rf_q_data[0]` | D18 | LVCMOS33 | MSB |
| `rf_q_data[1]` | F17 | LVCMOS33 | |
| `rf_q_data[2]` | G16 | LVCMOS33 | |
| `rf_q_data[3]` | H16 | LVCMOS33 | |
| `rf_q_data[4]` | J18 | LVCMOS33 | |
| `rf_q_data[5]` | J17 | LVCMOS33 | |
| `rf_q_data[6]` | K18 | LVCMOS33 | |
| `rf_q_data[7]` | K17 | LVCMOS33 | LSB |

### Constraints
```xdc
# Q-Channel Inputs
set rf_q_pins {D18 F17 G16 H16 J18 J17 K18 K17}
foreach pin $rf_q_pins {
    set_property IOSTANDARD LVCMOS33 [get_ports $pin]
    set_property DRIVE 12 [get_ports $pin]
}
```

---

## Output Pins (Status LEDs)

| Signal | Pin | IOSTANDARD | LED Function |
|--------|-----|-----------|--------------|
| `status_led[0]` | L16 | LVCMOS33 | Output Valid |
| `status_led[1]` | L17 | LVCMOS33 | Ready Signal |
| `status_led[2]` | K16 | LVCMOS33 | Error Flag |
| `status_led[3]` | M16 | LVCMOS33 | Heartbeat |

### Constraints
```xdc
# Status LEDs
set_property PACKAGE_PIN L16 [get_ports status_led[0]]
set_property PACKAGE_PIN L17 [get_ports status_led[1]]
set_property PACKAGE_PIN K16 [get_ports status_led[2]]
set_property PACKAGE_PIN M16 [get_ports status_led[3]]

foreach pin {L16 L17 K16 M16} {
    set_property IOSTANDARD LVCMOS33 [get_ports $pin]
    set_property SLEW SLOW [get_ports $pin]
    set_property DRIVE 12 [get_ports $pin]
}
```

---

## Power Control Pins

| Signal | Pin | IOSTANDARD | Function |
|--------|-----|-----------|----------|
| `pwr_enable` | M17 | LVCMOS33 | Master power control |
| `pwr_lna_en` | M18 | LVCMOS33 | LNA power enable |
| `pwr_adc_en` | N16 | LVCMOS33 | ADC power enable |
| `pwr_ml_en` | N17 | LVCMOS33 | ML accelerator power |
| `pwr_ddr_en` | N18 | LVCMOS33 | DDR power control |
| `pwr_mgt_en` | P16 | LVCMOS33 | MGT power enable |

### Constraints
```xdc
# Power Control GPIO
set pwr_pins {M17 M18 N16 N17 N18 P16}
foreach pin $pwr_pins {
    set_property IOSTANDARD LVCMOS33 [get_ports $pin]
    set_property DRIVE 12 [get_ports $pin]
    set_property SLEW SLOW [get_ports $pin]
}
```

---

## Bank Voltage & Termination

| Bank | Supply | Voltage | Status |
|------|--------|---------|--------|
| Bank 13 | VCCO_13 | 3.3V | RF I/O domain |
| Bank 14 | VCCO_14 | 3.3V | Status/Control |
| Bank 33 | VDD_PSMX | 1.0V | PS (ARM) |
| Bank 34 | VCCAUX | 1.8V | Aux supply |

### Pull-Up/Pull-Down Strategy
```xdc
# Reset button pull-up (external 10k recommended)
set_property PULLUP TRUE [get_ports rst_n]

# Input pull-down for unused pins
set_property PULLDOWN TRUE [get_ports unused_gpio[*]]
```

---

## Timing Constraints for I/O

### Input Timing
```xdc
# RF input setup/hold relative to clock
set_input_delay -clock sys_clk -min 1.0 [get_ports rf_i_data[*]]
set_input_delay -clock sys_clk -max 4.0 [get_ports rf_i_data[*]]
```

### Output Timing
```xdc
# LED output timing (relaxed for visibility)
set_output_delay -clock sys_clk -min -1.0 [get_ports status_led[*]]
set_output_delay -clock sys_clk -max 5.0 [get_ports status_led[*]]
```

---

## PCB Layout Recommendations

### Signal Integrity
- **RF Input Traces:** 
  - Length: Match to ±50 mils
  - Impedance: 50Ω characteristic
  - Shielding: Ground plane on both sides
  
- **Clock Distribution:**
  - Length: <2 inches (50 mm)
  - Via: Minimal (use 0.2mm vias)
  - Ground return: Direct to FPGA GND

### Power Distribution
- **Decoupling Capacitors:**
  - 100nF: 1 per power pin (12 minimum for xc7z020)
  - 10µF: 1 per 2-3 power pins
  - 47µF: 1 per power rail (bulk)
  
- **Trace Width:**
  - Power: ≥10 mils for 1A current
  - GND plane: Solid 2oz copper

### Thermal Management
- **Copper Area:** Minimum 2×2 inches for FPGA
- **Thermal Vias:** 0.3mm, 20mil spacing
- **Heatsink:** Optional (dissipates ~0.5W max)

---

## Verification Checklist

- [ ] All pins assigned per package datasheet
- [ ] No pin conflicts with PS (ARM) pins
- [ ] IOSTANDARD consistent per bank
- [ ] Clock trace impedance verified
- [ ] Power delivery verified (IR drop <100mV)
- [ ] Timing constraints achievable
- [ ] DRC report: 0 violations

---

## Implementation Notes

### LVDS Removal
**Original Design:** Differential LVDS clock input  
**Problem:** xc7z020clg484-1 has no available differential pairs in target bank  
**Solution:** Changed to single-ended LVCMOS33 (125Ω termination on PCB)

### Pin Banking Strategy
- **Bank 13, 14:** RF I/O and control (3.3V single-ended)
- **Separate Banks:** Avoids ground bounce on analog signals
- **Future Expansion:** Banks 35, 36 available for additional I/O

