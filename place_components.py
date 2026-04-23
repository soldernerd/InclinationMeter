#!/usr/bin/env python3
"""
PCB Component Placement & Design Rules Script — Precision Electronic Level Instrument.

Uses KiCad's pcbnew Python API to:
  1. Set up design rules (grid, trace widths, clearances, diff pair)
  2. Place all footprints according to layout zones
  3. Draw board outline

Run with KiCad's bundled Python:
  "C:\Program Files\KiCad\10.0\bin\python.exe" place_components.py

Board dimensions: 130 × 35 mm (fits 150×35mm enclosure with margins)
Coordinate origin: top-left of board outline.

Reference designators (from generate_schematic.py output):
  Power:      Q1(DMG2305UX), Q3(FS8205A), U3(TP4056), U4(DW01A),
              U5(LP5907), U6(SD6210A), R1-R5, C1-C6
  MCU:        U1(STM32G0B1RET6), Y1(8MHz crystal), C7-C14
  Display:    U7(SN74AHCT244), J4(FH12-10S FPC), C15-C17
  BLE:        U2(RN4871), C18-C19
  Connectors: J3(FTSH-107 SWD)
  UI:         U8(SN74HC14), U9(24LC256), U11(LM35), D1, D2,
              BZ1(buzzer), R6-R8, C20-C22
"""

import pcbnew
from pathlib import Path

BOARD_PATH = Path(__file__).resolve().parent / "KiCad" / "InclinationMeter.kicad_pcb"

# Board dimensions (mm)
BOARD_W = 130.0
BOARD_H = 35.0
BOARD_ORIGIN_X = 25.0   # offset from KiCad origin
BOARD_ORIGIN_Y = 25.0

# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def mm_to_pos(x_mm, y_mm):
    """Convert board-relative mm coordinates to KiCad internal coords."""
    return pcbnew.VECTOR2I(
        pcbnew.FromMM(BOARD_ORIGIN_X + x_mm),
        pcbnew.FromMM(BOARD_ORIGIN_Y + y_mm)
    )


def place(board, ref, x, y, angle=0):
    """Place a footprint by reference designator."""
    for fp in board.GetFootprints():
        if fp.GetReference() == ref:
            fp.SetPosition(mm_to_pos(x, y))
            fp.SetOrientationDegrees(angle)
            return fp
    print(f"  WARNING: {ref} not found on board")
    return None


def draw_board_outline(board):
    """Draw rectangular board outline on Edge.Cuts layer."""
    x0 = pcbnew.FromMM(BOARD_ORIGIN_X)
    y0 = pcbnew.FromMM(BOARD_ORIGIN_Y)
    x1 = pcbnew.FromMM(BOARD_ORIGIN_X + BOARD_W)
    y1 = pcbnew.FromMM(BOARD_ORIGIN_Y + BOARD_H)

    corners = [
        (x0, y0), (x1, y0), (x1, y1), (x0, y1)
    ]
    for i in range(4):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetStart(pcbnew.VECTOR2I(corners[i][0], corners[i][1]))
        seg.SetEnd(pcbnew.VECTOR2I(corners[(i+1) % 4][0], corners[(i+1) % 4][1]))
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(pcbnew.FromMM(0.1))
        board.Add(seg)


# ═══════════════════════════════════════════════════════════════════════════
# DESIGN RULES
# ═══════════════════════════════════════════════════════════════════════════

def setup_design_rules(board):
    """Configure design rules for JLCPCB 4-layer capability."""
    ds = board.GetDesignSettings()

    # Grid: 0.5 mm (set in KiCad GUI; we set track/clearance rules here)

    # Default net class rules (JLCPCB 4-layer minimums)
    ds.SetCopperLayerCount(4)

    # Default trace width: 0.2mm (good for signals)
    # Min trace width: 0.127mm (5mil, JLCPCB minimum)
    ds.m_TrackMinWidth = pcbnew.FromMM(0.127)

    # Clearance: 0.2mm default (JLCPCB min 0.127mm for inner layers)
    ds.m_MinClearance = pcbnew.FromMM(0.127)

    # Via: 0.6mm diameter / 0.3mm drill (JLCPCB standard)
    ds.m_ViasMinSize = pcbnew.FromMM(0.45)
    ds.m_MinThroughDrill = pcbnew.FromMM(0.2)

    # Board edge clearance: 0.3mm
    ds.m_CopperEdgeClearance = pcbnew.FromMM(0.3)

    # Silkscreen
    ds.m_SilkClearance = pcbnew.FromMM(0.15)

    print("  Design rules configured (4-layer, JLCPCB compatible)")


# ═══════════════════════════════════════════════════════════════════════════
# PLACEMENT LAYOUT
# ═══════════════════════════════════════════════════════════════════════════
#
# Board: 130 × 35 mm, landscape, component side up.
#
# Layout zones (left to right):
#
#  ┌──────────┬──────────┬─────────┬──────────┬──────────┬────────┐
#  │  POWER   │   MCU    │ DISPLAY │   BLE    │   UI     │ CONN   │
#  │ 0-30mm   │ 30-65mm  │ 65-85mm │ 85-110mm │ 85-110mm │110-130 │
#  │          │          │         │  (top)   │ (bottom) │        │
#  └──────────┴──────────┴─────────┴──────────┴──────────┴────────┘
#
# Priorities:
# 1. Crystal close to STM32 OSC pins
# 2. USB D+/D- short, matched length
# 3. RN4871 at board edge, antenna keep-out
# 4. Power section grouped, away from sensitive signals
# 5. 74AHCT244 between STM32 and display connector
# 6. Display connector near display window
# 7. Decoupling caps tight to IC power pins
# 8. LM35 away from heat sources

def place_all(board):
    """Place all components according to layout plan."""

    # ── ZONE 1: Power (x = 0–30 mm) ──

    # Battery input / reverse polarity protection
    place(board, "Q1",  5.0,  10.0)         # DMG2305UX P-FET reverse protection
    place(board, "R1",  5.0,  17.0)         # 100k gate pull-down

    # TP4056 charger
    place(board, "U3", 15.0,  10.0)         # TP4056
    place(board, "R2", 10.0,  17.0)         # 1k PROG resistor
    place(board, "R3", 20.0,  17.0)         # 2.4k resistor
    place(board, "C1", 22.0,  6.0)          # 10uF input cap
    place(board, "C2", 10.0,  6.0)          # 10uF cap (LP5907 input)

    # DW01A + FS8205A cell protection
    place(board, "U4", 10.0,  27.0)         # DW01A
    place(board, "Q3", 18.0,  27.0)         # FS8205A dual MOSFET

    # LP5907 LDO (3.3V)
    place(board, "U5", 28.0,  8.0)          # LP5907
    place(board, "C3", 28.0,  3.0)          # 10uF output cap (close to LDO)

    # SD6210A charge pump (5V for display)
    place(board, "U6", 28.0,  22.0)         # SD6210A
    place(board, "C4", 28.0, 27.0)          # 10uF output cap
    place(board, "C5", 25.0, 17.0)          # 1uF flying cap

    # VBAT sense divider
    place(board, "R4",  5.0,  27.0)         # 100k top
    place(board, "R5",  5.0,  32.0)         # 390k bottom
    place(board, "C6", 10.0,  32.0)         # 100nF filter

    # ── ZONE 2: MCU (x = 32–62 mm) ──
    place(board, "U1", 47.0,  17.5)         # STM32G0B1RET6 (centre of zone)

    # Crystal — close to OSC_IN / OSC_OUT pins (left side of STM32)
    place(board, "Y1", 36.0,  17.5)         # 8 MHz crystal
    place(board, "C13", 34.0,  13.0)        # 33pF load cap 1
    place(board, "C14", 34.0,  22.0)        # 33pF load cap 2

    # STM32 decoupling — close to power pins
    # Must be VERY close to VDD/VSS pins (pins 8,9 on left side)
    place(board, "C7",  42.0,  5.0)         # 100nF VDD
    place(board, "C8",  45.0,  5.0)         # 100nF VDD
    place(board, "C9",  48.0,  5.0)         # 4.7uF VDD bulk
    place(board, "C10", 51.0,  5.0)         # 1uF VREF+
    place(board, "C11", 54.0,  5.0)         # 10nF VREF+ NP0
    place(board, "C12", 57.0,  5.0)         # 100nF VBAT

    # ── ZONE 3: Display interface (x = 63–83 mm) ──
    # 74AHCT244 between STM32 and display connector (priority #5)
    place(board, "U7", 70.0,  17.5)         # SN74AHCT244 level shifter
    place(board, "C15", 70.0,  5.0)         # 100nF decoupling (5V VCC)

    # Display FPC connector at top edge (priority #6)
    place(board, "J4", 78.0,  2.0, 0)       # FH12-10S display FPC
    place(board, "C16", 78.0,  8.0)         # 1uF display VDD
    place(board, "C17", 82.0,  8.0)         # 1uF display VDDA

    # ── ZONE 4: BLE (x = 85–115 mm, top half) ──
    # RN4871 at right side, antenna at board edge (priority #3)
    place(board, "U2", 105.0,  8.0)         # RN4871 BLE module
    place(board, "C18", 98.0,  5.0)         # 100nF decoupling
    place(board, "C19", 95.0,  5.0)         # 10uF bulk

    # ── ZONE 5: UI components (x = 85–115 mm, bottom half) ──
    # 74HC14 Schmitt trigger for encoders
    place(board, "U8", 95.0,  27.0)         # SN74HC14
    place(board, "C20", 95.0,  32.0)        # 100nF decoupling (close to pin 14/7)

    # LEDs + resistors
    place(board, "D1", 88.0,  32.0)         # Green LED (power)
    place(board, "D2", 92.0,  32.0)         # Blue LED (status)
    place(board, "R6", 88.0,  28.0)         # 330R for D1
    place(board, "R7", 92.0,  28.0)         # 330R for D2

    # Buzzer
    place(board, "BZ1", 105.0, 28.0)        # Piezo buzzer

    # EEPROM — on I2C1 bus, near STM32
    place(board, "U9", 62.0,  27.0)         # 24LC256
    place(board, "C21", 62.0,  32.0)        # 100nF decoupling (close to VCC)

    # LM35 — away from heat sources, near centre (priority #8)
    place(board, "U11", 50.0,  30.0)        # LM35 temp sensor
    place(board, "R8",  55.0,  30.0)        # 100R series (output filter)
    place(board, "C22", 55.0,  33.0)        # 10nF filter cap

    # ── ZONE 6: Connectors (edges) ──
    # SWD header at bottom edge
    place(board, "J3", 120.0, 30.0, 0)      # FTSH-107 SWD


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print(f"Loading board: {BOARD_PATH}")
    board = pcbnew.LoadBoard(str(BOARD_PATH))

    fps = list(board.GetFootprints())
    print(f"Found {len(fps)} footprints, {len(board.GetTracks())} tracks")

    # Remove existing board outline (if any)
    to_remove = []
    for drawing in board.GetDrawings():
        if drawing.GetLayer() == pcbnew.Edge_Cuts:
            to_remove.append(drawing)
    for d in to_remove:
        board.Remove(d)

    # Set up design rules
    print("Setting up design rules...")
    setup_design_rules(board)

    # Draw board outline
    print(f"Drawing board outline: {BOARD_W} x {BOARD_H} mm")
    draw_board_outline(board)

    # Place components
    print("Placing components...")
    place_all(board)

    # Save
    board.Save(str(BOARD_PATH))
    print(f"Saved: {BOARD_PATH}")
    print("\nNext steps:")
    print("  1. Open in KiCad → 'Update PCB from Schematic' to sync nets")
    print("  2. Verify placement visually")
    print("  3. Route high-priority signals: USB D+/D- first")
    print("  4. Fill ground planes on In1.Cu and B.Cu")


if __name__ == "__main__":
    main()
