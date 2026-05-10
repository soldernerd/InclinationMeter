# InclinationMeter — Netlist & Hardware Reference

**Version:** 1.0  
**Date:** 2026-05-09  
**Source:** Finalized KiCad 10 schematics (commit 03fac10)  
**Schematic tool:** KiCad 10.0, library: sldrnrd_kicad_lib

> This document is the single source of truth for firmware development.  
> All pin assignments, net names, and component roles are derived directly  
> from the KiCad schematics. Do not rely on older documents.

---

## 1. Schematic Hierarchy

| Sheet file | Description |
|------------|-------------|
| `InclinationMeter.kicad_sch` | Root sheet (title block, hierarchy) |
| `KiCad/power.kicad_sch` | Power management, battery charging, LDOs, boost converter |
| `KiCad/mcu.kicad_sch` | MCU (U6), BLE module (U7), all MCU signal routing |
| `KiCad/ui.kicad_sch` | Display (DS1), encoders (SW1/SW2), LEDs, buzzer |
| `KiCad/connectors.kicad_sch` | External connectors: J2–J6, sensor headers |

Global labels are used for all inter-sheet net connections.

---

## 2. Power Architecture

### 2.1 Power Rails

| Rail | Voltage | Source | Enabled by |
|------|---------|--------|------------|
| `BAT+` | 3.0–4.2 V | Battery (J2 USB-C charge input) | always |
| `3V3` | 3.3 V | U2 LP5907MFX-3.3 LDO | `3V3_EN` (PB9, active-high) |
| `3V3_Sensors` | 3.3 V | U4 LP5907MFX-3.3 LDO | `LDO_EN` (power-sheet local, tied to both LDOs) |
| `5V0` | 5.0 V | U5 SD6210A boost converter | `5V_EN` (PB8, active-high) |
| `VBUS` | 5.0 V | USB-C input | external |

`3V3` powers: MCU (U6), BLE module (U7), EEPROM (U10), display (DS1), buzzer buffer (U8).  
`3V3_Sensors` powers: SCL3300 (U3/J3), PCAP04 #1 (J5), PCAP04 #2 (J6).  
`5V0` powers: buzzer (BZ1) via U8 buffer output.

> **Note:** `LDO_EN` is a local net in power.kicad_sch that enables both LP5907 LDOs (U2 and U4) simultaneously. There is no separate MCU GPIO for `LDO_EN`; it is driven by the power sequencing circuit on the power sheet.

### 2.2 Power Switching

| Component | Type | Function |
|-----------|------|----------|
| Q3 | AO3400A (N-ch MOSFET) | Battery charging control |
| Q4 | AO3400A (N-ch MOSFET) | Battery sense divider isolation (prevents drain in off-state) |
| Q2 | FS8205A (dual N-ch MOSFET) | Battery FET (reverse protection / disconnect) |
| Q1 | DMG2305UX (P-ch MOSFET) | Charge enable gate control |
| D1–D4 | BAT54WS (Schottky) | Flyback / reverse-blocking diodes |

### 2.3 Battery Charger

| Component | Value/Type | Net | Notes |
|-----------|-----------|-----|-------|
| U1 | TP4056 | — | 1-cell Li-Ion charger |
| R3 | 2 kΩ | RPROG | Sets charge current ≈ 500 mA |
| R5 | 2 kΩ | — | Second RPROG (parallel path) |

Charger outputs: `CHARGE_SENSE` (GPIO input, PC4), `~{CHARGE_EN}` (GPIO output, PB7, active-low).

### 2.4 Battery Voltage Sense

Resistor divider on `BAT+` → `BATTERY_SENSE` → PB14 (ADC input):

| Component | Value |
|-----------|-------|
| R9 | 100 kΩ (upper) |
| R6 | 33 kΩ (lower) |

Divider ratio: 33k/(100k+33k) = 0.248. Full battery (4.2 V) → 1.041 V on ADC. Use VREF+ = 3.3 V for ADC reference.

### 2.5 Power Control Signals

| Net | Direction | MCU Pin | Description |
|-----|-----------|---------|-------------|
| `3V3_EN` | Output | PB9 | Enables U2 LP5907 (3V3 rail). Active-high. |
| `5V_EN` | Output | PB8 | Enables U5 SD6210A (5V0 rail). Active-high. |
| `~{CHARGE_EN}` | Output | PB7 | Disables TP4056 charger. Active-low (low = charging enabled). |
| `PWR_ON` | — | — | Power-on latch signal (power sheet logic) |
| `STANDBY_SENSE` | Input | PC5 | Detects low-power standby condition |
| `VBUS_SENSE` | Input | PC7 | Detects USB-C VBUS presence (5 V from host) |

---

## 3. Component List

### 3.1 ICs

| Ref | Part | Description | Sheet |
|-----|------|-------------|-------|
| U1 | TP4056 | Li-Ion 1-cell battery charger, SOT-23-6 | power |
| U2 | LP5907MFX-3.3/NOPB | 3.3 V LDO, 250 mA, SOT-23-5; supplies `3V3` | power |
| U3 | SCL3300 | 3-axis inclinometer, SPI, SO-14 | connectors (via J3) |
| U4 | LP5907MFX-3.3/NOPB | 3.3 V LDO, 250 mA, SOT-23-5; supplies `3V3_Sensors` | power |
| U5 | SD6210A | 5 V synchronous boost converter; supplies `5V0` | power |
| U6 | STM32G0B1RET6 | MCU, Cortex-M0+, LQFP64 | mcu |
| U7 | RN4871-I/RM128 | BLE 5.0 module (UART interface) | mcu |
| U8 | 74AHCT244 | Octal buffer/driver (3.3 V → 5 V level shift for buzzer) | ui |
| U9 | PCAP04 | Capacitance-to-digital converter #2 (I2C) | connectors (via J6) |
| U10 | AT24Cxx | I2C EEPROM | mcu |
| U11 | PCAP04 | Capacitance-to-digital converter #1 (I2C) | connectors (via J5) |

> U3 (SCL3300) mounts on a daughter board connected via J3 (6-pin FFC).  
> U11 and U9 (PCAP04) mount on daughter boards connected via J5 and J6 (10-pin FFC).

### 3.2 Discrete Semiconductors

| Ref | Part | Function |
|-----|------|----------|
| Q1 | DMG2305UX | P-ch MOSFET, charger gate |
| Q2 | FS8205A | Dual N-ch MOSFET, battery protection FET |
| Q3 | AO3400A | N-ch MOSFET, battery charging control |
| Q4 | AO3400A | N-ch MOSFET, battery sense divider isolation |
| D1–D4 | BAT54WS | Schottky diode, SOD-323 |
| D5–D8 | (see schematic) | Additional diodes (power sheet) |

### 3.3 Passive Components (Key Values)

| Ref | Value | Function |
|-----|-------|----------|
| R3 | 2 kΩ | TP4056 RPROG (charge current) |
| R5 | 2 kΩ | TP4056 RPROG (parallel) |
| R6 | 33 kΩ | BATTERY_SENSE lower divider |
| R8 | 1 kΩ | Current limit resistor |
| R9 | 100 kΩ | BATTERY_SENSE upper divider |
| R10 | 68 kΩ | Pull-up/filter (power sheet) |
| Y1 | 32.768 kHz | RTC crystal (LQFP64 pins PC14/PC15, OSC32_IN/OUT) |

### 3.4 Connectors

| Ref | Part | Pins | Function |
|-----|------|------|----------|
| J2 | USB-C receptacle | — | USB data + battery charging input |
| J3 | Header_FFC_1.0mm_06 (JUSHUO AFA07) | 6 | SCL3300 sensor FFC |
| J4 | Header_50mil_2x07 | 14 (2×7) | SWD debug header (STLINK-V3MINIE) |
| J5 | FFC 10-pin | 10 | PCAP04 #1 sensor FFC |
| J6 | FFC 10-pin | 10 | PCAP04 #2 sensor FFC |

### 3.5 Electromechanical

| Ref | Part | Function |
|-----|------|----------|
| SW1 | Rotary encoder with push | Encoder 1 (ENC_1A/B/SW) |
| SW2 | Rotary encoder with push | Encoder 2 (ENC_2A/B/SW) |
| BZ1 | Piezo buzzer | Driven at 5 V via U8 (74AHCT244) |
| DS1 | LS027B7DH01 (Sharp Memory LCD) | 2.7" reflective display, SPI |

---

## 4. Connector Pinouts

### 4.1 J3 — SCL3300 FFC (6-pin, 1.0 mm pitch)

| Pin | Net | Direction | Description |
|-----|-----|-----------|-------------|
| 1 | 3V3_Sensors | — | 3.3 V supply for SCL3300 |
| 2 | SCL3300_CS | MCU→SCL3300 | SPI chip select (active-low) |
| 3 | SCL3300_SCK | MCU→SCL3300 | SPI clock |
| 4 | SCL3300_MISO | SCL3300→MCU | SPI data out |
| 5 | SCL3300_MOSI | MCU→SCL3300 | SPI data in |
| 6 | GND | — | Ground |

### 4.2 J4 — Debug Header (2×7, 50 mil pitch)

| Pin | Net | Description |
|-----|-----|-------------|
| 1 | VCC (3V3) | Target voltage sense for STLINK |
| 2 | SWDIO | SWD data |
| 3 | GND | Ground |
| 4 | SWCLK | SWD clock |
| 5 | GND | Ground |
| 6 | SWO | Serial Wire Output (trace, Cortex-M0+ — may not be functional) |
| 7 | — | NC |
| 8 | ~{RST} | Target reset |
| 9 | GND | Ground |
| 10 | DEBUG_UART_MCU_TO_PC | UART TX (MCU→PC) |
| 11 | DEBUG_UART_PC_TO_MCU | UART RX (PC→MCU) |
| 12–14 | GND / NC | — |

> The exact J4 pin-to-position mapping follows the STLINK-V3MINIE connector standard.  
> The debug UART uses PD9 (TX to PC) and PD8 (RX from PC).

### 4.3 J5 — PCAP04 #1 FFC (10-pin)

| Pin | Net | Direction | Description |
|-----|-----|-----------|-------------|
| 1 | 3V3_Sensors | — | 3.3 V supply |
| 2 | PCAP04_1_SCL | MCU→PCAP04 | I2C clock |
| 3 | PCAP04_1_SDA | Bidirectional | I2C data |
| 4–7 | GND / NC | — | Ground / no-connect |
| 8 | PCAP04_1_P3 | Bidirectional | PCAP04 port P3 (capacitance measurement) |
| 9 | PCAP04_1_P2 | Bidirectional | PCAP04 port P2 (capacitance measurement) |
| 10 | PCAP04_1_INT | PCAP04→MCU | Interrupt output |

### 4.4 J6 — PCAP04 #2 FFC (10-pin)

| Pin | Net | Direction | Description |
|-----|-----|-----------|-------------|
| 1 | 3V3_Sensors | — | 3.3 V supply |
| 2 | PCAP04_2_SCL | MCU→PCAP04 | I2C clock |
| 3 | PCAP04_2_SDA | Bidirectional | I2C data |
| 4–7 | GND / NC | — | Ground / no-connect |
| 8 | PCAP04_2_P3 | Bidirectional | PCAP04 port P3 |
| 9 | PCAP04_2_P2 | Bidirectional | PCAP04 port P2 |
| 10 | PCAP04_2_INT | PCAP04→MCU | Interrupt output |

> **Compatibility note:** J5 and J6 are 10-pin FFC connectors.  
> Existing prototype daughter boards using 6-pin FFC are **physically incompatible** with this main board.  
> New daughter boards are required.

---

## 5. MCU Pin Assignments — U6 (STM32G0B1RET6, LQFP64)

Pin assignments derived by coordinate analysis of `KiCad/mcu.kicad_sch`.  
All global labels connected to the MCU symbol are mapped below.

### 5.1 Left Edge — Pins 1–16

| Phys. Pin | Port | Net / Signal | Function |
|-----------|------|-------------|---------|
| 1 | PC11 | PCAP04_2_P2 | PCAP04 #2 port P2 |
| 2 | PC12 | PCAP04_2_P3 | PCAP04 #2 port P3 |
| 3 | PC13 | PCAP04_2_SDA | I2C SDA — PCAP04 #2 |
| 4 | PC14 | PCAP04_2_SCL | I2C SCL — PCAP04 #2 (also OSC32_IN if RTC crystal fitted) |
| 5 | PC15 | ~{RST} | External reset input from J4 debug header ¹ |
| 6 | VBAT | [VBAT] | RTC backup power (connect to 3V3 or coin cell) |
| 7 | VREF+ | [VREF+] | ADC reference (connect to 3V3) |
| 8 | VDD | [3V3] | Core supply |
| 9 | VSS | [GND] | Ground |
| 10 | PF0 | NC | OSC_IN (crystal not used on PF0/PF1) |
| 11 | PF1 | NC | OSC_OUT |
| 12 | ~{NRST} | — | Reset pin (no global label; see note ¹) |
| 13 | PC0 | NC | — |
| 14 | PC1 | ENC_2SW | Encoder 2 push-button (active-low, RC filter) |
| 15 | PC2 | ENC_2A | Encoder 2 channel A |
| 16 | PC3 | ENC_2B | Encoder 2 channel B |

¹ The `~{RST}` global label connects to PC15. The physical ~{NRST} pin (pin 12) has no global label in the schematic. This likely means PC15 is used as a software-monitored reset-request GPIO input, with firmware acting on it, rather than a hard-wired connection to NRST. Clarify with designer.

### 5.2 Top Edge — Pins 17–32

| Phys. Pin | Port | Net / Signal | Function |
|-----------|------|-------------|---------|
| 17 | PA0 | ~{ENC_1SW} | Encoder 1 push-button (active-low, RC filter) |
| 18 | PA1 | ENC_1A | Encoder 1 channel A |
| 19 | PA2 | ENC_1B | Encoder 1 channel B |
| 20 | PA3 | EEPROM_SDA | I2C SDA — EEPROM (U10) |
| 21 | PA4 | EEPROM_SCL | I2C SCL — EEPROM (U10) |
| 22 | PA5 | LED_STATUS | Status LED drive |
| 23 | PA6 | LED_PWR | Power LED drive |
| 24 | PA7 | SWO | Serial Wire Output ² |
| 25 | PC4 | CHARGE_SENSE | Charger status input (from TP4056 CHRG pin) |
| 26 | PC5 | STANDBY_SENSE | Standby/sleep detection input |
| 27 | PB0 | DISP_MOSI | Display SPI data (LS027B7DH01 SI) |
| 28 | PB1 | DISP_VCOM | Display VCOM toggle (timer PWM recommended) |
| 29 | PB2 | DISP_ON | Display power enable |
| 30 | PB10 | DISP_SCK | Display SPI clock |
| 31 | PB11 | DISP_CS | Display SPI chip select (SCS) |
| 32 | PB12 | BUZZER | Buzzer drive signal (MCU logic → U8 → 5 V buzzer) |

² STM32G0B1 (Cortex-M0+) does not have ITM/SWO hardware. The SWO pin is included for debug header compatibility but will not carry trace data.

### 5.3 Right Edge — Pins 33–48

| Phys. Pin | Port | Net / Signal | Function |
|-----------|------|-------------|---------|
| 33 | PB13 | TEMP_SENSE | Temperature sense ADC input |
| 34 | PB14 | BATTERY_SENSE | Battery voltage ADC input (R6/R9 divider) |
| 35 | PB15 | SWCLK | SWD clock signal to J4 — see note ³ |
| 36 | PA8 | SWDIO | SWD data signal to J4 — see note ³ |
| 37 | PA9 | USB_D+ | USB FS D+ (alternate pin mapping — see note ⁴) |
| 38 | PC6 | USB_D- | USB FS D− (alternate pin mapping — see note ⁴) |
| 39 | PC7 | VBUS_SENSE | USB VBUS detection |
| 40 | PD8 | DEBUG_UART_PC_TO_MCU | Debug UART RX |
| 41 | PD9 | DEBUG_UART_MCU_TO_PC | Debug UART TX |
| 42 | PA10 | NC | — |
| 43 | PA11 | NC | — |
| 44 | PA12 | PCAP04_1_INT | PCAP04 #1 interrupt input |
| 45 | PA13 | PCAP04_1_P3 | PCAP04 #1 port P3 — shared with SWDIO ³ |
| 46 | PA14 | PCAP04_1_P2 | PCAP04 #1 port P2 — shared with SWCLK ³ |
| 47 | PA15 | PCAP04_1_SDA | I2C SDA — PCAP04 #1 |
| 48 | PC8 | PCAP04_1_SCL | I2C SCL — PCAP04 #1 |

³ **SWD / PCAP04_1 pin conflict:** PA13 and PA14 are the hardware SWD pins (SWDIO/SWCLK) on all STM32G0B1 devices. In this schematic, PA13/PA14 are assigned to PCAP04_1_P3/P2. The `SWDIO` and `SWCLK` global labels (driving J4) appear at PA8/PB15 in the mcu.kicad_sch. Since PA8/PB15 are not standard SWD-capable pins, the STLINK connection via J4 must physically reach PA13/PA14. The SWDIO/SWCLK labels on PA8/PB15 may be routing artifacts in the schematic; verify with designer. During active SWD sessions, PCAP04_1 P2/P3 GPIO usage is inhibited.

⁴ **USB pin mapping:** Primary USB FS pins on STM32G0B1 are PA11 (D−) and PA12 (D+). The schematic assigns USB_D+ to PA9 and USB_D− to PC6. Verify in the STM32G0B1 alternate function table that USB remapping to PA9/PC6 is supported. PA11/PA12 are NC in this schematic.

### 5.4 Bottom Edge — Pins 49–64

| Phys. Pin | Port | Net / Signal | Function |
|-----------|------|-------------|---------|
| 49 | PC9 | BLE_P2_0 | RN4871 GPIO P2_0 ↔ MCU |
| 50 | PD0 | BLE_P1_7 | RN4871 GPIO P1_7 ↔ MCU |
| 51 | PD1 | BLE_P3_6 | RN4871 GPIO P3_6 ↔ MCU |
| 52 | PD2 | BLE_P0_2 | RN4871 GPIO P0_2 ↔ MCU |
| 53 | PD3 | BLE_P1_6 | RN4871 GPIO P1_6 ↔ MCU |
| 54 | PD4 | ~{BLE_RST} | RN4871 hardware reset (active-low output from MCU) |
| 55 | PD5 | BLE_UART_BLE_TO_MCU | UART RX from RN4871 (USART2 RX) |
| 56 | PD6 | BLE_UART_MCU_TO_BLE | UART TX to RN4871 (USART2 TX) |
| 57 | PB3 | SCL3300_MOSI | SPI MOSI to SCL3300 |
| 58 | PB4 | SCL3300_MISO | SPI MISO from SCL3300 |
| 59 | PB5 | SCL3300_SCK | SPI clock to SCL3300 |
| 60 | PB6 | SCL3300_CS | SPI chip select for SCL3300 (active-low) |
| 61 | PB7 | ~{CHARGE_EN} | TP4056 charge enable (active-low; low = charging allowed) |
| 62 | PB8 | 5V_EN | Enable 5 V boost (U5 SD6210A), active-high |
| 63 | PB9 | 3V3_EN | Enable 3.3 V main LDO (U2), active-high |
| 64 | PC10 | PCAP04_2_INT | PCAP04 #2 interrupt input |

---

## 6. Peripheral Interface Summary

### 6.1 SPI — SCL3300 Inclinometer

| Signal | MCU Pin | Net |
|--------|---------|-----|
| SCK | PB5 | SCL3300_SCK |
| MOSI | PB3 | SCL3300_MOSI |
| MISO | PB4 | SCL3300_MISO |
| CS | PB6 | SCL3300_CS |

SPI peripheral: **SPI1** (PB3–PB6 — verify alternate function in STM32G0B1 datasheet).  
Mode: SPI Mode 0 (CPOL=0, CPHA=0) per SCL3300 datasheet.  
Supply rail: `3V3_Sensors`.

### 6.2 I2C — PCAP04 #1

| Signal | MCU Pin | Net |
|--------|---------|-----|
| SCL | PC8 | PCAP04_1_SCL |
| SDA | PA15 | PCAP04_1_SDA |
| INT | PA12 | PCAP04_1_INT |
| P2 | PA14 | PCAP04_1_P2 |
| P3 | PA13 | PCAP04_1_P3 |

I2C peripheral: verify which I2C instance supports PC8/PA15 on STM32G0B1.  
Supply rail: `3V3_Sensors` (via J5).

### 6.3 I2C — PCAP04 #2

| Signal | MCU Pin | Net |
|--------|---------|-----|
| SCL | PC14 | PCAP04_2_SCL |
| SDA | PC13 | PCAP04_2_SDA |
| INT | PC10 | PCAP04_2_INT |
| P2 | PC11 | PCAP04_2_P2 |
| P3 | PC12 | PCAP04_2_P3 |

> PC13/PC14 are also OSC32_IN/OUT (RTC crystal pins). See open item 2 below.

### 6.4 I2C — EEPROM (U10)

| Signal | MCU Pin | Net |
|--------|---------|-----|
| SCL | PA4 | EEPROM_SCL |
| SDA | PA3 | EEPROM_SDA |

Dedicated I2C bus for EEPROM only (separate from both PCAP04 buses).

### 6.5 SPI — Display (LS027B7DH01)

| Signal | MCU Pin | Net |
|--------|---------|-----|
| SCK | PB10 | DISP_SCK |
| MOSI (SI) | PB0 | DISP_MOSI |
| CS (SCS) | PB11 | DISP_CS |
| VCOM | PB1 | DISP_VCOM |
| Power on | PB2 | DISP_ON |

3-wire SPI (no MISO). VCOM must toggle at ≥ 1 Hz to prevent display damage.  
PB0 and PB10 are on different default SPI peripherals — use bit-banged SPI or verify compatible AF assignment in STM32G0B1 datasheet.

### 6.6 UART — BLE (RN4871)

| Signal | MCU Pin | Net | Direction |
|--------|---------|-----|-----------|
| TX (MCU→BLE) | PD6 | BLE_UART_MCU_TO_BLE | Output |
| RX (BLE→MCU) | PD5 | BLE_UART_BLE_TO_MCU | Input |
| ~{RST} | PD4 | ~{BLE_RST} | Output (active-low) |

UART peripheral: **USART2** (PD5/PD6 — verify AF).  
Default baud rate: 115200 baud, 8N1.

RN4871 GPIO connections:

| RN4871 GPIO | MCU Pin | Net |
|-------------|---------|-----|
| P0_2 | PD2 | BLE_P0_2 |
| P1_6 | PD3 | BLE_P1_6 |
| P1_7 | PD0 | BLE_P1_7 |
| P2_0 | PC9 | BLE_P2_0 |
| P3_6 | PD1 | BLE_P3_6 |

### 6.7 UART — Debug (J4)

| Signal | MCU Pin | Net | Direction |
|--------|---------|-----|-----------|
| TX (MCU→PC) | PD9 | DEBUG_UART_MCU_TO_PC | Output |
| RX (PC→MCU) | PD8 | DEBUG_UART_PC_TO_MCU | Input |

UART peripheral: **USART3** or LPUART (PD8/PD9 — verify AF on STM32G0B1).

### 6.8 USB

| Signal | MCU Pin | Net |
|--------|---------|-----|
| D+ | PA9 | USB_D+ |
| D− | PC6 | USB_D- |
| VBUS sense | PC7 | VBUS_SENSE |

See note ⁴ in section 5.3 regarding non-standard USB pin assignment.

### 6.9 ADC Inputs

| Net | MCU Pin | Source |
|-----|---------|--------|
| BATTERY_SENSE | PB14 | R6/R9 voltage divider from BAT+ |
| TEMP_SENSE | PB13 | Temperature sensor (thermistor or IC output) |
| CHARGE_SENSE | PC4 | TP4056 CHRG status (open-drain, needs pull-up) |
| STANDBY_SENSE | PC5 | Standby detection |
| VBUS_SENSE | PC7 | USB VBUS (through resistor divider) |

### 6.10 User Interface

#### Encoders

Encoder RC filter values (from schematic):

| Filter | R | C | MCU Pins |
|--------|---|---|----------|
| ENC_1 A/B | 33 kΩ | 10 nF | PA1 (A), PA2 (B) |
| ENC_1 SW | 68 kΩ | 100 nF | PA0 |
| ENC_2 A/B | 33 kΩ | 10 nF | PC2 (A), PC3 (B) |
| ENC_2 SW | 68 kΩ | 100 nF | PC1 |

All encoder inputs are active-low. Configure GPIO as input with internal or external pull-up.  
The RC filters provide hardware debounce; add ≥ 5 ms software debounce in firmware.

#### LEDs

| Net | MCU Pin |
|-----|---------|
| LED_STATUS | PA5 |
| LED_PWR | PA6 |

#### Buzzer

BZ1 (piezo) driven at 5 V through 74AHCT244 (U8):  
PB12 (3.3 V PWM) → U8 input → `BUZZER_5V` net → BZ1.  
Use timer PWM on PB12 at the buzzer's resonant frequency (typically 2–4 kHz).

---

## 7. Net Glossary

| Net Name | Type | Description |
|----------|------|-------------|
| `3V3` | Power | 3.3 V main rail (U2 LDO) |
| `3V3_Sensors` | Power | 3.3 V sensor rail (U4 LDO) |
| `5V0` | Power | 5.0 V boost output (U5) |
| `BAT+` | Power | Battery positive |
| `BAT-` | Power | Battery negative (GND) |
| `VBUS` | Power | USB VBUS (5 V from host) |
| `BUZZER` | Signal | MCU buzzer drive (3.3 V logic) |
| `BUZZER_5V` | Signal | Buffered buzzer drive (5 V, U8 output) |
| `BLE_UART_MCU_TO_BLE` | Signal | UART TX from MCU to RN4871 |
| `BLE_UART_BLE_TO_MCU` | Signal | UART RX from RN4871 to MCU |
| `~{BLE_RST}` | Signal | RN4871 hardware reset (active-low, MCU output) |
| `BLE_P0_2` … `BLE_P3_6` | Signal | RN4871 GPIO lines |
| `SCL3300_SCK` | Signal | SPI clock to SCL3300 |
| `SCL3300_MOSI` | Signal | SPI MOSI to SCL3300 |
| `SCL3300_MISO` | Signal | SPI MISO from SCL3300 |
| `SCL3300_CS` | Signal | SPI CS for SCL3300 (active-low) |
| `PCAP04_1_SCL` | Signal | I2C SCL for PCAP04 #1 |
| `PCAP04_1_SDA` | Signal | I2C SDA for PCAP04 #1 |
| `PCAP04_1_INT` | Signal | Interrupt from PCAP04 #1 |
| `PCAP04_1_P2` | Signal | PCAP04 #1 measurement port P2 |
| `PCAP04_1_P3` | Signal | PCAP04 #1 measurement port P3 |
| `PCAP04_2_SCL` | Signal | I2C SCL for PCAP04 #2 |
| `PCAP04_2_SDA` | Signal | I2C SDA for PCAP04 #2 |
| `PCAP04_2_INT` | Signal | Interrupt from PCAP04 #2 |
| `PCAP04_2_P2` | Signal | PCAP04 #2 measurement port P2 |
| `PCAP04_2_P3` | Signal | PCAP04 #2 measurement port P3 |
| `EEPROM_SCL` | Signal | I2C SCL for EEPROM |
| `EEPROM_SDA` | Signal | I2C SDA for EEPROM |
| `DISP_SCK` | Signal | Display SPI clock |
| `DISP_MOSI` | Signal | Display SPI data |
| `DISP_CS` | Signal | Display SPI chip select |
| `DISP_VCOM` | Signal | Display VCOM toggle |
| `DISP_ON` | Signal | Display power enable |
| `ENC_1A` | Signal | Encoder 1 channel A (active-low) |
| `ENC_1B` | Signal | Encoder 1 channel B (active-low) |
| `~{ENC_1SW}` | Signal | Encoder 1 push-button (active-low) |
| `ENC_2A` | Signal | Encoder 2 channel A (active-low) |
| `ENC_2B` | Signal | Encoder 2 channel B (active-low) |
| `ENC_2SW` | Signal | Encoder 2 push-button (active-low) |
| `LED_STATUS` | Signal | Status LED drive |
| `LED_PWR` | Signal | Power LED drive |
| `BATTERY_SENSE` | Signal | Battery voltage ADC input |
| `TEMP_SENSE` | Signal | Temperature ADC input |
| `CHARGE_SENSE` | Signal | Charger status input |
| `~{CHARGE_EN}` | Signal | Charger enable (active-low MCU output) |
| `STANDBY_SENSE` | Signal | Standby condition input |
| `VBUS_SENSE` | Signal | USB VBUS detection |
| `5V_EN` | Signal | 5 V boost enable (active-high) |
| `3V3_EN` | Signal | 3.3 V main LDO enable (active-high) |
| `USB_D+` | Signal | USB FS D+ |
| `USB_D-` | Signal | USB FS D− |
| `SWDIO` | Signal | SWD data (J4 debug header) |
| `SWCLK` | Signal | SWD clock (J4 debug header) |
| `SWO` | Signal | Serial Wire Output (J4, not functional on Cortex-M0+) |
| `~{RST}` | Signal | External reset from J4 → PC15 |
| `DEBUG_UART_MCU_TO_PC` | Signal | Debug UART TX (MCU→PC via J4) |
| `DEBUG_UART_PC_TO_MCU` | Signal | Debug UART RX (PC→MCU via J4) |
| `PWR_ON` | Signal | Power-on latch (power sheet) |

---

## 8. Open Items / Firmware Notes

1. **SWD vs PCAP04_1_P2/P3 conflict (PA13/PA14):** The standard SWD pins PA13/PA14 are used for PCAP04_1_P3/P2. Disable these GPIOs before connecting STLINK. Continuous background debug is not possible while PCAP04_1 P2/P3 are actively driven.

2. **~{RST} on PC15 / RTC crystal conflict:** PC15 carries the `~{RST}` signal from J4. PC14/PC15 are also the OSC32_IN/OUT pins used by RTC crystal Y1. If Y1 is fitted and the RTC oscillator is enabled in hardware, PCAP04_2_SCL (PC14) and ~{RST} (PC15) will conflict with the crystal. Configure RTC to use the internal LSI oscillator if PCAP04 #2 is required, and verify the reset scheme with the hardware designer.

3. **USB pin mapping (PA9/PC6):** Primary USB pins on STM32G0B1 are PA11/PA12. Confirm that STM32G0B1 supports USB remapping to PA9 (D+) and PC6 (D−) before implementing the USB driver.

4. **Display SPI (PB0/PB10/PB11):** PB0 (MOSI) and PB10/PB11 (SCK/CS) span multiple SPI peripherals. Check the AF table or use bit-banged SPI.

5. **VCOM:** Toggle DISP_VCOM (PB1) at ≥ 1 Hz continuously. Failure to toggle will damage the LS027B7DH01 display. Implement via timer interrupt or PWM.

6. **Buzzer frequency:** Drive PB12 with PWM at the resonant frequency of BZ1. The 74AHCT244 (U8) level-shifts to 5 V. Check U8 output current against buzzer impedance.

7. **Encoder debounce:** Hardware RC filters present (33 kΩ + 10 nF for A/B, 68 kΩ + 100 nF for SW). Add ≥ 5 ms software debounce in addition.

8. **BLE UART:** RN4871 default 115200 baud, 8N1 on USART2 (PD5 RX, PD6 TX). RN4871 GPIO lines (P0_2–P3_6) function per RN4871 firmware configuration.

9. **EEPROM I2C address:** Depends on address pins A0/A1/A2 configuration. Check connectors.kicad_sch or power.kicad_sch for pull-up/down connections. Default AT24Cxx base address: 0x50.

10. **NRST pin (pin 12):** The physical NRST pin has no global label in the schematic. Verify in the power or connectors sheet that it is connected to a decoupling capacitor to GND (standard practice) and not floating.
