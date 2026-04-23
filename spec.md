# Precision Electronic Level Instrument — Hardware Design Specification

**Document version:** 0.2  
**Status:** Draft  
**Date:** April 2026

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
| Supply voltage | 3.3V (main rail), 5V (display only) |

---

## 2. Power Supply

### 2.1 Architecture

```
1S LiPo 1000mAh (JST-PH 2.0mm)
    │
    ├── Reverse polarity protection (DMG2305UX P-MOSFET + 100kΩ)
    │
    ├── TP4056 (USB-C charging, CC/CV, 500mA charge current)
    │       └── DW01A + FS8205A (cell protection)
    │
    ├── LP5907MFX-3.3 LDO #1 (U5) → 3.3V rail (STM32, RN4871, display logic, EEPROM, etc.)
    │       └── Enable pin controlled by STM32 PC0 (active high)
    │
    ├── LP5907MFX-3.3 LDO #2 (U5B) → 3.3V_DBOARD rail (SCL3300, PCAP04 #1, PCAP04 #2)
    │       └── Enable tied to VIN (always on when main power present)
    │
    └── SD6210A charge pump → 5V rail (display VDD/VDDA only)
```

### 2.2 Component Details

| Function | Part | Package | JLCPCB # | Notes |
|---|---|---|---|---|
| LiPo cell | 1S, 1000mAh, JST-PH | Flat pouch | — | Source separately |
| Battery connector | JST-PH 2.0mm 2-pin | Through-hole | — | Mark polarity on silkscreen |
| Reverse polarity | DMG2305UX | SOT-23 | C144153 | P-channel MOSFET, gate pull-down 100kΩ |
| Charger | TP4056 | SOP-8 | C382139 | RPROG = 2.4kΩ → 500mA charge current |
| Cell protection | DW01A | SOT-23-6 | C85680 | Over/under voltage + short circuit |
| Protection FETs | FS8205A | TSSOP-8 | C14212 | Dual N-channel, driven by DW01A |
| 3.3V LDO (U5) | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 250mA, 150mV dropout, ultra low noise — main rail, EN controlled by STM32 PC0 |
| 3.3V_DBOARD LDO (U5B) | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 250mA, 150mV dropout, ultra low noise — daughter boards only, EN tied to VIN |
| 5V charge pump | SD6210A | SOT-23-6 | C250809 | 2.8–5V in, regulated 5V out, 250mA |

### 2.3 Battery Cutoff

- Hardware cutoff: DW01A at ~3.0V (cell protection absolute minimum)
- Software cutoff: STM32 ADC monitors Vbat via resistor divider, disables LDO enable pin at 3.6V
- Usable capacity at 3.6V cutoff: ~70% of rated capacity (~700mAh)
- Runtime at 30mA average: ~23 hours

### 2.4 Vbat Measurement

Resistor divider to scale 4.2V max down to STM32 ADC range (3.3V):
- R1 = 100kΩ (high side, battery to divider)
- R2 = 390kΩ (low side, divider to GND)
- Scale factor: 390/(100+390) = 0.796 → 4.2V × 0.796 = 3.34V max → within 3.3V ADC range

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

- External crystal: 8 MHz, ±20 ppm, SMD 5032 package (Yangxing X50328MSB2GI, JLCPCB C115962)
- Load capacitors: 33 pF NP0 (0603). Crystal CL = 20 pF, C_stray ≈ 3 pF → C_load = 2×(20−3) = 34 pF → 33 pF (nearest E12)
- PLL configuration: HSE 8 MHz, M=1, N=16, R=2 → SYSCLK = 64 MHz
- USB clock: HSI48 internal RC + CRS locked to USB SOF packets → 48 MHz (no crystal required for USB)
- Crystal pins: PF0-OSC_IN (pin 10), PF1-OSC_OUT (pin 11)

### 3.3 Debug / Programming Interface (SWD)

**Samtec FTSH-107-01-L-DV-K** — SMD, 14-pin 2×7, 1.27 mm pitch, keyed shroud. JLCPCB: C5307809. Compatible with STLINK-V3MINIE:

| STDC14 Pin | Signal | Notes |
|---|---|---|
| 1 | VCC | +3V3 target power sense |
| 2 | SWDIO | PA13 (pin 45), via R_SWDIO (100 Ω) |
| 3 | GND | Ground |
| 4 | SWCLK | PA14 (pin 46), via R_SWCLK (100 Ω) |
| 5 | GND | Ground |
| 6 | SWO | NC (Cortex-M0+ has no ITM) |
| 7 | NC | No connect |
| 8 | NC | No connect |
| 9 | GND | Ground |
| 10 | NRST | PF2 (pin 12), reset signal |
| 11–14 | GND/NC | Ground / No connect |

### 3.4 Reset

10 kΩ pull-up on NRST to +3V3. 100 nF capacitor to GND for noise filtering.

### 3.5 BOOT0 / DFU Bootloader

PA14 doubles as BOOT0. A 10 kΩ pull-down resistor (R_BOOT0) holds BOOT0 LOW for normal boot from flash. To activate the STM32 ROM DFU bootloader, pull BOOT0 HIGH before or during reset — the device enumerates as a USB DFU device and accepts firmware via `dfu-util` or STM32CubeProgrammer. No SPI flash required.

---

## 4. Peripheral Pin Allocation

### 4.1 Summary Table

| Function | Signal | Direction | STM32 Pin | Notes |
|---|---|---|---|---|
| **Power** | | | | |
| Battery voltage sense | VBAT_SENSE | Analog in | PB0 (pin 27), ADC_IN8 | Via resistor divider |
| LDO enable | LDO_EN | Digital out | PC0 (pin 13) | Active high to enable LP5907 |
| Charge sense | CHG_SENSE | Digital in | PA9 (pin 37) | TP4056 CHRG pin, low = charging |
| **SPI1 — Display** | | | | |
| Display SCK | DISP_SCK | SPI out | PA5 (pin 22), SPI1_SCK AF0 | |
| Display MOSI | DISP_MOSI | SPI out | PA7 (pin 24), SPI1_MOSI AF0 | Write-only, no MISO |
| Display CS | DISP_CS | Digital out | PA4 (pin 21) | Active HIGH |
| Display ON/OFF | DISP_ON | Digital out | PA8 (pin 36) | High = display on |
| Display VCOM | DISP_VCOM | Digital out | PA6 (pin 23), TIM3_CH1 AF1 | Toggle ~30 Hz, hardware or GPIO |
| **SPI2 — SCL3300** | | | | |
| SPI2 SCK | SPI2_SCK | SPI out | PB13 (pin 33), SPI2_SCK AF0 | |
| SPI2 MOSI | SPI2_MOSI | SPI out | PB15 (pin 35), SPI2_MOSI AF0 | |
| SPI2 MISO | SPI2_MISO | SPI in | PB14 (pin 34), SPI2_MISO AF0 | |
| SCL3300 CS | SCL_CS | Digital out | PB12 (pin 32) | Active low |
| **I2C1 — PCAP04 #1 + EEPROM** | | | | |
| I2C1 SDA | I2C_SDA | I2C | PB9 (pin 63), I2C1_SDA AF6 | 4.7 kΩ pull-up to 3.3V |
| I2C1 SCL | I2C_SCL | I2C | PB8 (pin 62), I2C1_SCL AF6 | 4.7 kΩ pull-up to 3.3V |
| **I2C2 — PCAP04 #2** | | | | |
| I2C2 SDA | I2C2_SDA | I2C | PB11 (pin 31), I2C2_SDA AF6 | 4.7 kΩ pull-up to 3.3V |
| I2C2 SCL | I2C2_SCL | I2C | PB10 (pin 30), I2C2_SCL AF6 | 4.7 kΩ pull-up to 3.3V |
| **I2C GPIO — PCAP04 control** | | | | |
| PCAP04 #1 interrupt | PCAP1_INT | Digital in | PC6 (pin 38), EXTI6 | Active low |
| PCAP04 #2 interrupt | PCAP2_INT | Digital in | PC7 (pin 39), EXTI7 | Active low |
| PCAP04 #1 reset | PCAP1_RST | Digital out | PC9 (pin 49) | Active low |
| PCAP04 #2 reset | PCAP2_RST | Digital out | PD0 (pin 50) | Active low |
| **USART1 — RN4871 BLE** | | | | |
| BLE TX | BLE_TX | UART out | PB6 (pin 60), USART1_TX AF0 | STM32 TX → module RX |
| BLE RX | BLE_RX | UART in | PB7 (pin 61), USART1_RX AF0 | Module TX → STM32 RX |
| BLE reset | BLE_RST | Digital out | PA15 (pin 47) | Active low |
| BLE status | BLE_STATUS | Digital in | PC8 (pin 48) | RX_IND / status pin |
| **USB** | | | | |
| USB D+ | USB_DP | Dedicated | PA12 (pin 44) | Via 22 Ω series resistor |
| USB D− | USB_DM | Dedicated | PA11 (pin 43) | Via 22 Ω series resistor |
| USB sense | VBUS_SENSE | Digital in | PA10 (pin 42) | Detect USB connection (optional) |
| **Rotary encoders** | | | | |
| Encoder 1 A | ENC1_A | Digital in | PA0 (pin 17), EXTI0 | RC filter + 74HC14 |
| Encoder 1 B | ENC1_B | Digital in | PA1 (pin 18), EXTI1 | RC filter + 74HC14 |
| Encoder 1 SW | ENC1_SW | Digital in | PA2 (pin 19), EXTI2 | RC filter + 74HC14 |
| Encoder 2 A | ENC2_A | Digital in | PA3 (pin 20), EXTI3 | RC filter + 74HC14 |
| Encoder 2 B | ENC2_B | Digital in | PC4 (pin 25), EXTI4 | RC filter + 74HC14 |
| Encoder 2 SW | ENC2_SW | Digital in | PC5 (pin 26), EXTI5 | RC filter + 74HC14 |
| **Temperature sensor** | | | | |
| LM35 output | TEMP_SENSE | Analog in | PB1 (pin 28), ADC_IN9 | Via 100 Ω + 10 nF LP filter |
| **Buzzer** | | | | |
| Buzzer PWM | BUZZER | Digital out | PB3 (pin 57), TIM1_CH2 AF1 | Direct drive, no transistor |
| **Status LEDs** | | | | |
| Power LED | LED_PWR | Digital out | PC1 (pin 14) | Via 330 Ω series resistor |
| Status LED | LED_STS | Digital out | PC2 (pin 15) | Via 330 Ω series resistor |
| **SWD debug** | | | | |
| SWD data | SWDIO | Dedicated | PA13 (pin 45) | 100 Ω series to J3 header |
| SWD clock | SWCLK | Dedicated | PA14 (pin 46) | 100 Ω series to J3 header; 10 k pull-down |

**Total GPIO/AF used: 46 of 64 pins. Spare GPIO pins: 18.**

### 4.2 Peripheral Allocation

| Peripheral | Assignment |
|---|---|
| SPI1 | Display (dedicated, write-only) |
| SPI2 | SCL3300 (dedicated bus) |
| I2C1 | PCAP04 #1 + 24LC256 EEPROM (shared bus) |
| I2C2 | PCAP04 #2 (dedicated bus) |
| USART1 | RN4871 BLE module (115200 baud, 8N1) |
| USB FS | USB-C (charging + HID + DFU); clock from HSI48 + CRS |
| ADC | Vbat sense (PB0/IN8) + LM35 temperature (PB1/IN9) |
| TIM1_CH2 | Buzzer PWM (PB3, 4 kHz) |
| TIM3_CH1 | VCOM toggle for display (~30 Hz, optional hardware) |
| EXTI0–7 | Rotary encoder inputs + PCAP04 interrupts |

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

| Signal | STM32 Pin | Direction | Notes |
|---|---|---|---|
| UART_TX | PB6 (pin 60), USART1_TX AF0 | STM32 → RN4871 | 3.3V logic |
| UART_RX | PB7 (pin 61), USART1_RX AF0 | RN4871 → STM32 | 3.3V logic |
| RESET | PA15 (pin 47) | STM32 → RN4871 | Active low, 100 Ω series |
| STATUS / RX_IND | PC8 (pin 48) | RN4871 → STM32 | Status indication |

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

**Pinout of 6-pin FFC connector (SCL3300 board):**

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | +3.3V_DBOARD |
| 3 | SCK |
| 4 | MOSI |
| 5 | MISO |
| 6 | CS |

### 7.3 Main Board Connection

3 identical 6-pin ZIF FFC connectors on main board (one per daughter board). All same physical part, different signal assignments per connector type.

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

Each PCAP04 board has a dedicated I2C bus:

**I2C1 (SDA1/SCL1) — PCAP04 #1 + EEPROM:**
- PCAP04 #1: address pin LOW → I2C address 0x48 (verify in PCAP04 datasheet)
- 24LC256 EEPROM: A0=A1=A2=GND → I2C address 0x50
- 4.7kΩ pull-up on SDA1 and SCL1 to 3.3V

**I2C2 (SDA2/SCL2) — PCAP04 #2:**
- PCAP04 #2: address pin HIGH → I2C address 0x49 (existing hardware; address is irrelevant for disambiguation on a dedicated bus)
- 4.7kΩ pull-up on SDA2 and SCL2 to 3.3V

### 8.3 Existing Boards

Two prototype PCAP04 boards already exist. Pinout of 6-pin FFC connector:

| Pin | Signal |
|---|---|
| 1 | SDA |
| 2 | SCL |
| 3 | GND |
| 4 | RESET (active low) |
| 5 | +3.3V_DBOARD |
| 6 | INT (interrupt, active low) |

**FFC pitch:** 1.0 mm (confirmed from existing PCAP04 prototype boards).

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

Driven directly from STM32 TIM1_CH2 on PB3 (pin 57, AF1). No driver transistor or series resistor required — the piezo transducer is a capacitive load and 5 mA max is within STM32 GPIO capability.

PWM frequency: 4000 Hz (resonant frequency) for maximum SPL. Duty cycle 50% for continuous tone; shorter bursts for click feedback.

### 12.3 Connections

| Buzzer Pin | Net | Notes |
|---|---|---|
| + (signal) | BUZZER | STM32 PB3 (pin 57), TIM1_CH2 AF1 PWM output |
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

**Debouncing:** RC filter followed by 74HC14 Schmitt trigger inverter on each of 6 lines. All 6 signals connect to STM32 EXTI-capable GPIO pins (PA0–PA3, PC4, PC5).

- Encoder A/B signals (4 lines): 10 kΩ + 100 nF (τ = 1 ms)
- Encoder switch signals (2 lines): 100 kΩ + 100 nF (τ = 10 ms)

**Encoder part:** Bourns PEC11R-4215F-S0024. JLCPCB: C143790. Incremental, 24 detents/rev, integrated push-button switch, 15 mm shaft, SMD.

**74HC14 device:** SN74HC14PWR hex Schmitt trigger inverter, TSSOP-14 (TI). JLCPCB: C6821

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

**Series resistors:** 22 Ω on D+ and D− between USB-C connector and STM32 PA12/PA11 (pins 44/43).

**VBUS detection:** PA10 (pin 42) optionally senses VBUS for cable presence detection.

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

| Connector | Type | Pins | Pitch | Part | Purpose |
|---|---|---|---|---|---|
| Battery | JST-PH | 2 | 2.0mm | B2B-PH-K | LiPo cell |
| USB-C | USB-C receptacle | — | — | Standard SMD | Charging + data |
| SWD | STDC14 header | 14 | 1.27mm | 2×7 SMD/THT | STLINK-V3MINIE debug |
| Display | ZIF FPC | 10 | 0.5mm | Hirose FH12-10S-0.5SH | LS027B7DH01 |
| SCL3300 FFC | ZIF FFC | 6 | 1.0mm | Standard ZIF | SCL3300 daughter board |
| PCAP04 #1 FFC | ZIF FFC | 6 | 1.0mm | Standard ZIF | PCAP04 board 1 |
| PCAP04 #2 FFC | ZIF FFC | 6 | 1.0mm | Standard ZIF | PCAP04 board 2 |
| Expansion | 100mil header | 7 | 2.54mm | Through-hole, DNP | Future extension |

All three 6-pin FFC connectors use 1.0 mm pitch and identical physical parts.

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

| # | Designator | Description | Part Number | Package | JLCPCB # | Qty |
|---|---|---|---|---|---|---|
| 1 | U1 | Microcontroller STM32G0B1RET6 | STM32G0B1RET6 | LQFP64-GP | C2829307 | 1 |
| 2 | U2 | BLE module RN4871 | RN4871-I/RM128 | Castellated | C633941 | 1 |
| 3 | U3 | LiPo charger | TP4056 | SOP-8 | C382139 | 1 |
| 4 | U4 | Cell protection IC | DW01A | SOT-23-6 | C85680 | 1 |
| 5 | Q1, Q2 | Protection FETs | FS8205A | TSSOP-8 | C14212 | 2 |
| 6 | Q3 | Reverse polarity MOSFET | DMG2305UX-13 | SOT-23 | C144153 | 1 |
| 7 | U5 | 3.3V LDO — main rail | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 1 |
| 7B | U5B | 3.3V_DBOARD LDO — daughter boards | LP5907MFX-3.3/NOPB | SOT-23-5 | C80670 | 1 |
| 8 | U6 | 5V charge pump | SD6210A | SOT-23-6 | C250809 | 1 |
| 9 | U7 | Logic level shifter | SN74AHCT244DBR | SSOP-20 | C2868870 | 1 |
| 10 | U8 | Schmitt trigger inverter | SN74HC14PWR | TSSOP-14 | C6821 | 1 |
| 11 | U9 | EEPROM 32KB | 24LC256-I/ST | TSSOP-8 | C87823 | 1 |
| 12 | U10 | Temperature sensor | LM35 | SOT-23 | C9900081740 | 1 |
| 13 | Y1 | Crystal 8MHz | X50328MSB2GI | SMD-5032 | C115962 | 1 |
| 14 | J1 | Battery connector | JST B2B-PH-K | Through-hole | — | 1 |
| 15 | J2 | USB-C connector | TYPE-C-31-M-12 | USB-C SMD right-angle | C165948 | 1 |
| 16 | J3 | SWD debug header | Samtec FTSH-107-01-L-DV-K | SMD 14-pin 2×7 1.27mm | C5307809 | 1 |
| 17 | J4 | Display ZIF 10-pin | FH12-10S-0.5SH | SMD ZIF | — | 1 |
| 18 | J5–J7 | FFC ZIF 6-pin ×3 | 6-pin 1.0mm ZIF | SMD ZIF | TBD | 3 |
| 19 | ENC1, ENC2 | Rotary encoder with switch | Bourns PEC11R-4215F-S0024 | SMD | C143790 | 2 |
| 20 | LED1 | Power LED green | 0603 green LED | 0603 | — | 1 |
| 21 | LED2 | Status LED blue | 0603 blue LED | 0603 | — | 1 |
| 22 | DISP1 | Sharp Memory LCD 2.7" | LS027B7DH01 | FPC panel | C17492463 | 1 |
| 23 | BZ1 | Passive piezo transducer | CPT-9019A-SMT-TR | SMD 9×9mm | C20181991 | 1 |
| 24 | J8 | Expansion header 7-pin, DNP | 2.54mm through-hole | Through-hole | — | 1 |
| — | Various | Resistors 0603 | Various values | 0603 | — | ~30 |
| — | Various | Capacitors 0603/0805 | 100nF, 1µF (0603); 4.7µF, 10µF (0805/1206) | 0603/0805 | — | ~40 |

**Removed from BOM vs. previous revision:** W25Q80DV SPI Flash (U9 — replaced by STM32 ROM DFU bootloader).

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

1. Check BOOT0 (PA14) state: if HIGH → STM32 ROM DFU bootloader handles firmware update, enumerates USB DFU
2. Normal boot (BOOT0 LOW): STM32 jumps to user application at `0x08000000`
3. Firmware initialises all peripherals, starts main loop

### 18.2 Main Tasks

| Task | Rate | Notes |
|---|---|---|
| SCL3300 read | 10 Hz | SPI2, Mode 4 |
| PCAP04 read | 2–10 Hz | I2C, both devices |
| Sensor fusion | 10 Hz | Complementary filter: pendulum < 0.5Hz, MEMS > 0.5Hz |
| BLE notify | On measurement | Send via RN4871 UART |
| Display update | 10 Hz | Redraw changed regions only |
| VCOM toggle | 30 Hz | TIM3_CH1 hardware or timer ISR |
| Vbat ADC | 1 Hz | Software cutoff at 3.6V |
| Temperature ADC | 0.1 Hz | LM35 via ADC |
| USB service | As needed | HID + MSD |
| Encoder service | IOC interrupt | Debounced via 74HC14 |

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
| ~~FFC pitch~~ | ~~Confirmed: 1.0 mm pitch~~ | ~~Resolved~~ |
| ~~Crystal load caps~~ | ~~Calculated: 33 pF (CL=20 pF, C_stray≈3 pF)~~ | ~~Resolved~~ |
| ~~STM32 JLCPCB part number~~ | ~~C2829307~~ | ~~Resolved~~ |
| J3 SWD connector | Samtec FTSH-107-01-L-DV-K (C5307809) — selected, update schematic | Medium — add to schematic |
| PCAP04 I2C address | Verify exact I2C addresses from PCAP04 datasheet | Medium |
| LiPo cell dimensions | Select cell fitting enclosure, confirm JST-PH polarity | Medium |
| ZIF connector selection | Confirm exact ZIF parts for 6-pin FFC connectors | Medium |
| Custom BLE UUIDs | Define 128-bit UUIDs for measurement and command characteristics | Medium |
| PCB dimensions | Define main board outline matching enclosure | Medium |
| ~~Rotary encoder selection~~ | ~~Choose specific encoder part~~ | ~~Resolved: Bourns PEC11R-4215F-S0024 (C143790)~~ |
| ~~USB-C connector selection~~ | ~~Confirm USB-C part~~ | ~~Resolved: TYPE-C-31-M-12 (C165948), 16-pin SMD right-angle, 5A, 10,000 cycles~~ |
| 5V rail validation | Verify SD6210A output with LS027B7DH01 load at 3.6V input | Low |
| SCL3300 daughter board | Design second PCB (out of scope for this document) | Low |
| TIM3_CH1 VCOM toggle | Decide: hardware TIM3_CH1 (PA6 AF1) vs. simple timer ISR GPIO | Low |
| STM32 Eagle library | Download STM32G0B1RET6 LQFP64 library from Ultra Librarian | Medium — needed for Fusion 360 |

---

*End of specification*
