# STM32G0B1RET6 Pin Assignment

**Package:** LQFP64-GP (10×10 mm, 0.5 mm pitch)  
**Datasheet:** DS13560 Rev 6, Figure 8 + Table 12  
**Reference:** spec.md Section 4

---

## 1. Complete Pin Assignment Table

| Pin | Datasheet Pin Name | Signal | Dir | Function | Notes |
|-----|-------------------|--------|-----|----------|-------|
| **Side 1 (pins 1–16, left, top→bottom)** | | | | | |
| 1 | PC11 | *spare* | — | GPIO | |
| 2 | PC12 | *spare* | — | GPIO | |
| 3 | PC13 | *spare* | — | GPIO | 3 mA max; output speed ≤ 2 MHz |
| 4 | PC14-OSC32_IN | *spare* | — | GPIO / LSE | LSE crystal capable |
| 5 | PC15-OSC32_OUT | *spare* | — | GPIO / LSE | LSE crystal capable |
| 6 | VBAT | VBAT | Pwr | RTC supply | Tie to +3V3. 100 nF to GND. |
| 7 | VREF+ | VREF+ | Pwr | ADC reference | +3V3 + 1 µF + 10 nF to GND. |
| 8 | VDD/VDDA | +3V3 | Pwr | Power + analog supply | 2× 100 nF + 1× 4.7 µF decoupling. |
| 9 | VSS/VSSA | GND | Pwr | Ground + analog GND | |
| 10 | PF0-OSC_IN | OSC_IN | In | HSE crystal input | X50328MSB2GI 8 MHz. |
| 11 | PF1-OSC_OUT | OSC_OUT | Out | HSE crystal output | Load caps on both pins. |
| 12 | PF2-NRST | NRST | In | Reset | 10 k pull-up to +3V3, 100 nF to GND. Active low. |
| 13 | PC0 | LDO_EN | Out | GPIO | LP5907 enable, active high. |
| 14 | PC1 | LED_PWR | Out | GPIO | Power LED (green), via 330 Ω. |
| 15 | PC2 | LED_STS | Out | GPIO | Status LED (blue), via 330 Ω. |
| 16 | PC3 | *spare* | — | GPIO | |
| **Side 2 (pins 17–32, bottom, left→right)** | | | | | |
| 17 | PA0 | ENC1_A | In | GPIO, EXTI0 | Encoder 1 ch A. Via 74HC14. |
| 18 | PA1 | ENC1_B | In | GPIO, EXTI1 | Encoder 1 ch B. Via 74HC14. |
| 19 | PA2 | ENC1_SW | In | GPIO, EXTI2 | Encoder 1 push switch. Via 74HC14. |
| 20 | PA3 | ENC2_A | In | GPIO, EXTI3 | Encoder 2 ch A. Via 74HC14. |
| 21 | PA4 | DISP_CS | Out | GPIO | Display chip select, active HIGH. |
| 22 | PA5 | DISP_SCK | Out | SPI1_SCK, AF0 | Display SPI clock. |
| 23 | PA6 | DISP_VCOM | Out | TIM3_CH1 AF1 or GPIO | VCOM toggle, ~30 Hz. |
| 24 | PA7 | DISP_MOSI | Out | SPI1_MOSI, AF0 | Display SPI data. Write-only, no MISO. |
| 25 | PC4 | ENC2_B | In | GPIO, EXTI4 | Encoder 2 ch B. Via 74HC14. |
| 26 | PC5 | ENC2_SW | In | GPIO, EXTI5 | Encoder 2 push switch. Via 74HC14. |
| 27 | PB0 | VBAT_SENSE | In | ADC_IN8 | Battery voltage via resistor divider. |
| 28 | PB1 | TEMP_SENSE | In | ADC_IN9 | LM35 temperature. Via 100 Ω + 10 nF LP filter. |
| 29 | PB2 | *spare* | — | GPIO | |
| 30 | PB10 | I2C2_SCL | Out | I2C2 SCL, AF6 | 4.7 k pull-up. PCAP04 #2. |
| 31 | PB11 | I2C2_SDA | I/O | I2C2 SDA, AF6 | 4.7 k pull-up. |
| 32 | PB12 | SCL_CS | Out | GPIO | SCL3300 chip select, active low. |
| **Side 3 (pins 33–48, right, bottom→top)** | | | | | |
| 33 | PB13 | SPI2_SCK | Out | SPI2_SCK, AF0 | SCL3300 SPI clock. |
| 34 | PB14 | SPI2_MISO | In | SPI2_MISO, AF0 | SCL3300 data out. |
| 35 | PB15 | SPI2_MOSI | Out | SPI2_MOSI, AF0 | SCL3300 data in. |
| 36 | PA8 | DISP_ON | Out | GPIO | Display on/off. High = on. |
| 37 | PA9 | CHG_SENSE | In | GPIO | TP4056 CHRG pin. Low = charging. |
| 38 | PC6 | PCAP1_INT | In | GPIO, EXTI6 | PCAP04 #1 interrupt, active low. |
| 39 | PC7 | PCAP2_INT | In | GPIO, EXTI7 | PCAP04 #2 interrupt, active low. |
| 40 | PD8 | *spare* | — | GPIO | |
| 41 | PD9 | *spare* | — | GPIO | |
| 42 | PA10 | VBUS_SENSE | In | GPIO | USB VBUS cable detect (optional). |
| 43 | PA11 [PA9] | USB_DM | I/O | USB D− (fixed) | 22 Ω series resistor. |
| 44 | PA12 [PA10] | USB_DP | I/O | USB D+ (fixed) | 22 Ω series resistor. |
| 45 | PA13 | SWDIO | I/O | SWD data (fixed AF) | Internal pull-up. To J3 STDC14. |
| 46 | PA14-BOOT0 | SWCLK | In | SWD clock / BOOT0 (fixed AF) | Internal pull-down + R_BOOT0 10 k to GND. |
| 47 | PA15 | BLE_RST | Out | GPIO | RN4871 reset, active low. 100 Ω series. |
| 48 | PC8 | BLE_STATUS | In | GPIO | RN4871 status / RX_IND. |
| **Side 4 (pins 49–64, top, right→left)** | | | | | |
| 49 | PC9 | PCAP1_RST | Out | GPIO | PCAP04 #1 reset, active low. |
| 50 | PD0 | PCAP2_RST | Out | GPIO | PCAP04 #2 reset, active low. |
| 51 | PD1 | *spare* | — | GPIO | |
| 52 | PD2 | *spare* | — | GPIO | |
| 53 | PD3 | *spare* | — | GPIO | |
| 54 | PD4 | *spare* | — | GPIO | |
| 55 | PD5 | *spare* | — | GPIO | |
| 56 | PD6 | *spare* | — | GPIO | |
| 57 | PB3 | BUZZER | Out | TIM1_CH2, AF1 | Piezo buzzer PWM, 4 kHz. |
| 58 | PB4 | *spare* | — | GPIO | |
| 59 | PB5 | *spare* | — | GPIO | |
| 60 | PB6 | BLE_TX | Out | USART1_TX, AF0 | STM32 TX → RN4871 RX. |
| 61 | PB7 | BLE_RX | In | USART1_RX, AF0 | RN4871 TX → STM32 RX. |
| 62 | PB8 | I2C1_SCL | Out | I2C1 SCL, AF6 | 4.7 k pull-up. PCAP04 #1 + EEPROM. |
| 63 | PB9 | I2C1_SDA | I/O | I2C1 SDA, AF6 | 4.7 k pull-up. |
| 64 | PC10 | *spare* | — | GPIO | |

---

## 2. Alternate Function (AF) Configuration Summary

### AF Output Registers (GPIOx_AFRL / GPIOx_AFRH)

| Port | Pin | AFR Reg | AF# | Peripheral | Signal |
|------|-----|---------|-----|------------|--------|
| GPIOA | PA5 | AFRL[23:20] | AF0 | SPI1_SCK | DISP_SCK |
| GPIOA | PA6 | AFRL[27:24] | AF1 | TIM3_CH1 | DISP_VCOM (optional hardware toggle) |
| GPIOA | PA7 | AFRL[31:28] | AF0 | SPI1_MOSI | DISP_MOSI |
| GPIOB | PB3 | AFRL[15:12] | AF1 | TIM1_CH2 | BUZZER |
| GPIOB | PB6 | AFRL[27:24] | AF0 | USART1_TX | BLE_TX |
| GPIOB | PB7 | AFRL[31:28] | AF0 | USART1_RX | BLE_RX |
| GPIOB | PB8 | AFRH[3:0] | AF6 | I2C1_SCL | I2C1_SCL |
| GPIOB | PB9 | AFRH[7:4] | AF6 | I2C1_SDA | I2C1_SDA |
| GPIOB | PB10 | AFRH[11:8] | AF6 | I2C2_SCL | I2C2_SCL |
| GPIOB | PB11 | AFRH[15:12] | AF6 | I2C2_SDA | I2C2_SDA |
| GPIOB | PB13 | AFRH[23:20] | AF0 | SPI2_SCK | SPI2_SCK |
| GPIOB | PB14 | AFRH[27:24] | AF0 | SPI2_MISO | SPI2_MISO |
| GPIOB | PB15 | AFRH[31:28] | AF0 | SPI2_MOSI | SPI2_MOSI |

**Note:** PA13 (SWDIO) and PA14 (SWCLK) are automatically in SWD alternate function after reset — no AFR write needed. All GPIOx_MODER bits default to analog input on reset; configure each pin explicitly in firmware init.

---

## 3. EXTI Interrupt Mapping

| Signal | Port Pin | EXTI Line | SYSCFG_EXTICRx | NVIC Vector |
|--------|----------|-----------|----------------|-------------|
| ENC1_A | PA0 | EXTI0 | EXTICR1[3:0] = 0000 (PA) | EXTI0_1_IRQn |
| ENC1_B | PA1 | EXTI1 | EXTICR1[7:4] = 0000 (PA) | EXTI0_1_IRQn |
| ENC1_SW | PA2 | EXTI2 | EXTICR1[11:8] = 0000 (PA) | EXTI2_3_IRQn |
| ENC2_A | PA3 | EXTI3 | EXTICR1[15:12] = 0000 (PA) | EXTI2_3_IRQn |
| ENC2_B | PC4 | EXTI4 | EXTICR2[3:0] = 0010 (PC) | EXTI4_15_IRQn |
| ENC2_SW | PC5 | EXTI5 | EXTICR2[7:4] = 0010 (PC) | EXTI4_15_IRQn |
| PCAP1_INT | PC6 | EXTI6 | EXTICR2[11:8] = 0010 (PC) | EXTI4_15_IRQn |
| PCAP2_INT | PC7 | EXTI7 | EXTICR2[15:12] = 0010 (PC) | EXTI4_15_IRQn |

**EXTI conflict check:** Each EXTI line maps to exactly one port. All 8 EXTI users above are on different line numbers — no conflicts. Encoders 1–4 use port A; encoders 5–6 and both PCAP INTs use port C on different lines.

---

## 4. Peripheral Summary

| Peripheral | Pins Used | Notes |
|------------|-----------|-------|
| SPI1 (Display) | SCK=PA5(22), MOSI=PA7(24) | Write-only, no MISO. AF0. |
| SPI1 GPIO (Display ctrl) | CS=PA4(21), VCOM=PA6(23), ON=PA8(36) | GPIO outputs |
| SPI2 (SCL3300) | SCK=PB13(33), MISO=PB14(34), MOSI=PB15(35) | AF0 |
| SPI2 GPIO (SCL3300 CS) | CS=PB12(32) | Active low |
| I2C1 (PCAP04 #1 + EEPROM) | SCL=PB8(62), SDA=PB9(63) | AF6, 4.7 k pull-ups |
| I2C2 (PCAP04 #2) | SCL=PB10(30), SDA=PB11(31) | AF6, 4.7 k pull-ups |
| USART1 (BLE RN4871) | TX=PB6(60), RX=PB7(61) | AF0, 115200 baud 8N1 |
| USB FS | D−=PA11(43), D+=PA12(44) | Fixed. 22 Ω series. HSI48+CRS for USB clock. |
| TIM1_CH2 (Buzzer PWM) | PB3(57) | AF1, 4 kHz |
| ADC (Vbat, LM35) | PB0(27)=IN8, PB1(28)=IN9 | VREF+ = pin 7 |
| SWD | SWDIO=PA13(45), SWCLK=PA14(46) | Fixed AF. STDC14 connector J3. |
| HSE (Crystal) | OSC_IN=PF0(10), OSC_OUT=PF1(11) | 8 MHz → PLL → 64 MHz SYSCLK |
| NRST | PF2(12) | Reset |

---

## 5. Pin Count

| Category | Count |
|----------|-------|
| Power / Ground (VDD, VSS, VBAT, VREF+) | 4 |
| Crystal (OSC_IN, OSC_OUT, NRST) | 3 |
| SWD (SWDIO, SWCLK) | 2 |
| USB D+/D− | 2 |
| SPI1 bus (Display) | 2 |
| SPI1 GPIO (CS, VCOM, ON) | 3 |
| SPI2 bus (SCL3300) | 3 |
| SPI2 GPIO (SCL3300 CS) | 1 |
| I2C1 bus | 2 |
| I2C2 bus | 2 |
| I2C GPIO (PCAP INT ×2, RST ×2) | 4 |
| USART1 (BLE bus) | 2 |
| USART1 GPIO (BLE RST, STATUS) | 2 |
| ADC (Vbat, Temp) | 2 |
| TIM1_CH2 (Buzzer) | 1 |
| Encoders (6 lines) | 6 |
| LEDs (PWR, STS) | 2 |
| Power management (CHG_SENSE, LDO_EN) | 2 |
| VBUS_SENSE | 1 |
| **Spare** | **18** |
| **Total** | **64** |

---

## 6. Spare Pins

| Pin | Name | Capabilities |
|-----|------|-------------|
| 1 | PC11 | GPIO, FT |
| 2 | PC12 | GPIO, FT |
| 3 | PC13 | GPIO, FT (3 mA / 2 MHz limit) |
| 4 | PC14 | GPIO, LSE |
| 5 | PC15 | GPIO, LSE |
| 16 | PC3 | GPIO, FT |
| 29 | PB2 | GPIO, FT |
| 40 | PD8 | GPIO, FT |
| 41 | PD9 | GPIO, FT |
| 51 | PD1 | GPIO, FT |
| 52 | PD2 | GPIO, FT |
| 53 | PD3 | GPIO, FT |
| 54 | PD4 | GPIO, FT |
| 55 | PD5 | GPIO, FT |
| 56 | PD6 | GPIO, FT |
| 58 | PB4 | GPIO, FT |
| 59 | PB5 | GPIO, FT |
| 64 | PC10 | GPIO, FT |

---

## 7. Clock Configuration

| Clock | Source | Configuration | Result |
|-------|--------|---------------|--------|
| SYSCLK | HSE + PLL | HSE=8 MHz, M=1, N=16, R=2 | 64 MHz |
| USB clock | HSI48 + CRS | CRS locked to USB SOF packets | 48 MHz |
| Peripheral clocks | SYSCLK via AHB/APB prescalers | Default: all = SYSCLK | 64 MHz |

HSI48 oscillator is only needed for USB and is started automatically by the USB peripheral. The external crystal is used exclusively for SYSCLK/peripherals.

**PLL register values:**  
`RCC_PLLCFGR: PLLSRC=HSE, PLLM=1, PLLN=16, PLLR=2`  
`→ VCO = 8 × 16 = 128 MHz; SYSCLK = 128 / 2 = 64 MHz`

---

## 8. BOOT0 / DFU Entry

PA14 doubles as BOOT0. To enter the STM32 ROM DFU bootloader:
- Pull BOOT0 HIGH at reset (STLINK-V3MINIE can do this via JTAG TRST/BOOT pin)
- Or activate via firmware jump to DFU entry address `0x1FFF0000`

**Normal operation:** R_BOOT0 (10 k) pulls PA14 LOW → boots from flash.  
**DFU mode:** Pull PA14 HIGH before / during reset → STM32 ROM DFU activates, enumerates as USB DFU device.

During SWD programming: STLINK drives SWCLK (PA14) normally; the 10 k pull-down has negligible effect on SWCLK signal integrity.

---

## 9. Design Notes

1. **No VCAP pin**: STM32G0 core voltage regulator is fully integrated. No external 10 µF filter capacitor required (unlike PIC32MX470).

2. **Single VDD/VDDA pin (pin 8)**: The LQFP64-GP variant combines digital and analog power on one pin. Use at least 2× 100 nF (placed directly at pin 8) plus 1× 4.7 µF bulk capacitor.

3. **VREF+ (pin 7)**: ADC reference. Connect to +3V3 via 1 µF + 10 NF decoupling. Keep PCB trace short; run close to VSS/VSSA (pin 9) for minimal inductance.

4. **VBAT (pin 6)**: RTC domain supply. Since RTC is not used, connect directly to +3V3 with 100 nF bypass cap. Do not leave floating.

5. **SPI1 routing**: PA4–PA8 are consecutive on side 2/3 (pins 21–24, then 36). Display signals route to 74AHCT244 level shifter, then to 10-pin FPC connector J4.

6. **SPI2 routing**: PB12–PB15 (pins 32–35) are consecutive at the side 2/3 junction — excellent for short trace routing to FFC connector J5 (SCL3300).

7. **I2C clustering**: I2C1 (PB8/PB9, pins 62/63) and I2C2 (PB10/PB11, pins 30/31) are all on Port B. PCAP interrupts (PC6/PC7, pins 38/39) and PCAP resets (PC9/PD0, pins 49/50) are on the adjacent side 3/4 area — good for routing to FFC connectors J6 and J7.

8. **BLE clustering**: USART1 TX/RX (PB6/PB7, pins 60/61), BLE_RST (PA15, pin 47), and BLE_STATUS (PC8, pin 48) are all in the side 3/4 corner. Place RN4871 module at board edge near these pins.

9. **Encoder grouping**: PA0–PA3 (pins 17–20) and PC4/PC5 (pins 25/26) cover all 6 encoder inputs on adjacent positions of side 2. Place 74HC14 between encoder connectors and these pins.

10. **ANSEL default**: On reset, all GPIO pins default to analog mode. Firmware must configure MODER registers for all GPIO and AF pins before use. The HAL GPIO init functions handle this when called correctly.

11. **BOOT0 pull-down**: R_BOOT0 (10 k) on PA14 ensures normal boot from flash. This resistor is always present and the STLINK overrides it during programming without issue.

12. **USB differential pair**: Route PA11/PA12 (pins 43/44) as a matched-length differential pair, 90 Ω differential impedance, no vias. Keep away from SPI/I2C signals. 22 Ω series resistors placed within 10 mm of MCU pins.
