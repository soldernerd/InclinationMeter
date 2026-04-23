# Inclination Meter

A battery-powered, Bluetooth-enabled precision electronic level instrument for machine tool geometry inspection and granite surface plate qualification.

## Overview

The instrument combines a MEMS 3-axis inclinometer (Murata SCL3300) with a high-resolution pendulum-based capacitive sensor (Sciosense PCAP04), a 2.7" Sharp Memory LCD display, and a Bluetooth Low Energy interface to a companion Windows application. All precision sensing is mechanically coupled directly to a cast iron reference base, isolated from the plastic enclosure.

## Hardware

| Parameter | Value |
|---|---|
| MCU | STM32G0B1RET6 (Cortex-M0+, 64 MHz, 512 KB flash) |
| Display | Sharp LS027B7DH01, 2.7", 400�240 monochrome |
| Connectivity | Bluetooth LE 5.0 (Microchip RN4871) |
| USB | USB-C Full Speed — charging + HID + DFU bootloader |
| Battery | 1S LiPo 1000 mAh, ~20 h runtime |
| Supply | 3.3 V main rail, 5 V display rail |
| MEMS range | �90� |
| Pendulum range | �1 mm/m |
| Pendulum resolution | ~0.001 �m/m |

### Physical Architecture

Three PCBs:
- **Main board** — MCU, power management, display, BLE, user interface
- **SCL3300 daughter board** — 3-axis MEMS inclinometer, mounted to cast iron base
- **PCAP04 daughter boards �2** — capacitive pendulum readout, one per axis

## Repository Structure

```
KiCad/          KiCad 10 schematic and PCB files
docs/           KiCad file format and schematic reference notes
spec.md         Full hardware design specification
Netlist.md      Schematic netlist / connection list
```

## KiCad Library

All symbols and footprints use [sldrnrd_kicad_lib](https://github.com/soldernerd/sldrnrd_kicad_lib). Clone it as a sibling of this repository:

```
EmbeddedSystems/
├── InclinationMeter/   ← this repo
└── sldrnrd_kicad_lib/  ← library repo
```

## Firmware

Developed with STM32CubeIDE. Firmware update via USB DFU bootloader (no external programmer required after initial flash).

## Status

Hardware design in progress — schematic phase.
