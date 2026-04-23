# Tech Stack

## Firmware
- **IDE:** STM32CubeIDE (latest stable)
- **Compiler:** arm-none-eabi-gcc (bundled with STM32CubeIDE)
- **Programmer:** STLINK-V3MINIE

## PCB Design
- **Tool:** KiCad 10.0

## KiCad Library
- Use exclusively the sldrnrd_kicad_lib (github.com/soldernerd/sldrnrd_kicad_lib) for all symbols and footprints
- If a required component is missing from the library, ask for it to be added — do not use any other library
- Datasheets for all components are stored inside this library (`datasheets/` folder). Use them as the single source of truth about each component
- Do not assume anything about a component. If anything is unclear or not specified in the datasheet, ask before proceeding

## Hardware
- See separate spec.md document

## Default components
- Resistors: SMD size R0603, 1% accuracy, 100mW max. Stick to E24 series if possible.
- Ceramic capacitors: SMD size C0603. Use C0805 for 4.7µF and above; C1206 if necessary for high capacitance or voltage rating. No 0402. Use NP0 or X7R whenever sensible. Stick to E12 series if possible (E6 is preferred)

