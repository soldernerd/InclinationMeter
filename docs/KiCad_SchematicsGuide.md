# KiCad Schematic Best Practices — Reference Guide

**Purpose:** Reference for programmatic generation of clean, professional KiCad schematics.  
**Target:** KiCad 10 (.kicad_sch S-expression format, version 20250114)

---

## 1. Grid and Spacing

| Parameter | Value (mil) | Value (mm) | Usage |
|-----------|-------------|------------|-------|
| Primary grid | 50 | 1.27 | All pins, wires, symbol placement |
| Secondary grid | 25 | 0.635 | Fine text positioning only |
| Never smaller than | 25 | 0.635 | Pins/wires MUST be on 50-mil grid |

- **All pin endpoints and wire endpoints must land on 1.27 mm grid.** KiCad will not detect connections if endpoints are off-grid.
- Minimum clearance between symbol bodies: 5.08 mm (200 mil).
- Recommended spacing between adjacent components: 7.62–10.16 mm (300–400 mil).
- Place components on multiples of 2.54 mm (100 mil) for visual alignment.

---

## 2. Signal Flow Conventions

### Left-to-Right
- **Inputs on the left, outputs on the right.** This is the single most important readability rule.
- Signal flows left → right, matching natural reading direction.
- Feedback paths (power supply feedback, etc.) flow right → left to distinguish from forward paths.

### Vertical Power Convention
- **Higher voltages at the top, ground at the bottom.**
- VCC/VDD/+3V3 power symbols point upward (↑).
- GND power symbols point downward (↓).

### Cross-Sheet Flow
- Place inter-sheet labels at the sheet edges: inputs on the left edge, outputs on the right edge.
- Maintain consistent signal direction across all pages.

---

## 3. Symbol Pin Placement (KLC Rules)

| Pin Type | Position on Symbol |
|----------|-------------------|
| Positive power (VCC, VDD, VIN) | Top |
| Ground / Negative power (GND, VSS) | Bottom |
| Input / Control / Logic (EN, RST) | Left |
| Output / Driver (Q, OUT) | Right |
| Bidirectional (SDA, USB D±) | Left or Right (context-dependent) |

- **Never** arrange IC pins in physical package order. Group by function.
- Active-low signals: use overbar notation or `~{SIGNAL}` syntax.
- Pin names use 1.27 mm (50 mil) text.

---

## 4. Wire Routing Rules

1. **No four-way junctions.** Use T-junctions only. Offset one wire if four would meet.
2. **Junction dots** required wherever 3+ wire endpoints meet at one point.
3. **Orthogonal routing only** — horizontal and vertical wires. No diagonals.
4. Exit at least one grid point (1.27 mm) straight from a pin before changing direction.
5. **Short wires + net labels** preferred over long wires crossing the sheet.
6. Minimize crossings by rearranging components.
7. Use buses for grouped multi-bit signals: `DATA[7:0]`, `GPIO[0:3]`.

---

## 5. Label Types and Usage

| Label Type | Scope | When to Use |
|------------|-------|-------------|
| Net label (local) | Single sheet only | Most intra-sheet connections |
| Global label | All sheets | Power rails, shared clocks, signals spanning entire design |
| Hierarchical label | Parent ↔ child sheet | Explicit sub-sheet interfaces (preferred for hierarchy) |
| Power symbol | All sheets (implicit global) | VCC, GND, +3V3, +5V — use instead of wiring power |

- **Use global labels sparingly.** Overuse defeats hierarchical organization.
- For a flat multi-page design (our case), global labels are appropriate for inter-sheet signals.
- **Net naming:** UPPERCASE, descriptive: `SPI1_MOSI`, `I2C_SDA`, `VBAT_SENSE`.
- Active-low: consistent suffix `_N` or overbar `~{RESET}`.

---

## 6. Power and Decoupling

### Power Symbols
- Use KiCad power symbols (`power:GND`, `power:+3V3`, etc.) — they create implicit global nets.
- Do NOT draw long wires for power distribution. Use power symbols everywhere needed.
- Use distinct symbols for different voltage domains if needed.

### Decoupling Capacitor Placement (Schematic)
- Place decoupling caps **visually adjacent** to the IC they serve, not in a separate "cap farm."
- Show the connection: `+3V3` symbol above → wire → cap pin 1 → cap pin 2 → wire → `GND` below.
- Label with value (100nF, 4.7µF) and note which IC pin they serve.

### STM32 Decoupling (this project)
| Cap | Value | IC Pin | Size |
|-----|-------|--------|------|
| C_VDD1, C_VDD2 | 100nF | VDD/VDDA (pin 8) | 0603 |
| C_VDD_BULK | 4.7µF | VDD/VDDA (pin 8) | 0805 |
| C_VREF1 | 1µF | VREF+ (pin 7) | 0603 |
| C_VREF2 | 10nF NP0 | VREF+ (pin 7) | 0603 |
| C_VBAT | 100nF | VBAT (pin 6) | 0603 |

---

## 7. Component Grouping

### Functional Blocks
Divide the schematic into logical blocks:
- Power supply / regulation
- MCU core (crystal, reset, decoupling, boot)
- Communication interfaces (SPI, I2C, UART, USB)
- Sensors / analog inputs
- Output drivers / actuators
- Connectors

### Visual Separation
- Use dashed rectangles (`(polyline ... (stroke (type dash)))`) to delineate blocks.
- Add a bold title text (2.54 mm font) at the top-left of each block.
- Keep 5–10 mm margin inside the rectangle.

---

## 8. Hierarchical Design

### Our Hierarchy (7 sheets)
| Page | Sheet | Content |
|------|-------|---------|
| 1 | Root | System block diagram with sub-sheet references |
| 2 | Power | Battery, charger, protection, LDO, charge pump |
| 3 | MCU | STM32G0B1 + crystal + decoupling + reset + boot |
| 4 | Display | 74AHCT244 level shifter + Sharp LCD connector |
| 5 | BLE | RN4871 module + decoupling |
| 6 | Connectors | USB-C, SWD, FFC daughter boards, expansion |
| 7 | UI | Encoders, 74HC14, LEDs, buzzer, EEPROM, LM35 |

### Connection Strategy
- **Global labels** for inter-sheet signal connections (flat multi-page approach).
- **Power symbols** for all power distribution (implicit global).
- Each sheet is self-contained: all needed power symbols and signal labels present.

---

## 9. Sheet Sizing

| Sheet | Recommended Size | Rationale |
|-------|-----------------|-----------|
| Root | A4 landscape | Overview only, 6 sub-sheet boxes |
| Power | A3 landscape | Many components, complex routing |
| MCU | A3 landscape | Large IC + many connections |
| Display | A4 landscape | Few components |
| BLE | A4 landscape | Few components |
| Connectors | A3 landscape | Multiple connectors + passives |
| UI | A3 landscape | Many small circuits |

- A4 landscape: 297 × 210 mm, usable area ~(25, 25) to (272, 185).
- A3 landscape: 420 × 297 mm, usable area ~(25, 25) to (395, 272).
- Never use sheets larger than A3 — split into multiple sheets instead.

---

## 10. Text and Annotation

| Element | Font Size (mm) | Notes |
|---------|---------------|-------|
| Reference designator (R1, U3) | 1.27 | KLC standard |
| Component value (100nF, 10k) | 1.27 | KLC standard |
| Pin names / numbers | 1.27 | KLC standard |
| Net labels | 1.27 | Match component text |
| Section titles | 2.54 | Bold, at block top-left |
| Notes / annotations | 1.27–1.524 | Smaller to avoid clutter |

- **All text horizontal.** Rotate the component, not the text.
- Reference designator: above or upper-left of symbol.
- Value: below or lower-left of symbol.
- No overlapping text on wires or other components.

---

## 11. Title Block

Every sheet must include:
- Project name: "Precision Electronic Level Instrument"
- Sheet title: functional block name
- Revision: "0.1"
- Date: "2026-04-14"

---

## 12. KiCad Coordinate System

### Symbol definitions (.kicad_sym)
- **Y-axis points UP** (mathematical convention).
- Pin `(at X Y ROT)` is the wire **connection endpoint**.
- Pin extends FROM connection point by `length` in direction `ROT`:
  - 0° = extends RIGHT (connection is on LEFT of symbol body)
  - 90° = extends UP (connection at BOTTOM)
  - 180° = extends LEFT (connection on RIGHT)
  - 270° = extends DOWN (connection at TOP)

### Schematic files (.kicad_sch)
- **Y-axis points DOWN** (screen convention).
- Symbol placement: `(symbol (at SX SY ROT) ...)`.

### Pin Position Formula
When a symbol is placed at (sx, sy) with rotation R, a pin defined at local (px, py):

```
R=0°:   wire_x = sx + px,  wire_y = sy - py
R=90°:  wire_x = sx - py,  wire_y = sy - px
R=180°: wire_x = sx - px,  wire_y = sy + py
R=270°: wire_x = sx + py,  wire_y = sy + px
```

This accounts for the Y-axis flip between symbol coords (Y-up) and schematic coords (Y-down).

---

## 13. Programmatic Generation Strategy

### Approach: Direct S-Expression Generation
- KiCad has **no official Python API for schematics** (only PCB).
- Best approach: generate `.kicad_sch` files directly as text (S-expressions).
- Third-party `kicad-sch-api` library exists but is beta; direct generation is more reliable.

### File Structure (.kicad_sch)
```
(kicad_sch
  (version 20250114)
  (generator "eeschema")
  (generator_version "10.0")
  (uuid "...")
  (paper "A3")
  (title_block ...)
  (lib_symbols
    // Embedded copies of ALL symbol definitions used on this sheet
  )
  // Content: junctions, wires, labels, symbols, sheets
  (wire ...)
  (label ...)
  (global_label ...)
  (symbol ...)        // Component instances
  (sheet ...)         // Sub-sheet references (root only)
  (sheet_instances ...)
  (embedded_fonts no)
)
```

### Key Rules for Generation
1. Every element needs a unique UUID.
2. `lib_symbols` must embed definitions for ALL symbols used on that sheet.
3. Symbol instances reference `lib_id` matching the embedded definition.
4. Power symbols are both lib_symbol definitions AND symbol instances.
5. All coordinates in mm, on 1.27 mm grid.
6. Pin endpoints must EXACTLY match wire endpoints for connections.

### Symbol Loading
- Local libraries: extract from `.kicad_sym` files with `extract_symbol()`.
- Built-in symbols (R, C, LED): define inline in the generator.
- Power symbols (GND, +3V3, +5V): define inline.
- Custom symbols (STM32 functional): define inline with pins grouped by function.

---

## 14. Checklist for Clean Schematics

- [ ] All connections on 1.27 mm grid
- [ ] Signal flow: left → right; power: top → bottom
- [ ] No four-way wire junctions
- [ ] Components grouped by function with visual separators
- [ ] Decoupling caps adjacent to their IC
- [ ] All text horizontal, 1.27 mm standard size
- [ ] Descriptive UPPERCASE net names
- [ ] Power symbols used (not long power wires)
- [ ] All IC pins accounted for (unused tied, NC marked)
- [ ] Title block on every sheet
- [ ] ERC clean (no unconnected pins, no floating nets)

---

## References

- [KiCad Library Conventions (KLC)](https://klc.kicad.org)
- [KiCad Schematic File Format](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/)
- [KiCad Default Values](https://docs.kicad.org/doxygen/default__values_8h.html)
- [Phil's Lab — KiCad STM32 Hardware Design Tutorials](https://www.phils-lab.net/courses)
- [Schemalyzer — 30 Schematic Design Best Practices](https://www.schemalyzer.com/en/blog/schematic-review/best-practices/)
