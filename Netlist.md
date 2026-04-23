# Schematic Netlist / Connection List

**Reference documents:** spec.md, STM32_PinAssignment.md, component datasheets  
**Net naming:** UPPERCASE for power rails, CamelCase for signals

---

## Net Summary — Power Rails

| Net Name | Description | Source |
|----------|-------------|--------|
| VBAT_RAW | Battery + from JST, before reverse polarity protection | JST J1 pin 1 |
| VBAT | Protected battery voltage (~3.0-4.2V) | DMG2305UX drain |
| CELL_NEG | Cell B-, DW01A ground side | JST J1 pin 2 |
| GND | System ground (after FS8205A protection) | FS8205A S2 |
| VUSB | USB 5V from connector | USB-C J2 VBUS |
| +3V3 | 3.3V regulated rail | LP5907 OUT |
| +5V | 5V charge pump output (display only) | SD6210A VOUT |

---

## 1. Power Supply — Battery Input and Protection

### J1 — JST-PH 2-pin Battery Connector

| Pin | Net |
|-----|-----|
| 1 (+) | VBAT_RAW |
| 2 (-) | CELL_NEG |

### Q3 — DMG2305UX (P-MOSFET, Reverse Polarity Protection, SOT-23)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | Gate | net: Q3_GATE | Via R_RPP (100k) to GND |
| 2 | Source | VBAT_RAW | From JST + |
| 3 | Drain | VBAT | Protected battery rail |

### R_RPP — 100k (0603) — Reverse polarity gate pull-down

| Pad | Net |
|-----|-----|
| 1 | Q3_GATE |
| 2 | GND |

### U4 — DW01A (Cell Protection, SOT-23-6)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | OD | net: PROT_OD | Overdischarge gate → FS8205A G1 |
| 2 | CS | net: PROT_CS | Current sense, via R_CS to GND |
| 3 | OC | net: PROT_OC | Overcharge gate → FS8205A G2 |
| 4 | NC | — | No connect |
| 5 | VCC | net: DW01_VCC | Via R_DW (470R) from VBAT |
| 6 | GND | CELL_NEG | Cell B- |

### R_DW — 470R (0603) — DW01A VCC series resistor

| Pad | Net |
|-----|-----|
| 1 | VBAT |
| 2 | DW01_VCC |

### C_DW — 100nF (0603, X7R) — DW01A VCC decoupling

| Pad | Net |
|-----|-----|
| 1 | DW01_VCC |
| 2 | CELL_NEG |

### R_CS — 1k (0603) — DW01A current sense resistor

| Pad | Net |
|-----|-----|
| 1 | PROT_CS |
| 2 | GND |

### Q1 — FS8205A (Dual N-MOSFET, Cell Protection, TSSOP-8)

**Note:** Spec lists SOT-23-6 but datasheet confirms TSSOP-8. Update BOM accordingly.

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | D12 | net: PROT_D | Shared drain (internal node) |
| 2 | S1 | CELL_NEG | Source MOSFET 1 → cell B- |
| 3 | S1 | CELL_NEG | Source MOSFET 1 → cell B- |
| 4 | G1 | PROT_OD | Gate MOSFET 1 ← DW01A OD |
| 5 | G2 | PROT_OC | Gate MOSFET 2 ← DW01A OC |
| 6 | S2 | GND | Source MOSFET 2 → system ground |
| 7 | S2 | GND | Source MOSFET 2 → system ground |
| 8 | D12 | PROT_D | Shared drain (internal node) |

---

## 2. Power Supply — USB-C Charging

### J2 — USB-C Connector (SMD)

| Pin(s) | Name | Net | Notes |
|--------|------|-----|-------|
| A1, A12, B1, B12 | GND | GND | |
| A4, A9, B4, B9 | VBUS | VUSB | USB 5V |
| A5 | CC1 | net: USB_CC1 | 5.1k to GND |
| B5 | CC2 | net: USB_CC2 | 5.1k to GND |
| A6, B6 | D+ | net: USB_DP | To STM32 PA12 (pin 44) via 22R |
| A7, B7 | D- | net: USB_DM | To STM32 PA11 (pin 43) via 22R |
| Shell | Shield | GND | |

### R_CC1 — 5.1k (0603) — CC1 pull-down

| Pad | Net |
|-----|-----|
| 1 | USB_CC1 |
| 2 | GND |

### R_CC2 — 5.1k (0603) — CC2 pull-down

| Pad | Net |
|-----|-----|
| 1 | USB_CC2 |
| 2 | GND |

### R_DP — 22R (0603) — USB D+ series resistor

| Pad | Net |
|-----|-----|
| 1 | USB_DP |
| 2 | net: USB_DP_MCU |

### R_DM — 22R (0603) — USB D- series resistor

| Pad | Net |
|-----|-----|
| 1 | USB_DM |
| 2 | net: USB_DM_MCU |

### U3 — TP4056 (LiPo Charger, SOP-8)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | TEMP | GND | Tied to GND (NTC disabled) |
| 2 | PROG | net: TP_PROG | Via R_PROG to GND |
| 3 | GND | GND | |
| 4 | VCC | VUSB | USB 5V input |
| 5 | BAT | VBAT | Battery positive (protected) |
| 6 | STDBY | — | Not connected (or optional LED) |
| 7 | CHRG | net: CHG_SENSE | Open drain, to STM32 PA9 (pin 37) |
| 8 | CE | VUSB | Chip enable, tied to VCC |

### R_PROG — 2.4k (0603, 1%) — Charge current set (500mA)

| Pad | Net |
|-----|-----|
| 1 | TP_PROG |
| 2 | GND |

### C_VUSB — 10uF (0805 or 1206, X7R) — TP4056 input decoupling

| Pad | Net |
|-----|-----|
| 1 | VUSB |
| 2 | GND |

### C_BAT — 10uF (0805 or 1206, X7R) — TP4056 output / battery decoupling

| Pad | Net |
|-----|-----|
| 1 | VBAT |
| 2 | GND |

---

## 3. Power Supply — 3.3V LDO

### U5 — LP5907MFX-3.3 (3.3V LDO, SOT-23-5)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | OUT | +3V3 | 3.3V output |
| 2 | GND | GND | |
| 3 | EN | net: LDO_EN | From STM32 PC0 (pin 13). Active high. |
| 4 | NC | — | No connect |
| 5 | IN | VBAT | Battery input |

### C_LDO_IN — 1uF (0603, X7R) — LDO input capacitor

| Pad | Net |
|-----|-----|
| 1 | VBAT |
| 2 | GND |

### C_LDO_OUT — 10uF (0805 or 1206, X7R) — LDO output capacitor

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | GND |

---

## 4. Power Supply — 5V Charge Pump (Display)

### U6 — SD6210A (5V Charge Pump, SOT-23-6)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | VOUT | +5V | 5V regulated output |
| 2 | GND | GND | |
| 3 | EN | +3V3 | Tied to 3.3V (always enabled when LDO on) |
| 4 | C- | net: CFLY_N | Flying capacitor negative |
| 5 | VIN | VBAT | Battery input |
| 6 | C+ | net: CFLY_P | Flying capacitor positive |

### C_FLY — 1uF (0603, X7R) — Flying capacitor

| Pad | Net |
|-----|-----|
| 1 | CFLY_P |
| 2 | CFLY_N |

### C_5V_IN — 10uF (0805 or 1206, X7R) — Charge pump input

| Pad | Net |
|-----|-----|
| 1 | VBAT |
| 2 | GND |

### C_5V_OUT — 10uF (0805 or 1206, X7R) — Charge pump output

| Pad | Net |
|-----|-----|
| 1 | +5V |
| 2 | GND |

---

## 5. Power Supply — Battery Voltage Sensing

### R_VBAT1 — 100k (0603, 1%) — Voltage divider high side

| Pad | Net |
|-----|-----|
| 1 | VBAT |
| 2 | net: VBAT_SENSE |

### R_VBAT2 — 390k (0603, 1%) — Voltage divider low side

| Pad | Net |
|-----|-----|
| 1 | VBAT_SENSE |
| 2 | GND |

### C_VBAT_F — 100nF (0603, X7R) — ADC input filter

| Pad | Net |
|-----|-----|
| 1 | VBAT_SENSE |
| 2 | GND |

VBAT_SENSE connects to STM32 PB0 (pin 27, ADC_IN8).

---

## 6. Microcontroller — STM32G0B1RET6 (U1, LQFP64-GP)

### Power Pins

| Pin | Name | Net | Decoupling |
|-----|------|-----|------------|
| 8 | VDD/VDDA | +3V3 | 2× 100nF (0603) + 4.7µF (0805) to GND |
| 9 | VSS/VSSA | GND | |
| 6 | VBAT | +3V3 | 100nF (0603) to GND. Tie to +3V3 (RTC not used). |
| 7 | VREF+ | net: VREF_MCU | 1µF (0603) + 10nF (0603) to GND |

### C_VREF_1 — 1µF (0603, X7R) — VREF+ bulk decoupling

| Pad | Net |
|-----|-----|
| 1 | VREF_MCU |
| 2 | GND |

### C_VREF_2 — 10nF (0603, NP0) — VREF+ HF decoupling

| Pad | Net |
|-----|-----|
| 1 | VREF_MCU |
| 2 | GND |

### R_VREF — 0R (0603) — VREF+ to +3V3 (or ferrite bead if needed)

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | VREF_MCU |

### USB Pins

| Pin | Name | Net |
|-----|------|-----|
| 42 | PA10 | net: VBUS_SENSE | GPIO input, optional VBUS detect |
| 43 | PA11 | USB_DM_MCU | Via 22R from USB-C |
| 44 | PA12 | USB_DP_MCU | Via 22R from USB-C |

### Crystal / Reset Pins

| Pin | Name | Net |
|-----|------|-----|
| 10 | PF0-OSC_IN | net: XTAL1 | To crystal + load cap |
| 11 | PF1-OSC_OUT | net: XTAL2 | To crystal + load cap |
| 12 | PF2-NRST | net: NRST | 10k pull-up to +3V3, 100nF to GND |

### SWD Pins

| Pin | Name | Net |
|-----|------|-----|
| 45 | PA13 | net: SWDIO | Via R_SWDIO (100R) to J3 header |
| 46 | PA14-BOOT0 | net: SWCLK | Via R_SWCLK (100R) to J3 header; R_BOOT0 (10k) to GND |

### SPI1 — Display

| Pin | Name | Net | AF |
|-----|------|-----|----|
| 22 | PA5 | net: DISP_SCK | SPI1_SCK, AF0 |
| 24 | PA7 | net: DISP_MOSI | SPI1_MOSI, AF0 |

### SPI1 — Display GPIO

| Pin | Name | Net |
|-----|------|-----|
| 21 | PA4 | net: DISP_CS |
| 23 | PA6 | net: DISP_VCOM |
| 36 | PA8 | net: DISP_ON |

### SPI2 — SCL3300

| Pin | Name | Net | AF |
|-----|------|-----|----|
| 33 | PB13 | net: SPI2_SCK | SPI2_SCK, AF0 |
| 34 | PB14 | net: SPI2_MISO | SPI2_MISO, AF0 |
| 35 | PB15 | net: SPI2_MOSI | SPI2_MOSI, AF0 |

### SPI2 — Chip Select

| Pin | Name | Net |
|-----|------|-----|
| 32 | PB12 | net: SCL_CS |

### I2C1 — PCAP04 #1 + EEPROM

| Pin | Name | Net | AF |
|-----|------|-----|----|
| 62 | PB8 | net: I2C_SCL | I2C1_SCL, AF6 |
| 63 | PB9 | net: I2C_SDA | I2C1_SDA, AF6 |

### I2C2 — PCAP04 #2

| Pin | Name | Net | AF |
|-----|------|-----|----|
| 30 | PB10 | net: I2C2_SCL | I2C2_SCL, AF6 |
| 31 | PB11 | net: I2C2_SDA | I2C2_SDA, AF6 |

### I2C GPIO — PCAP04 Control

| Pin | Name | Net |
|-----|------|-----|
| 38 | PC6 | net: PCAP1_INT |
| 49 | PC9 | net: PCAP1_RST |
| 39 | PC7 | net: PCAP2_INT |
| 50 | PD0 | net: PCAP2_RST |

### USART1 — BLE (RN4871)

| Pin | Name | Net | AF |
|-----|------|-----|----|
| 60 | PB6 | net: BLE_TX | USART1_TX, AF0 |
| 61 | PB7 | net: BLE_RX | USART1_RX, AF0 |

### BLE Control GPIO

| Pin | Name | Net |
|-----|------|-----|
| 47 | PA15 | net: BLE_RST |
| 48 | PC8 | net: BLE_STATUS |

### ADC Inputs

| Pin | Name | Net |
|-----|------|-----|
| 27 | PB0 | VBAT_SENSE (ADC_IN8) |
| 28 | PB1 | net: TEMP_SENSE (ADC_IN9) |

### Encoder Inputs (via 74HC14)

| Pin | Name | Net |
|-----|------|-----|
| 17 | PA0 | net: ENC1_A |
| 18 | PA1 | net: ENC1_B |
| 19 | PA2 | net: ENC1_SW |
| 20 | PA3 | net: ENC2_A |
| 25 | PC4 | net: ENC2_B |
| 26 | PC5 | net: ENC2_SW |

### Buzzer PWM

| Pin | Name | Net | AF |
|-----|------|-----|----|
| 57 | PB3 | net: BUZZER | TIM1_CH2, AF1 |

### LEDs

| Pin | Name | Net |
|-----|------|-----|
| 14 | PC1 | net: LED_PWR |
| 15 | PC2 | net: LED_STS |

### Power Management

| Pin | Name | Net |
|-----|------|-----|
| 37 | PA9 | net: CHG_SENSE |
| 13 | PC0 | net: LDO_EN |

---

## 7. Crystal — Y1 (X50328MSB2GI, 8 MHz, 5032)

XTAL1 connects to STM32 PF0-OSC_IN (pin 10). XTAL2 connects to STM32 PF1-OSC_OUT (pin 11).

| Pad | Net |
|-----|-----|
| 1 | XTAL1 |
| 2 | XTAL2 |

### C_X1 — 33pF (0603, NP0) — Crystal load capacitor OSC_IN

| Pad | Net |
|-----|-----|
| 1 | XTAL1 |
| 2 | GND |

### C_X2 — 33pF (0603, NP0) — Crystal load capacitor OSC_OUT

| Pad | Net |
|-----|-----|
| 1 | XTAL2 |
| 2 | GND |

---

## 8. SWD Header — J3 (Samtec FTSH-107-01-L-DV-K, SMD, 14-pin 2×7, 1.27mm pitch, keyed)

JLCPCB: C5307809. Compatible with STLINK-V3MINIE. Odd pins on left column, even pins on right.

| Pin | Signal | Net | Notes |
|-----|--------|-----|-------|
| 1 | VCC | +3V3 | Target power sense |
| 2 | SWDIO | net: SWDIO_HDR | Via R_SWDIO from STM32 PA13 (pin 45) |
| 3 | GND | GND | |
| 4 | SWCLK | net: SWCLK_HDR | Via R_SWCLK from STM32 PA14 (pin 46) |
| 5 | GND | GND | |
| 6 | SWO | — | NC — Cortex-M0+ has no SWO |
| 7 | NC | — | No connect |
| 8 | NC | — | No connect |
| 9 | GND | GND | |
| 10 | NRST | net: NRST | STM32 PF2 (pin 12) |
| 11 | NC | — | No connect |
| 12 | NC | — | No connect |
| 13 | GND | GND | |
| 14 | GND | GND | |

### R_SWDIO — 100R (0603) — SWD data series protection

| Pad | Net |
|-----|-----|
| 1 | SWDIO |
| 2 | SWDIO_HDR |

### R_SWCLK — 100R (0603) — SWD clock series protection

| Pad | Net |
|-----|-----|
| 1 | SWCLK |
| 2 | SWCLK_HDR |

### R_BOOT0 — 10k (0603) — BOOT0 pull-down (normal boot from flash)

| Pad | Net |
|-----|-----|
| 1 | SWCLK |
| 2 | GND |

Note: R_BOOT0 pad 1 connects to the SWCLK net (= STM32 PA14). This holds BOOT0 LOW during normal operation. The 100R R_SWCLK in series does not affect BOOT0 level — R_BOOT0 is connected on the STM32 side, before R_SWCLK.

### R_NRST — 10k (0603) — NRST pull-up

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | NRST |

### C_NRST — 100nF (0603, X7R) — NRST noise filter

| Pad | Net |
|-----|-----|
| 1 | NRST |
| 2 | GND |

---

## 9. Display — Sharp LS027B7DH01 via 74AHCT244

### U7 — SN74AHCT244DBR (Level Shifter, SSOP-20)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | 1OE | GND | Always enabled (active low) |
| 2 | 1A1 | DISP_SCK | 3.3V input from STM32 PA5 (pin 22) |
| 3 | 2Y4 | — | Spare output (NC) |
| 4 | 1A2 | DISP_MOSI | 3.3V input from STM32 PA7 (pin 24) |
| 5 | 2Y3 | — | Spare output (NC) |
| 6 | 1A3 | DISP_CS | 3.3V input from STM32 PA4 (pin 21) |
| 7 | 2Y2 | — | Spare output (NC) |
| 8 | 1A4 | DISP_VCOM | 3.3V input from STM32 PA6 (pin 23) |
| 9 | 2Y1 | net: DISP_ON_5V | 5V output → display DISP |
| 10 | GND | GND | |
| 11 | 2A1 | DISP_ON | 3.3V input from STM32 PA8 (pin 36) |
| 12 | 1Y4 | net: DISP_VCOM_5V | 5V output → display EXTCOMIN |
| 13 | 2A2 | — | Spare input (tie to GND) |
| 14 | 1Y3 | net: DISP_CS_5V | 5V output → display SCS |
| 15 | 2A3 | — | Spare input (tie to GND) |
| 16 | 1Y2 | net: DISP_MOSI_5V | 5V output → display SI |
| 17 | 2A4 | — | Spare input (tie to GND) |
| 18 | 1Y1 | net: DISP_SCK_5V | 5V output → display SCLK |
| 19 | 2OE | GND | Always enabled (active low) |
| 20 | VCC | +5V | 5V supply |

### C_244 — 100nF (0603, X7R) — 74AHCT244 decoupling

| Pad | Net |
|-----|-----|
| 1 | +5V |
| 2 | GND |

### J4 — Display FPC Connector (10-pin, 0.5mm ZIF, Hirose FH12-10S-0.5SH)

| Pin | Signal | Net | Notes |
|-----|--------|-----|-------|
| 1 | SCLK | DISP_SCK_5V | SPI clock |
| 2 | SI | DISP_MOSI_5V | SPI data in |
| 3 | SCS | DISP_CS_5V | Chip select (active HIGH) |
| 4 | EXTCOMIN | DISP_VCOM_5V | VCOM inversion signal |
| 5 | DISP | DISP_ON_5V | Display on/off |
| 6 | EXTMODE | +5V | Tied to VDD (external VCOM mode) |
| 7 | VDD | +5V | Digital supply |
| 8 | VSS | GND | Digital ground |
| 9 | VDDA | +5V | Analog supply |
| 10 | VSSA | GND | Analog ground |

### C_DISP_VDD — 1uF (0603, X7R) — Display VDD decoupling

| Pad | Net |
|-----|-----|
| 1 | +5V |
| 2 | GND |

### C_DISP_VDDA — 1uF (0603, X7R) — Display VDDA decoupling

| Pad | Net |
|-----|-----|
| 1 | +5V |
| 2 | GND |

---

## 10. Bluetooth — RN4871

### U2 — RN4871-I/RM128 (BLE Module, Castellated)

| Pad | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | GND | GND | |
| 2 | GND | GND | |
| 3 | GND | GND | |
| 4 | VBAT | +3V3 | Module power supply |
| 5 | P2_2 | — | NC (GPIO, unused) |
| 6 | VDD_IO | +3V3 | I/O voltage level |
| 7 | VDD_IO | +3V3 | I/O voltage level |
| 8 | ULPC_O | — | NC (do not connect) |
| 9 | P2_3 | — | NC (GPIO, unused) |
| 10 | BK_IN | net: BLE_BK | Buck input, 10uF cap to GND |
| 11 | P1_1 | BLE_STATUS | Status indication → STM32 PC8 (pin 48) |
| 12 | P1_2 | — | NC (I2C SCL, unused) |
| 13 | P1_3 | — | NC (I2C SDA, unused) |
| 14 | P0_0 | — | NC (CTS, unused) |
| 15 | P1_0 | — | NC (STATUS2, unused) |
| 16 | P3_6 | — | NC (RTS, unused) |
| 17 | P2_0 | +3V3 | System config: HIGH = app mode |
| 18 | P2_4 | — | NC (GPIO, unused) |
| 19 | NC | — | No connect |
| 20 | RST_N | BLE_RST | Active low reset ← STM32 PA15 (pin 47) |
| 21 | UART_RX | BLE_TX | STM32 TX → module RX |
| 22 | UART_TX | BLE_RX | Module TX → STM32 RX |
| 23 | P3_1 | — | NC |
| 24 | P3_2 | — | NC |
| 25 | P3_3 | — | NC |
| 26 | P3_4 | — | NC |
| 27 | P3_5 | — | NC |
| 28 | P0_7 | — | NC |
| 29 | P0_2 | — | NC |
| 30 | GND | GND | |
| 31 | GND | GND | |
| 32 | BT_RF | — | NC (internal antenna on RN4871) |
| 33 | GND | GND | |

### R_BLE_RST — 100R (0603) — BLE reset series resistor

| Pad | Net |
|-----|-----|
| 1 | BLE_RST |
| 2 | net: BLE_RST_MOD |

Note: R_BLE_RST pad 2 connects to U2 pad 20. BLE_RST from STM32 PA15 (pin 47) → R_BLE_RST → U2.RST_N.

### C_BLE — 100nF (0603, X7R) — RN4871 VBAT decoupling

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | GND |

### C_BLE_BK — 10uF (0805, X7R) — RN4871 buck input capacitor

| Pad | Net |
|-----|-----|
| 1 | BLE_BK |
| 2 | GND |

Note: BLE_BK connects to U2 pad 10 (BK_IN). Refer to RN4871 datasheet for BK_IN connection details — may need to connect to VBAT (pad 4) or have specific wiring. Verify in datasheet Section 2.

---

## 11. SPI Flash — REMOVED

The W25Q80DV SPI flash (previously U9) has been removed. Firmware updates are handled by the STM32G0B1 built-in ROM DFU bootloader over USB. No SPI flash, no FLASH_CS net. The SPI2 bus is now dedicated to the SCL3300 sensor only.

---

## 12. EEPROM — 24LC256

### U10 — 24LC256-I/ST (32KB EEPROM, TSSOP-8)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | A0 | GND | Address bit 0 = 0 |
| 2 | A1 | GND | Address bit 1 = 0 |
| 3 | A2 | GND | Address bit 2 = 0 → I2C addr 0x50 |
| 4 | VSS | GND | |
| 5 | SDA | I2C_SDA | Shared I2C bus |
| 6 | SCL | I2C_SCL | Shared I2C bus |
| 7 | WP | GND | Write protect disabled |
| 8 | VCC | +3V3 | |

### C_EEPROM — 100nF (0603, X7R) — EEPROM decoupling

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | GND |

---

## 13. I2C Bus Pull-ups

### R_SDA — 4.7k (0603) — I2C1 SDA pull-up

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | I2C_SDA |

### R_SCL — 4.7k (0603) — I2C1 SCL pull-up

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | I2C_SCL |

### R_SDA2 — 4.7k (0603) — I2C2 SDA pull-up

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | I2C2_SDA |

### R_SCL2 — 4.7k (0603) — I2C2 SCL pull-up

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | I2C2_SCL |

---

## 14. FFC Connectors — Daughter Boards

### J5 — SCL3300 FFC (6-pin ZIF, 1.0mm pitch)

| Pin | Signal | Net | Notes |
|-----|--------|-----|-------|
| 1 | GND | GND | |
| 2 | +3.3V | +3V3 | |
| 3 | SCK | SPI2_SCK | SPI2 clock |
| 4 | MOSI | SPI2_MOSI | SPI2 data out |
| 5 | MISO | SPI2_MISO | SPI2 data in |
| 6 | CS | SCL_CS | ← STM32 PB12 (pin 32), active low |

### C_J5 — 100nF (0603, X7R) — SCL3300 connector decoupling

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | GND |

### J6 — PCAP04 #1 FFC (6-pin ZIF, 1.0mm pitch)

| Pin | Signal | Net | Notes |
|-----|--------|-----|-------|
| 1 | SDA | I2C_SDA | Shared I2C bus |
| 2 | SCL | I2C_SCL | Shared I2C bus |
| 3 | GND | GND | |
| 4 | RESET | PCAP1_RST | ← STM32 PC9 (pin 49), active low |
| 5 | +3.3V | +3V3 | |
| 6 | INT | PCAP1_INT | → STM32 PC6 (pin 38), active low |

### J7 — PCAP04 #2 FFC (6-pin ZIF, 1.0mm pitch)

| Pin | Signal | Net | Notes |
|-----|--------|-----|-------|
| 1 | SDA | I2C2_SDA | I2C2 bus (STM32 PB11/pin 31) |
| 2 | SCL | I2C2_SCL | I2C2 bus (STM32 PB10/pin 30) |
| 3 | GND | GND | |
| 4 | RESET | PCAP2_RST | ← STM32 PD0 (pin 50), active low |
| 5 | +3.3V | +3V3 | |
| 6 | INT | PCAP2_INT | → STM32 PC7 (pin 39), active low |

---

## 15. Temperature Sensor — LM35

### U11 — LM35 (SOT-23)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | VS+ | +3V3 | Supply |
| 2 | VOUT | net: LM35_OUT | 10mV/C output |
| 3 | GND | GND | |

### R_TEMP — 100R (0603) — LM35 output series resistor

| Pad | Net |
|-----|-----|
| 1 | LM35_OUT |
| 2 | TEMP_SENSE |

### C_TEMP — 10nF (0603, NP0) — LM35 output LP filter

| Pad | Net |
|-----|-----|
| 1 | TEMP_SENSE |
| 2 | GND |

TEMP_SENSE connects to STM32 PB1 (pin 28, ADC_IN9).

---

## 16. Buzzer

### BZ1 — CPT-9019A-SMT-TR (Passive Piezo Transducer, SMD 9×9mm, Same Sky/CUI, JLCPCB C20181991)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| + | Signal | net: BUZZER | STM32 PB3 (pin 57), TIM1_CH2 AF1, 4 kHz |
| − | GND | GND | |

---

## 17. User Interface — Rotary Encoders + 74HC14

### U8 — SN74HC14PWR (Hex Schmitt Trigger Inverter, TSSOP-14, TI, JLCPCB C6821)

| Pin | Name | Net | Notes |
|-----|------|-----|-------|
| 1 | 1A | net: ENC1_A_RAW | Encoder 1 A, after RC filter |
| 2 | 1Y | ENC1_A | → STM32 PA0 (pin 17, EXTI0, inverted) |
| 3 | 2A | net: ENC1_B_RAW | Encoder 1 B, after RC filter |
| 4 | 2Y | ENC1_B | → STM32 PA1 (pin 18, EXTI1, inverted) |
| 5 | 3A | net: ENC1_SW_RAW | Encoder 1 SW, after RC filter |
| 6 | 3Y | ENC1_SW | → STM32 PA2 (pin 19, EXTI2, inverted) |
| 7 | GND | GND | |
| 8 | 4Y | ENC2_A | → STM32 PA3 (pin 20, EXTI3, inverted) |
| 9 | 4A | net: ENC2_A_RAW | Encoder 2 A, after RC filter |
| 10 | 5Y | ENC2_B | → STM32 PC4 (pin 25, EXTI4, inverted) |
| 11 | 5A | net: ENC2_B_RAW | Encoder 2 B, after RC filter |
| 12 | 6Y | ENC2_SW | → STM32 PC5 (pin 26, EXTI5, inverted) |
| 13 | 6A | net: ENC2_SW_RAW | Encoder 2 SW, after RC filter |
| 14 | VCC | +3V3 | |

### C_HC14 — 100nF (0603, X7R) — 74HC14 decoupling

| Pad | Net |
|-----|-----|
| 1 | +3V3 |
| 2 | GND |

### RC Debounce Filters (x6, one per encoder line)

Each encoder line has: Encoder pin → R (10k, 0603) → junction → C (10nF NP0, 0603) to GND → 74HC14 input

**ENC1_A debounce:**

| Component | Pad 1 | Pad 2 |
|-----------|-------|-------|
| R_E1A (10k) | net: ENC1_A_ENC | ENC1_A_RAW |
| C_E1A (10nF, NP0) | ENC1_A_RAW | GND |

**ENC1_B debounce:**

| Component | Pad 1 | Pad 2 |
|-----------|-------|-------|
| R_E1B (10k) | net: ENC1_B_ENC | ENC1_B_RAW |
| C_E1B (10nF, NP0) | ENC1_B_RAW | GND |

**ENC1_SW debounce:**

| Component | Pad 1 | Pad 2 |
|-----------|-------|-------|
| R_E1S (10k) | net: ENC1_SW_ENC | ENC1_SW_RAW |
| C_E1S (10nF, NP0) | ENC1_SW_RAW | GND |

**ENC2_A debounce:**

| Component | Pad 1 | Pad 2 |
|-----------|-------|-------|
| R_E2A (10k) | net: ENC2_A_ENC | ENC2_A_RAW |
| C_E2A (10nF, NP0) | ENC2_A_RAW | GND |

**ENC2_B debounce:**

| Component | Pad 1 | Pad 2 |
|-----------|-------|-------|
| R_E2B (10k) | net: ENC2_B_ENC | ENC2_B_RAW |
| C_E2B (10nF, NP0) | ENC2_B_RAW | GND |

**ENC2_SW debounce:**

| Component | Pad 1 | Pad 2 |
|-----------|-------|-------|
| R_E2S (10k) | net: ENC2_SW_ENC | ENC2_SW_RAW |
| C_E2S (10nF, NP0) | ENC2_SW_RAW | GND |

### ENC1 — Rotary Encoder 1 (with push switch)

| Terminal | Net | Notes |
|----------|-----|-------|
| A | ENC1_A_ENC | Channel A |
| B | ENC1_B_ENC | Channel B |
| C (common) | GND | Encoder common |
| SW1 | ENC1_SW_ENC | Push switch |
| SW2 | GND | Push switch common |

### ENC2 — Rotary Encoder 2 (with push switch)

| Terminal | Net | Notes |
|----------|-----|-------|
| A | ENC2_A_ENC | Channel A |
| B | ENC2_B_ENC | Channel B |
| C (common) | GND | Encoder common |
| SW1 | ENC2_SW_ENC | Push switch |
| SW2 | GND | Push switch common |

---

## 17. Status LEDs

### LED1 — Power LED (Green, 0603)

| Pad | Net |
|-----|-----|
| Anode | net: LED_PWR_A |
| Cathode | GND |

### R_LED1 — 330R (0603) — Power LED current limit

| Pad | Net |
|-----|-----|
| 1 | LED_PWR |
| 2 | LED_PWR_A |

LED_PWR from STM32 PC1 (pin 14) → R_LED1 → LED1 anode. LED1 cathode → GND.

### LED2 — Status LED (Blue, 0603)

| Pad | Net |
|-----|-----|
| Anode | net: LED_STS_A |
| Cathode | GND |

### R_LED2 — 330R (0603) — Status LED current limit

| Pad | Net |
|-----|-----|
| 1 | LED_STS |
| 2 | LED_STS_A |

LED_STS from STM32 PC2 (pin 15) → R_LED2 → LED2 anode. LED2 cathode → GND.

---

## 18. Expansion Header — J8 (DNP)

7-pin 100mil through-hole header. Do not populate — footprint only. Place at board edge.

### J8 — Expansion Header (7-pin, 2.54mm, DNP)

| Pin | Signal | Net | Notes |
|-----|--------|-----|-------|
| 1 | GND | GND | |
| 2 | +3.3V | +3V3 | |
| 3 | +5V | +5V | |
| 4 | EXP1 | net: EXP1 | Spare STM32 GPIO (assign at layout stage) |
| 5 | EXP2 | net: EXP2 | Spare STM32 GPIO |
| 6 | EXP3 | net: EXP3 | Spare STM32 GPIO |
| 7 | EXP4 | net: EXP4 | Spare STM32 GPIO |

Note: Specific STM32 spare pins (e.g. PD1–PD6, PB4/PB5) to be assigned when finalising PCB layout.

---

## Design Notes

1. **74HC14 inversion**: All encoder signals are inverted by the Schmitt trigger. Firmware must account for this (or swap A/B connections to reverse direction).

2. **GPIO default analog mode**: All STM32 GPIO pins default to analog input mode after reset (MODER = 11). Firmware must explicitly configure MODER, OTYPER, OSPEEDR, and PUPDR for every used pin in peripheral init code. HAL_GPIO_Init() handles this when called correctly.

3. **FS8205A package correction**: Spec listed SOT-23-6 but the part is TSSOP-8 per datasheet. BOM updated accordingly.

4. **SD6210A datasheet**: Download manually from LCSC or JLCPCB (see Datasheets folder note). Verify pinout matches this netlist before PCB layout.

5. **RN4871 BK_IN (pad 10)**: Verify required connection in datasheet. Typically connects to VBAT through the module's internal buck regulator. Add 10 µF cap per datasheet recommendation.

6. **Spare 74AHCT244 inputs**: Pins 13, 15, 17 (2A2, 2A3, 2A4) are unused — tie to GND to prevent floating inputs.

7. **Crystal load caps**: 33 pF NP0 (0603). Crystal CL = 20 pF (datasheet), C_stray ≈ 3 pF → C_load = 2×(20−3) = 34 pF → 33 pF nearest E12. Actual CL ≈ 19.5 pF.

8. **No VCAP net**: STM32G0 has integrated core regulator. The VCAP net and C_VCAP (10 µF) from the PIC32 design are removed.

9. **VREF_MCU net**: STM32 VREF+ (pin 7) drives the ADC reference. Connected to +3V3 via a 0 Ω jumper (R_VREF) with local decoupling. Replace R_VREF with a ferrite bead if ADC noise is an issue in bring-up.

10. **BOOT0 / R_BOOT0**: R_BOOT0 (10 k to GND) connects to the SWCLK net (STM32 PA14, pin 46) on the MCU side, before R_SWCLK. This ensures BOOT0 is held LOW for normal boot. STLINK drives SWCLK through R_SWCLK and is unaffected by R_BOOT0.

11. **SWD connector (J3)**: Samtec FTSH-107-01-L-DV-K — SMD, 14-pin 2×7, 1.27 mm pitch, keyed shroud. JLCPCB C5307809. Compatible with STLINK-V3MINIE ribbon cable (IDC female). Pin 6 (SWO) is left NC — Cortex-M0+ has no ITM trace output. NRST (pin 10) connects to STM32 PF2 (pin 12) for hard reset capability.
