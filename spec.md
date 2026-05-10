# Precision Electronic Level Instrument — Hardware Design Specification

**Document version:** 0.3  
**Status:** Draft  
**Date:** May 2026  
**Schematic reference:** KiCad commit 03fac10 (finalized)

---

## 1. System Overview

A battery-powered, Bluetooth-enabled precision electronic level instrument for machine tool geometry inspection and granite surface plate qualification. The system combines a MEMS 3-axis inclinometer with a high-resolution pendulum-based capacitive precision sensor, a wireless interface to a companion Windows desktop application, and a local display for standalone use.

### 1.1 Physical Architecture

The instrument consists of three PCBs:

| Board | Description | Mounting |
|---|---|---|
| Main PCB | Microcontroller, power, display, connectivity, user interface | 3D printed plastic enclosure |
| SCL3300 daughter board | 3-axis MEMS inclinometer | Cast iron precision base via brass standoffs |
| PCAP04 daughter board ×2 | Capacitive pendulum readout (one per axis) | Cast iron precision base via brass standoffs |

The cast iron base (~150×40mm) provides the precision reference surface. The plastic enclosure mounts on top. All precision sensing is mechanically coupled directly to the cast iron, isolated from the plastic enclosure.

### 1.2 Key Specifications

| Parameter | Value |
|---|---|
| Measurement range (MEMS) | ±90° |
| Measurement range (pendulum) | ±1 mm/m |
| Pendulum resolution | ~0.001 µm/m (electronics limited) |
| Pendulum precision (workshop) | ~0.1 µm/m |
| Display | 2.7" Sharp Memory LCD, 400×240 monochrome |
| Connectivity | Bluetooth Low Energy (BLE 5.0) |
| USB | USB-C, Full Speed (charging + HID + MSD bootloader) |
| Battery | 1S LiPo, 1000 mAh |
| Battery life | ~20 hours at 30 mA average |
| Supply voltage | 3.3V (main rail), 3.3V (sensor rail), 5V (buzzer only) |

---

## 2. Power Supply

### 2.1 Architecture

```
1S LiPo 1000mAh (JST-PH 2.0mm)
    │
    ├── Reverse polarity protection (Q1 DMG2305UX P-MOSFET)
    │
    ├── U1 TP4056 (USB-C charging, CC/CV, 500mA charge current)
    │       └── Q2 FS8205A (cell protection FET)
    │
    ├── U2 LP5907MFX-3.3 LDO → 3V3 rail (MCU, RN4871, display logic, EEPROM, buzzer buffer)
    │       └── Enable pin controlled by STM32 PB9 (3V3_EN, active-high)
    │
    ├── U4 LP5907MFX-3.3 LDO → 3V3_Sensors rail (SCL3300, PCAP04 #1, PCAP04 #2)
    │       └── Enable controlled by LDO_EN (power-sheet sequencing logic)
    │
    └── U5 SD6210A boost converter → 5V0 rail (buzzer BZ1 only, via U8 74AHCT244)
            └── Enable controlled by STM32 PB8 (5V_EN, active-high)
```

### 2.2 Component Details

| Ref | Function | Part | Package | JLCPCB # | Notes |
|---|---|---|---|---|---|
| J2 | USB-C + battery charge input | USB-C receptacle | SMD | C165948 | CC1/CC2: 5.1 kΩ to GND |
| Q1 | Reverse polarity | DMG2305UX | SOT-23 | C144153 | P-channel MOSFET |
| U1 | LiPo charger | TP4056 | SOP-8 | C382139 | RPROG = 2 kΩ (R3 ‖ R5) → ~500 mA |
| Q2 | Cell protection FET | FS8205A | TSSOP-8 | C14212 | Dual N-channel |
| U2 | 3V3 LDO — main rail | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 250 mA; EN = PB9 |
| U4 | 3V3_Sensors LDO — sensor rail | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 250 mA; EN = LDO_EN (power-sheet logic) |
| U5 | 5 V boost converter | SD6210A | SOT-23-6 | C250809 | 2.8–5 V in, 5 V/250 mA out; EN = PB8 |
| Q3 | Charging control | AO3400A | SOT-23 | C20917 | N-ch MOSFET; controls TP4056 charge enable path |
| Q4 | Sense-divider isolation | AO3400A | SOT-23 | C20917 | N-ch MOSFET; disconnects BATTERY_SENSE divider lower leg in off-state to prevent battery drain |
| D1–D4 | Schottky diodes | BAT54WS | SOD-323 | — | Present in schematic; verify placement in power sheet |

### 2.3 Battery Cutoff

- Hardware cutoff: DW01A at ~3.0V (cell protection absolute minimum)
- Software cutoff: STM32 ADC monitors Vbat via resistor divider, disables LDO enable pin at 3.6V
- Usable capacity at 3.6V cutoff: ~70% of rated capacity (~700mAh)
- Runtime at 30mA average: ~23 hours

### 2.4 Vbat Measurement

Resistor divider on BAT+ → BATTERY_SENSE → PB14 (ADC_IN):

- R9 = 100 kΩ (high side, BAT+ to divider node)
- R6 = 33 kΩ (low side, divider node to Q4 drain → GND)
- Q4 (AO3400A, N-ch) in the lower leg disconnects the divider during off-state to prevent battery drain
- Scale factor: 33/(100+33) = 0.248 → 4.2 V × 0.248 = 1.04 V max ADC input (within 3.3 V ADC range)
- Software ADC reference: VREF+ = 3.3 V

### 2.5 USB-C Connector

USB-C with CC1/CC2 pulled to GND via 5.1kΩ resistors for 5V/500mA negotiation. USB data lines connect to STM32 USB peripheral.

### 2.6 Decoupling

Every power pin of every IC must have a 100nF ceramic capacitor placed as close as possible to the pin. Additional bulk capacitors (10µF) at LDO output and charge pump output.

---

## 3. Microcontroller

### 3.1 Device

**STM32G0B1RET6**
- Package: LQFP64-GP (10×10 mm, 0.5 mm pitch — same body as PIC32MX470 64-TQFP)
- Core: ARM Cortex-M0+, 64 MHz
- Flash: 512 KB
- RAM: 144 KB (without parity)
- Supply: 1.7–3.6V
- JLCPCB: C2829307

### 3.2 Clock

- Main crystal: 8 MHz, ±20 ppm, SMD 5032 package (Yangxing X50328MSB2GI, JLCPCB C115962)
- Main crystal load caps: 33 pF NP0 (0603). Crystal CL = 20 pF, C_stray ≈ 3 pF → C_load = 2×(20−3) = 34 pF → 33 pF (nearest E12)
- Main crystal pins: PF0-OSC_IN (pin 10), PF1-OSC_OUT (pin 11)
- PLL configuration: HSE 8 MHz → SYSCLK = 64 MHz
- USB clock: HSI48 internal RC + CRS locked to USB SOF packets → 48 MHz (no crystal required for USB)
- **RTC crystal (Y1):** 32.768 kHz, standard RTC crystal, on PC14 (OSC32_IN, pin 4) and PC15 (OSC32_OUT, pin 5)
  > **Note:** PC14/PC15 are also used for PCAP04 #2 SCL/SDA and the ~{RST} signal respectively. See open items.

### 3.3 Debug / Programming Interface

**J4 — 2×7, 50 mil (1.27 mm) pitch SMD header**, compatible with STLINK-V3MINIE.

| J4 Position | Signal | Net | Notes |
|---|---|---|---|
| 1 | VCC | 3V3 | Target voltage sense for STLINK |
| 2 | SWDIO | SWDIO | SWD data — see note below |
| 3 | GND | GND | |
| 4 | SWCLK | SWCLK | SWD clock — see note below |
| 5 | GND | GND | |
| 6 | SWO | SWO | Cortex-M0+ has no ITM; SWO not functional |
| 7 | NC | — | |
| 8 | ~{RST} | ~{RST} | Reset signal → PC15 |
| 9 | GND | GND | |
| 10 | DEBUG_UART_MCU_TO_PC | — | PD9 (UART TX from MCU) |
| 11 | DEBUG_UART_PC_TO_MCU | — | PD8 (UART RX to MCU) |
| 12–14 | GND / NC | — | |

> **SWD pin note:** Standard SWD pins on STM32G0B1 are PA13 (SWDIO) and PA14 (SWCLK). In this design, PA13/PA14 are used for PCAP04 #1 P3/P2 GPIO. The `SWDIO` and `SWCLK` nets on J4 appear connected to PA8/PB15 in the schematic. This is a known conflict requiring clarification: either PA13/PA14 must be routed to J4 for SWD to function, or SWD and PCAP04_1 P2/P3 cannot be used simultaneously. See Netlist.md open items.

### 3.4 Reset

NRST (pin 12) has a decoupling capacitor to GND. The `~{RST}` signal from J4 routes to PC15 — see Netlist.md open item 2.

### 3.5 BOOT0 / DFU Bootloader

PA14 doubles as BOOT0 on STM32G0B1. A pull-down resistor holds BOOT0 LOW for normal boot. To activate the ROM DFU bootloader, pull BOOT0 HIGH before reset — the device enumerates as a USB DFU device. No SPI flash required.

---

## 4. Peripheral Pin Allocation

### 4.1 Summary Table

All assignments verified from KiCad/mcu.kicad_sch global label coordinates. See Netlist.md §5 for full analysis and footnotes.

| Function | Signal | Direction | STM32 Pin (phys.) | Net name |
|---|---|---|---|---|
| **Power control** | | | | |
| 3.3 V main LDO enable | 3V3_EN | Out | PB9 (63) | 3V3_EN |
| 5 V boost enable | 5V_EN | Out | PB8 (62) | 5V_EN |
| Charge enable (active-low) | ~{CHARGE_EN} | Out | PB7 (61) | ~{CHARGE_EN} |
| Battery voltage sense | BATTERY_SENSE | ADC in | PB14 (34) | BATTERY_SENSE |
| Charge status sense | CHARGE_SENSE | In | PC4 (25) | CHARGE_SENSE |
| Standby sense | STANDBY_SENSE | In | PC5 (26) | STANDBY_SENSE |
| USB VBUS sense | VBUS_SENSE | In | PC7 (39) | VBUS_SENSE |
| **SPI — SCL3300 inclinometer** | | | | |
| SCK | SCL3300_SCK | SPI out | PB5 (59) | SCL3300_SCK |
| MOSI | SCL3300_MOSI | SPI out | PB3 (57) | SCL3300_MOSI |
| MISO | SCL3300_MISO | SPI in | PB4 (58) | SCL3300_MISO |
| CS (active-low) | SCL3300_CS | Out | PB6 (60) | SCL3300_CS |
| **I2C — PCAP04 #1** | | | | |
| SCL | PCAP04_1_SCL | I2C out | PC8 (48) | PCAP04_1_SCL |
| SDA | PCAP04_1_SDA | I2C bidir | PA15 (47) | PCAP04_1_SDA |
| Interrupt | PCAP04_1_INT | In | PA12 (44) | PCAP04_1_INT |
| GPIO P2 (optional) | PCAP04_1_P2 | Bidir | PA14 (46) | PCAP04_1_P2 |
| GPIO P3 (optional) | PCAP04_1_P3 | Bidir | PA13 (45) | PCAP04_1_P3 |
| **I2C — PCAP04 #2** | | | | |
| SCL | PCAP04_2_SCL | I2C out | PC14 (4) | PCAP04_2_SCL |
| SDA | PCAP04_2_SDA | I2C bidir | PC13 (3) | PCAP04_2_SDA |
| Interrupt | PCAP04_2_INT | In | PC10 (64) | PCAP04_2_INT |
| GPIO P2 (optional) | PCAP04_2_P2 | Bidir | PC11 (1) | PCAP04_2_P2 |
| GPIO P3 (optional) | PCAP04_2_P3 | Bidir | PC12 (2) | PCAP04_2_P3 |
| **I2C — EEPROM (U10)** | | | | |
| SCL | EEPROM_SCL | I2C out | PA4 (21) | EEPROM_SCL |
| SDA | EEPROM_SDA | I2C bidir | PA3 (20) | EEPROM_SDA |
| **SPI — Display (LS027B7DH01)** | | | | |
| SCK | DISP_SCK | SPI out | PB10 (30) | DISP_SCK |
| MOSI (SI) | DISP_MOSI | SPI out | PB0 (27) | DISP_MOSI |
| CS (SCS, active-high) | DISP_CS | Out | PB11 (31) | DISP_CS |
| VCOM toggle | DISP_VCOM | Out | PB1 (28) | DISP_VCOM |
| Display on/off | DISP_ON | Out | PB2 (29) | DISP_ON |
| **USART2 — RN4871 BLE** | | | | |
| TX (MCU→BLE) | BLE_UART_MCU_TO_BLE | Out | PD6 (56) | BLE_UART_MCU_TO_BLE |
| RX (BLE→MCU) | BLE_UART_BLE_TO_MCU | In | PD5 (55) | BLE_UART_BLE_TO_MCU |
| Reset (active-low) | ~{BLE_RST} | Out | PD4 (54) | ~{BLE_RST} |
| GPIO P0_2 (optional) | BLE_P0_2 | Bidir | PD2 (52) | BLE_P0_2 |
| GPIO P1_6 (optional) | BLE_P1_6 | Bidir | PD3 (53) | BLE_P1_6 |
| GPIO P1_7 (optional) | BLE_P1_7 | Bidir | PD0 (50) | BLE_P1_7 |
| GPIO P2_0 (optional) | BLE_P2_0 | Bidir | PC9 (49) | BLE_P2_0 |
| GPIO P3_6 (optional) | BLE_P3_6 | Bidir | PD1 (51) | BLE_P3_6 |
| **Debug UART (J4)** | | | | |
| TX (MCU→PC) | DEBUG_UART_MCU_TO_PC | Out | PD9 (41) | DEBUG_UART_MCU_TO_PC |
| RX (PC→MCU) | DEBUG_UART_PC_TO_MCU | In | PD8 (40) | DEBUG_UART_PC_TO_MCU |
| **USB FS** | | | | |
| D+ | USB_D+ | Bidir | PA9 (37) | USB_D+ |
| D− | USB_D- | Bidir | PC6 (38) | USB_D- |
| **Rotary encoder 1** | | | | |
| Channel A | ENC_1A | In | PA1 (18) | ENC_1A |
| Channel B | ENC_1B | In | PA2 (19) | ENC_1B |
| Push-button (active-low) | ~{ENC_1SW} | In | PA0 (17) | ~{ENC_1SW} |
| **Rotary encoder 2** | | | | |
| Channel A | ENC_2A | In | PC2 (15) | ENC_2A |
| Channel B | ENC_2B | In | PC3 (16) | ENC_2B |
| Push-button | ENC_2SW | In | PC1 (14) | ENC_2SW |
| **Temperature sensor** | | | | |
| Analog output | TEMP_SENSE | ADC in | PB13 (33) | TEMP_SENSE |
| **Buzzer** | | | | |
| Drive signal (3.3 V logic) | BUZZER | PWM out | PB12 (32) | BUZZER |
| **Status LEDs** | | | | |
| Power LED | LED_PWR | Out | PA6 (23) | LED_PWR |
| Status LED | LED_STATUS | Out | PA5 (22) | LED_STATUS |
| **SWD / debug** | | | | |
| SWO | SWO | Out | PA7 (24) | SWO |
| SWDIO | SWDIO | Bidir | PA8 (36)* | SWDIO |
| SWCLK | SWCLK | In | PB15 (35)* | SWCLK |
| Reset sense | ~{RST} | In | PC15 (5)* | ~{RST} |
| **Misc** | | | | |
| External reset (NRST) | — | — | pin 12 | hardware only |

*See §3.3 note regarding SWD pin conflict with PCAP04 and ~{RST} on PC15.

### 4.2 Peripheral Allocation

| Peripheral | Assignment | Pins |
|---|---|---|
| SPI (TBD) | SCL3300 inclinometer | PB3/PB4/PB5/PB6 |
| SPI (TBD) | Display LS027B7DH01 | PB0/PB10/PB11 (bit-bang or AF, verify) |
| I2C (TBD) | PCAP04 #1 | PC8/PA15 |
| I2C (TBD) | PCAP04 #2 | PC14/PC13 |
| I2C (TBD) | EEPROM (U10) | PA4/PA3 — dedicated bus |
| USART2 | RN4871 BLE module, 115200 baud | PD5/PD6 |
| USART (TBD) | Debug UART to J4 | PD8/PD9 |
| USB FS | USB-C (charging + HID + DFU); HSI48 + CRS | PA9/PC6 |
| ADC | BATTERY_SENSE, TEMP_SENSE | PB14, PB13 |
| Timer (PWM) | BUZZER (3.3 V drive to U8) | PB12 |
| Timer (PWM) | DISP_VCOM toggle (≥ 1 Hz) | PB1 |

> All SPI and I2C peripheral assignments require verification against the STM32G0B1RET6 alternate function table.  
> PCAP04 P2/P3 GPIO lines and RN4871 GPIO lines will be assigned to specific functions during firmware development.

---

## 5. Display

### 5.1 Device

**Sharp LS027B7DH01**
- Size: 2.7", 400×240 pixels, monochrome
- Technology: Memory-in-Pixel reflective LCD (no backlight)
- Interface: SPI write-only
- Supply: VDD = VDDA = 5V
- Logic inputs: 3V compatible (level shifted from 3.3V)
- FPC connector: 10-pin, 0.5mm pitch, integral tail

### 5.2 Power

- VDD and VDDA both connected to 5V rail from SD6210A
- VDD must rise before or simultaneously with VDDA
- 1µF ceramic decoupling on both VDD and VDDA

### 5.3 Signal Connections

| Display Pin | Signal | Connection |
|---|---|---|
| SCLK | SPI clock | 74AHCT244 output → SPI1 SCK |
| SI | SPI data in | 74AHCT244 output → SPI1 MOSI |
| SCS | Chip select | 74AHCT244 output → GPIO (active HIGH) |
| EXTCOMIN | VCOM inversion | 74AHCT244 output → GPIO (timer ISR toggle) |
| EXTMODE | COM mode select | Tied to VDD (5V) — external VCOM mode |
| DISP | Display on/off | 74AHCT244 output → GPIO |
| VDD | Digital supply | 5V rail |
| VDDA | Analog supply | 5V rail |
| VSS | Digital GND | GND |
| VSSA | Analog GND | GND |

### 5.4 Logic Level Shifting

All 5 logic signals (SCLK, SI, SCS, EXTCOMIN, DISP) shifted from 3.3V to 5V via:

**SN74AHCT244DBR** (TI, SSOP-20, JLCPCB C2868870)
- 8-channel unidirectional buffer, 3.3V in, 5V out
- OE1, OE2 tied to GND (always enabled)
- 3 channels spare

### 5.5 PCB Connector

**10-pin, 0.5mm pitch ZIF FPC connector** (bottom contact, SMD)
- Hirose FH12-10S-0.5SH or equivalent
- Position within 30mm of display window in enclosure (limited by FPC tail length)

### 5.6 VCOM Timing

EXTMODE = HIGH selects external VCOM mode. STM32 TIM3_CH1 (PA6 AF1) or a timer ISR toggles DISP_VCOM at 30 Hz (33 ms period). This prevents DC bias buildup in the liquid crystal cells. VCOM must toggle continuously whenever the display is powered.

### 5.7 Framebuffer Note

Full 400×240 monochrome framebuffer = 12,000 bytes. STM32G0B1 has 144 KB RAM — full framebuffer fits comfortably. Render line-by-line for updates; transmit only changed lines to minimise SPI activity.

---

## 6. Bluetooth Low Energy

### 6.1 Device

**RN4871-I/RM128** (Microchip, castellated module)
- BLE 5.0
- UART ASCII command interface
- Pre-certified FCC/CE
- 3.3V supply
- JLCPCB: C633941

### 6.2 Interface

UART at 115200 baud, 8N1

| Signal | STM32 Pin (phys.) | Direction | Notes |
|---|---|---|---|
| UART TX (MCU→BLE) | PD6 (56), USART2_TX | STM32 → RN4871 | 3.3V logic |
| UART RX (BLE→MCU) | PD5 (55), USART2_RX | RN4871 → STM32 | 3.3V logic |
| ~{BLE_RST} | PD4 (54) | STM32 → RN4871 | Active low hardware reset |
| GPIO P0_2–P3_6 | PD2/PD3/PD0/PC9/PD1 | TBD | Optional; usage determined in firmware |

### 6.3 GATT Service

Custom BLE service with two characteristics:

| Characteristic | UUID | Properties | Description |
|---|---|---|---|
| Measurement notify | 128-bit custom | Notify | Device → PC: angle data |
| Command write | 128-bit custom | Write | PC → Device: trigger commands |

Custom 128-bit UUIDs to be defined during firmware development.

### 6.4 Antenna Keep-out

Keep-out zone around RN4871 antenna: no copper, no vias, no traces within the area specified in the module datasheet. Place module at PCB edge where possible.

---

## 7. 3-Axis Inclinometer (SCL3300 Daughter Board)

### 7.1 Device

**Murata SCL3300-D01**
- 3-axis MEMS inclinometer
- Digital SPI interface
- Supply: 3.0–3.6V
- Current: 1.2mA typical
- Measurement modes: 4 selectable (Mode 4 preferred: lowest noise, 10Hz ODR)
- Noise: 0.0009°/√Hz (Mode 4, X/Z axes)
- Factory calibrated, no external calibration required
- Package: 12-pin LCC (SMD, on daughter board)

### 7.2 Daughter Board

Separate small PCB (~30×25mm) with:
- SCL3300 + decoupling capacitors only
- 6-pin FFC connector (same physical standard as PCAP04 boards)
- Mounted to cast iron base via brass M3 standoffs, 4 corners

**Pinout of J3 (6-pin FFC, 1.0 mm pitch, main board side):**

| Pin | Signal | Description |
|---|---|---|
| 1 | 3V3_Sensors | 3.3 V supply (from U4 LDO) |
| 2 | SCL3300_CS | SPI chip select (active-low) |
| 3 | SCL3300_SCK | SPI clock |
| 4 | SCL3300_MISO | SPI data out (SCL3300 → MCU) |
| 5 | SCL3300_MOSI | SPI data in (MCU → SCL3300) |
| 6 | GND | Ground |

Connector: J3 (JUSHUO AFA07 or equivalent 6-pin 1.0 mm FFC ZIF).

### 7.3 Main Board Connection

J3 (SCL3300 FFC) is the only 6-pin FFC on the main board for sensor connections. J5 and J6 are 10-pin FFCs for PCAP04 #1 and #2 respectively.

**SPI timing:** Use SPI Mode 0, recommended clock 2–4 MHz per datasheet for best noise performance.

**Post-assembly calibration:** Perform system-level zero/offset calibration after final mechanical assembly with all standoffs torqued. Wait minimum 12 hours after reflow before calibrating.

---

## 8. Precision Capacitive Inclinometer (PCAP04 Boards)

### 8.1 Device

**Sciosense PCAP04-AQFM-24**
- Capacitance-to-digital converter with integrated DSP
- Input range: 1pF–100nF
- Resolution: up to 8aF at 2.5Hz
- Interface: I2C or SPI (I2C selected)
- Supply: 2.1–3.6V (3.3V nominal)
- Package: QFN-24, 4×4mm

### 8.2 I2C Configuration

Each PCAP04 board has a dedicated I2C bus. I2C (not SPI) is used in this design.

**PCAP04 #1 (J5) — SCL=PC8, SDA=PA15:**
- PCAP04 #1 I2C address: verify from PCAP04 datasheet (address depends on ADDR pin)
- Pull-ups on SCL/SDA to 3V3_Sensors on the daughter board

**PCAP04 #2 (J6) — SCL=PC14, SDA=PC13:**
- PCAP04 #2 I2C address: verify from PCAP04 datasheet
- Pull-ups on SCL/SDA to 3V3_Sensors on the daughter board

**EEPROM (U10) — SCL=PA4, SDA=PA3 (separate dedicated I2C bus)**

> EEPROM is on its own I2C bus, separate from both PCAP04 buses.

### 8.3 PCAP04 Daughter Boards (v2)

The PCAP04 v2 daughter boards are used. They expose both I2C and SPI interfaces but **only I2C is used**. Connector: 10-pin FFC.

**Pinout of J5 / J6 (10-pin FFC, main board side):**

| Pin | Signal | Description |
|---|---|---|
| 1 | 3V3_Sensors | 3.3 V supply |
| 2 | PCAP04_x_SCL | I2C clock |
| 3 | PCAP04_x_SDA | I2C data |
| 4–7 | GND / NC | Ground / no-connect |
| 8 | PCAP04_x_P3 | GPIO P3 (optional, usage TBD) |
| 9 | PCAP04_x_P2 | GPIO P2 (optional, usage TBD) |
| 10 | PCAP04_x_INT | Interrupt output (active-low) |

> **Compatibility note:** These 10-pin FFC connectors are **not compatible** with the old 6-pin FFC prototype boards.  
> New v2 daughter boards are required for use with this main board.

### 8.4 Mechanical Design (Pendulum Sensor)

The PCAP04 measures differential capacitance between two plates (~20mm diameter, 0.1mm gap) flanking a brass pendulum bob suspended from a thin metal foil pivot. Eddy current braking (permanent magnet near brass bob) provides damping. Pendulum length ~40mm to centre of gravity.

**Performance summary:**

| Parameter | Value |
|---|---|
| Capacitance per plate | ~28 pF |
| Sensitivity | ~53 fF/arcsecond |
| Resolution (8aF noise) | ~0.001 µm/m |
| Measurement range | ±1 mm/m |
| Natural frequency | ~2.5 Hz |

---

## 9. Firmware Update (DFU)

The W25Q80DV SPI flash has been removed. Firmware updates are handled by the STM32G0B1 built-in ROM DFU bootloader:

- No external flash required
- DFU activated by pulling BOOT0 (PA14/pin 46) HIGH during reset
- STM32 enumerates as USB DFU device (class 0xFE, subclass 0x01)
- Firmware downloaded via `dfu-util` or STM32CubeProgrammer over the existing USB-C port
- After programming, normal reset (BOOT0 LOW) boots from internal flash

The SPI2 bus is now dedicated to the SCL3300 sensor only (one device, one CS line).

---

## 10. EEPROM

### 10.1 Device

**Microchip 24LC256-I/ST**
- 256Kbit (32KB) EEPROM
- I2C interface
- 3.3V supply
- TSSOP-8 package
- JLCPCB: C87823

### 10.2 Purpose

Non-volatile storage for calibration coefficients, zero offsets, instrument configuration, and measurement history.

### 10.3 Connections

| EEPROM Pin | Connection | Notes |
|---|---|---|
| A0 | GND | I2C address bit 0 = 0 |
| A1 | GND | I2C address bit 1 = 0 |
| A2 | GND | I2C address bit 2 = 0 → address 0x50 |
| VSS | GND | |
| SDA | I2C SDA | Shared bus |
| SCL | I2C SCL | Shared bus |
| WP | GND | Write always enabled |
| VCC | 3.3V | 100nF decoupling |

---

## 11. Temperature Sensor

### 11.1 Device

**Texas Instruments LM35**
- Linear temperature sensor, 10mV/°C
- No calibration required
- Supply: 3.3V
- SOT-23 package
- JLCPCB: C9900081740

### 11.2 Purpose

Ambient temperature measurement for pendulum thermal drift compensation and data logging.

### 11.3 Placement

Mount on main PCB, away from heat sources (LP5907 LDO, TP4056, SD6210A charge pump). Placement near centre of board, not near USB-C connector or power section.

### 11.4 Connection

Output pin → STM32 PB1 (pin 28, ADC_IN9) via 100 Ω series resistor and 10 nF cap to GND (low-pass filter).

---

## 12. Buzzer

### 12.1 Device

**Same Sky (CUI) CPT-9019A-SMT-TR**
- SMD passive piezo transducer
- Resonant frequency: 4000 Hz
- Rated voltage: 3 Vp-p
- Capacitance: 12 nF (capacitive load — no driver transistor required)
- SPL: 75 dB typical / 72 dB minimum at 10 cm at 3 Vp-p
- Package: 9×9×1.9 mm SMD
- Operating temperature: −20 to +70 °C
- JLCPCB: C20181991

### 12.2 Drive

BZ1 is driven at **5 V** via the 74AHCT244 buffer (U8):

1. MCU PB12 (pin 32) outputs 3.3 V PWM signal (`BUZZER` net)
2. U8 (74AHCT244) level-shifts 3.3 V → 5 V (`BUZZER_5V` net)
3. 5 V signal drives BZ1

PWM frequency: buzzer resonant frequency (typically ~4 kHz). Duty cycle 50% for continuous tone. Shorter bursts for click feedback.

### 12.3 Connections

| Buzzer Pin | Net | Notes |
|---|---|---|
| + (signal) | BUZZER_5V | U8 (74AHCT244) output, 5 V |
| − (GND) | GND | |

### 12.4 Usage

| Event | Pattern |
|---|---|
| Encoder turn | Single short beep (e.g. 20 ms) |
| Button press | Double short beep (e.g. 2 × 10 ms) |
| Battery low warning | Slow repeating beep (firmware defined) |
| Error / invalid action | Long beep (firmware defined) |

---

## 13. User Interface

### 12.1 Rotary Encoders

Two mechanical rotary encoders with integral push-button switches.

**Debouncing:** RC filters only (no Schmitt trigger inverter). All 6 signals connect to STM32 GPIO pins with internal pull-ups. Additional software debounce (≥ 5 ms) required in firmware.

RC filter values (from schematic):
- Encoder A/B signals (4 lines): 33 kΩ + 10 nF (τ = 330 µs)
- Encoder switch signals (2 lines): 68 kΩ + 100 nF (τ = 6.8 ms)

**Encoder part:** Bourns PEC11R-4215F-S0024. JLCPCB: C143790. Incremental, 24 detents/rev, integrated push-button switch, 15 mm shaft, SMD.

**Encoder assignments:**
- Encoder 1: Navigation / value adjustment
- Encoder 2: Mode selection / confirmation

**Push buttons:** Short press = select/confirm, long press = back/cancel (defined in firmware).

### 12.2 Status LEDs

| LED | Colour | Function | Series resistor |
|---|---|---|---|
| LED_PWR | Green | Power on indicator | 330Ω |
| LED_STS | Blue | BLE connected / activity | 330Ω |

Both LEDs: 0603 SMD, active high from STM32 GPIO.

---

## 14. USB

### 13.1 Connector

USB-C receptacle, SMD, with CC1/CC2 pull-down resistors:
- CC1: 5.1kΩ to GND
- CC2: 5.1kΩ to GND
- Purpose: signals USB-C host to supply 5V/500mA (USB default power)

### 13.2 USB Interface

Implemented directly by STM32G0B1 internal USB peripheral (Full Speed, 12 Mbps).

**USB clock:** HSI48 internal 48 MHz RC oscillator locked to USB SOF via CRS (Clock Recovery System). No crystal required for USB operation.

**USB pin assignment:** D+ = PA9 (pin 37), D− = PC6 (pin 38). These are alternate USB pin positions on STM32G0B1 — verify AF table support before implementing USB driver.

**VBUS detection:** PC7 (pin 39) senses VBUS for cable presence detection.

### 13.3 USB Device Classes

| Class | Purpose |
|---|---|
| HID | Communication with Windows companion application |
| DFU | Firmware update via STM32 ROM DFU bootloader (USB DFU class) |
| CDC (optional) | Development/debug virtual COM port |

**DFU bootloader flow:** Pull BOOT0 (PA14) HIGH before reset → STM32 ROM DFU activates → host programs firmware via `dfu-util` or STM32CubeProgrammer → normal reset boots updated firmware. No SPI flash or external memory required.

---

## 15. Connectors and Headers

### 14.1 Connector Summary

| Ref | Type | Pins | Pitch | Purpose |
|---|---|---|---|---|
| J2 | USB-C receptacle | — | — | Charging + USB data |
| J3 | ZIF FFC | 6 | 1.0 mm | SCL3300 inclinometer daughter board |
| J4 | 2×7 50 mil SMD header | 14 | 1.27 mm | STLINK-V3MINIE SWD debug + debug UART |
| J5 | ZIF FFC | 10 | TBD | PCAP04 #1 daughter board (v2) |
| J6 | ZIF FFC | 10 | TBD | PCAP04 #2 daughter board (v2) |

The display (DS1, LS027B7DH01) FPC is integrated into the DS1 footprint — there is no separate FPC connector designator on the main board.

> J5 and J6 (10-pin FFC) are not compatible with earlier 6-pin FFC PCAP04 daughter boards. V2 daughter boards required.

### 14.2 Expansion Header (J8)

7-pin 100mil (2.54mm) through-hole header. **DNP (do not populate)** — footprint reserved for future hardware extensions. Place at board edge.

| Pin | Signal | Net | Notes |
|---|---|---|---|
| 1 | GND | GND | |
| 2 | +3.3V | +3V3 | |
| 3 | +5V | +5V | |
| 4 | EXP1 | EXP1 | Spare GPIO from STM32 (assign from 18 spare pins) |
| 5 | EXP2 | EXP2 | Spare GPIO from STM32 |
| 6 | EXP3 | EXP3 | Spare GPIO from STM32 |
| 7 | EXP4 | EXP4 | Spare GPIO from STM32 |

Specific spare pins to assign at PCB layout stage. Candidates: PD1–PD6 (pins 51–56), PB4/PB5 (pins 58/59).

### 14.3 FFC Cable Note

All three 6-pin FFC connectors on the main board are identical physical parts. The signal assignments at the daughter board end differ between SCL3300 and PCAP04 boards. Cable length should be sufficient to allow mechanical compliance between cast iron base and plastic enclosure — recommend 100–150mm.

---

## 16. Complete Bill of Materials

| Ref | Description | Part Number | Package | JLCPCB # | Qty |
|---|---|---|---|---|---|
| U6 | MCU STM32G0B1RET6 | STM32G0B1RET6 | LQFP64-GP | C2829307 | 1 |
| U7 | BLE module RN4871 | RN4871-I/RM128 | Castellated | C633941 | 1 |
| U1 | LiPo charger | TP4056 | SOP-8 | C382139 | 1 |
| U2 | 3.3 V LDO — main rail (3V3) | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 1 |
| U4 | 3.3 V LDO — sensor rail (3V3_Sensors) | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 1 |
| U5 | 5 V boost converter | SD6210A | SOT-23-6 | C250809 | 1 |
| U8 | Octal buffer 3.3V→5V (buzzer drive) | 74AHCT244 | SSOP-20 | C2868870 | 1 |
| U10 | EEPROM 32 KB | 24LC256-I/ST | TSSOP-8 | C87823 | 1 |
| Q1 | Reverse polarity P-ch MOSFET | DMG2305UX | SOT-23 | C144153 | 1 |
| Q2 | Cell protection FET | FS8205A | TSSOP-8 | C14212 | 1 |
| Q3 | Charge control N-ch MOSFET | AO3400A | SOT-23 | C20917 | 1 |
| Q4 | Sense-divider isolation N-ch MOSFET | AO3400A | SOT-23 | C20917 | 1 |
| D1–D4 | Schottky diode | BAT54WS | SOD-323 | — | 4 |
| Y1 (main) | Crystal 8 MHz | X50328MSB2GI | SMD-5032 | C115962 | 1 |
| Y1 (RTC) | Crystal 32.768 kHz | (TBD) | SMD | — | 1 |
| J2 | USB-C connector | TYPE-C-31-M-12 | SMD right-angle | C165948 | 1 |
| J3 | FFC ZIF 6-pin (SCL3300) | JUSHUO AFA07 | SMD ZIF 1.0 mm | — | 1 |
| J4 | Debug header 2×7 50 mil | (TBD) | SMD | — | 1 |
| J5, J6 | FFC ZIF 10-pin (PCAP04 ×2) | (TBD) | SMD ZIF | — | 2 |
| SW1, SW2 | Rotary encoder with switch | Bourns PEC11R-4215F-S0024 | SMD | C143790 | 2 |
| DS1 | Sharp Memory LCD 2.7" | LS027B7DH01 | FPC | C17492463 | 1 |
| BZ1 | Passive piezo transducer | CPT-9019A-SMT-TR | SMD 9×9 mm | C20181991 | 1 |
| — | Resistors 0603 | Various | 0603 | — | ~30 |
| — | Capacitors | 100 nF, 1 µF (0603); 4.7 µF, 10 µF (0805/1206) | — | — | ~40 |

> Components removed vs previous spec: DW01A (cell protection IC replaced by FS8205A alone), SN74HC14PWR Schmitt trigger (no longer used), SPI flash W25Q80DV (replaced by ROM DFU bootloader).

---

## 17. PCB Design Guidelines

### 16.1 Stack-up

4-layer PCB recommended:
- Layer 1: Signal + components (top)
- Layer 2: Ground plane (solid)
- Layer 3: Power planes (3.3V, 5V)
- Layer 4: Signal (bottom)

2-layer is acceptable for prototype if careful attention is paid to ground return paths.

### 16.2 Layout Priorities

1. Crystal and load capacitors as close to OSC1/OSC2 as possible, keep traces short, no other signals nearby
2. USB D+/D- routed as differential pair, matched length, 90Ω differential impedance, no vias
3. RN4871 at board edge, antenna keep-out observed, no copper under antenna area
4. Power section (TP4056, DW01A, LDO, charge pump) grouped together away from sensitive signals
5. 74AHCT244 between STM32 and display connector, short trace path
6. 10-pin display ZIF connector positioned within 30mm of display window location
7. Three 6-pin FFC connectors grouped at one edge of board for cable routing to cast iron base
8. U5B (3.3V_DBOARD LDO) placed close to the three FFC connectors with short traces to the 3.3V_DBOARD power pour; minimises resistive drop on the daughter board supply
9. LM35 away from heat sources, near centre of board

### 16.3 Decoupling Strategy

- 100 nF 0603 ceramic at every power pin, placed within 1 mm of pin
- 4.7 µF at STM32 VDD/VDDA (pin 8) as primary bulk cap; additional 100 nF directly at pin
- 1 µF + 10 nF at STM32 VREF+ (pin 7)
- 100 nF at STM32 VBAT (pin 6)
- 4.7 µF 0805 at STM32 VDD bulk; 10 µF 0805/1206 at LDO output and charge pump output
- 1 µF ceramic at display VDD and VDDA
- Keep decoupling capacitor ground via as short as possible — direct to ground plane
- **No VCAP capacitor needed** — STM32G0 has fully integrated core regulator (no external filter cap)

### 16.4 Ground

Single ground plane on layer 2. Star topology from main ground point near power section. No ground splits. Analogue and digital signals share the same ground plane — this is acceptable for this design given the SCL3300 and PCAP04 are fully digital devices. The only analogue signals are Vbat sense and LM35 output, both low frequency.

---

## 18. Mechanical

### 17.1 PCB Dimensions

To be defined. Target: fits within 150×35mm footprint of plastic enclosure with display centred on top face.

### 17.2 Enclosure

3D printed (PETG or ASA). Brass heat-set inserts for all screw attachment points. Display window with minimal bezel. Encoder knobs accessible from top/front panel. USB-C and ICSP header accessible from end panel. LED indicators visible from top.

### 17.3 Precision Base

Cast iron, approximately 150×40×20mm. Precision lapped bottom surface. Tapped holes for brass standoffs supporting sensor PCBs. Material: grey cast iron for vibration damping and thermal stability.

### 17.4 Sensor PCB Mounting

SCL3300 and PCAP04 PCBs mount directly to cast iron via 4× M3 brass standoffs each. All standoffs torqued to consistent value. PCBs must be flat — any bow introduces sensor offset. Perform zero calibration after final assembly with all hardware at operating temperature.

---

## 19. Firmware Architecture (Outline)

### 18.1 Boot Sequence

1. Check BOOT0 (PA14, shared with PCAP04_1_P2) state: if HIGH → STM32 ROM DFU bootloader handles firmware update, enumerates USB DFU
2. Normal boot (BOOT0 LOW): STM32 jumps to user application at `0x08000000`
3. Firmware initialises all peripherals, starts main loop

### 18.2 Main Tasks

| Task | Rate | Notes |
|---|---|---|
| SCL3300 read | 10 Hz | SPI, Mode 0, PB3–PB6 |
| PCAP04 read | 2–10 Hz | I2C; #1 on PC8/PA15, #2 on PC14/PC13 |
| Sensor fusion | 10 Hz | Complementary filter: pendulum < 0.5 Hz, MEMS > 0.5 Hz |
| BLE notify | On measurement | USART2 to RN4871 (PD5/PD6) |
| Display update | 10 Hz | Redraw changed lines only |
| VCOM toggle | ≥ 1 Hz | PB1 PWM — must run whenever display is powered |
| Vbat ADC | 1 Hz | PB14 ADC; software cutoff at 3.6 V |
| Temperature ADC | 0.1 Hz | PB13 ADC |
| USB service | As needed | HID + DFU; PA9/PC6 |
| Encoder service | GPIO interrupt | RC-filtered inputs; software debounce ≥ 5 ms |

### 18.3 BLE Protocol

Custom GATT service. Measurement notification packet format (to be defined):
- X-axis angle (pendulum, µm/m, 32-bit float)
- Y-axis angle (SCL3300, µm/m, 32-bit float)
- Z-axis angle (SCL3300, µm/m, 32-bit float)
- Temperature (°C, 16-bit fixed point)
- Status flags (battery, BLE, sensor health)
- Timestamp (ms since power-on)

---

## 20. Open Items

| Item | Description | Priority |
|---|---|---|
| **SWD vs PCAP04_1 pin conflict** | PA13/PA14 used for PCAP04_1_P3/P2 AND are the hardware SWD pins. Schematic shows SWDIO/SWCLK at PA8/PB15 — verify if this is intentional routing or an error. Clarify with designer before firmware implementation. | **High** |
| **~{RST} on PC15 / RTC crystal** | PC15 carries ~{RST} from J4. PC14/PC15 are also OSC32_IN/OUT for RTC crystal Y1. Clarify: is Y1 fitted? If yes, PCAP04_2 SCL/SDA (PC14/PC13) and ~{RST} (PC15) conflict. Decision: use LSI for RTC or do not populate Y1. | **High** |
| **USB alternate pin mapping** | USB D+=PA9, D−=PC6 (non-standard). Verify STM32G0B1 AF table supports USB FS on these pins before USB driver development. | **High** |
| **PCAP04 I2C addresses** | Verify I2C addresses for PCAP04 #1 and #2 from PCAP04 datasheet (ADDR pin configuration). | Medium |
| **10-pin FFC connector parts** | Select specific parts for J5 and J6 (10-pin FFC ZIF). Confirm pitch (0.5 mm or 1.0 mm) matches v2 PCAP04 daughter boards. | Medium |
| **J4 debug header part** | Confirm 50-mil 2×7 SMD header part number for J4. | Medium |
| **RTC crystal Y1** | Select 32.768 kHz crystal if RTC crystal is to be used. Confirm PC14/PC15 are not conflicting. | Medium |
| **EEPROM I2C address** | Confirm address pin wiring (A0/A1/A2) for U10 in schematic. Default 0x50 assumed. | Low |
| **Display SPI peripheral** | PB0 (MOSI) and PB10/PB11 (SCK/CS) — verify compatible STM32G0B1 AF or use bit-banged SPI. | Medium |
| **VCOM timer** | Confirm timer and pin AF for DISP_VCOM (PB1) PWM. Must toggle ≥ 1 Hz continuously when display is on. | Medium |
| **Buzzer resonant frequency** | Confirm BZ1 resonant frequency and set PWM accordingly on PB12. | Low |
| **Custom BLE UUIDs** | Define 128-bit UUIDs for measurement notification and command write characteristics. | Medium |
| **PCB dimensions** | Define main board outline matching enclosure. | Medium |
| **LiPo cell dimensions** | Select cell fitting enclosure, confirm JST-PH polarity. | Medium |
| **5V boost validation** | Verify SD6210A output voltage under load (buzzer) at minimum battery (3.6V input). | Low |
| ~~FFC pitch~~ | ~~Confirmed: J3 = 1.0 mm pitch~~ | ~~Resolved~~ |
| ~~Crystal load caps~~ | ~~33 pF (CL=20 pF, C_stray≈3 pF)~~ | ~~Resolved~~ |
| ~~Encoder selection~~ | ~~Bourns PEC11R-4215F-S0024 (C143790)~~ | ~~Resolved~~ |
| ~~USB-C connector~~ | ~~TYPE-C-31-M-12 (C165948)~~ | ~~Resolved~~ |

---

*End of specification*
