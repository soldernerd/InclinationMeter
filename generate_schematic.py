#!/usr/bin/env python3
"""
KiCad 10 Schematic Generator — Precision Electronic Level Instrument.

Generates a hierarchical .kicad_sch schematic with actual component symbols
placed and wired, following professional schematic layout best practices.

Usage:  python generate_schematic.py
Output: KiCad/ directory with .kicad_sch, .kicad_pro, library tables.

Reference: KiCad_SchematicsGuide.md, spec.md, Netlist.md
"""

import uuid
import json
import re
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR / "KiCad"
LOCAL_LIB_DIR = SCRIPT_DIR / "Libraries" / "KiCad"
KICAD_SYM_DIR = Path(r"C:\Program Files\KiCad\10.0\share\kicad\symbols")

PROJECT_NAME = "InclinationMeter"
DATE = "2026-04-14"
REV = "0.1"

# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def uid():
    return str(uuid.uuid4())


# Current instance path for the sheet being generated.
# Set by each sheet generator before creating components.
# Format: "/{root_uuid}/{sheet_uuid}" for sub-sheets, "/{root_uuid}" for root.
_current_instance_path = ""


# ── Pin position data for all local library symbols ──
# Extracted from .kicad_sym files. Format: {pin_num: (x, y)} in symbol coords (Y-up).
# Connection point = the (at X Y) value from the pin definition.

PINS = {
    "TP4056": {
        "1": (-12.70, 2.54), "2": (-12.70, 0.00), "3": (-12.70, -2.54),
        "4": (-12.70, -5.08), "5": (12.70, -5.08), "6": (12.70, -2.54),
        "7": (12.70, 0.00), "8": (12.70, 2.54), "9": (12.70, 5.08),
    },
    "DW01A": {
        "1": (-12.70, 2.54), "2": (-12.70, 0.00), "3": (-12.70, -2.54),
        "4": (12.70, -2.54), "5": (12.70, 0.00), "6": (12.70, 2.54),
    },
    "FS8205A": {
        "1": (-8.89, 3.81), "2": (-8.89, 1.27), "3": (-8.89, -1.27),
        "4": (-8.89, -3.81), "5": (8.89, -3.81), "6": (8.89, -1.27),
        "7": (8.89, 1.27), "8": (8.89, 3.81),
    },
    "DMG2305UX": {
        "1": (-7.62, 0.00), "2": (5.08, -10.16), "3": (5.08, 10.16),
    },
    "LP5907": {
        "1": (-10.16, 2.54), "2": (-10.16, 0.00), "3": (-10.16, -2.54),
        "4": (10.16, -2.54), "5": (10.16, 2.54),
    },
    "SD6210A": {
        "1": (-12.70, 2.54), "2": (-12.70, 0.00), "3": (-12.70, -2.54),
        "4": (12.70, -2.54), "5": (12.70, 0.00), "6": (12.70, 2.54),
    },
    "SN74AHCT244": {
        "1": (-11.43, 11.43), "2": (-11.43, 8.89), "3": (-11.43, 6.35),
        "4": (-11.43, 3.81), "5": (-11.43, 1.27), "6": (-11.43, -1.27),
        "7": (-11.43, -3.81), "8": (-11.43, -6.35), "9": (-11.43, -8.89),
        "10": (-11.43, -11.43), "11": (11.43, -11.43), "12": (11.43, -8.89),
        "13": (11.43, -6.35), "14": (11.43, -3.81), "15": (11.43, -1.27),
        "16": (11.43, 1.27), "17": (11.43, 3.81), "18": (11.43, 6.35),
        "19": (11.43, 8.89), "20": (11.43, 11.43),
    },
    "SN74HC14": {
        "1": (-10.16, 7.62), "2": (-10.16, 5.08), "3": (-10.16, 2.54),
        "4": (-10.16, 0.00), "5": (-10.16, -2.54), "6": (-10.16, -5.08),
        "7": (-10.16, -7.62), "8": (10.16, -7.62), "9": (10.16, -5.08),
        "10": (10.16, -2.54), "11": (10.16, 0.00), "12": (10.16, 2.54),
        "13": (10.16, 5.08), "14": (10.16, 7.62),
    },
    "RN4871": {
        "1": (-13.97, 8.89), "2": (-13.97, 6.35), "3": (-13.97, 3.81),
        "4": (-13.97, 1.27), "5": (-13.97, -1.27), "6": (-13.97, -3.81),
        "7": (-13.97, -6.35), "8": (-13.97, -8.89),
        "9": (13.97, -8.89), "10": (13.97, -6.35), "11": (13.97, -3.81),
        "12": (13.97, -1.27), "13": (13.97, 1.27), "14": (13.97, 3.81),
        "15": (13.97, 6.35), "16": (13.97, 8.89),
    },
    "24LC256": {
        "1": (-12.70, 6.35), "2": (-12.70, 3.81), "3": (-12.70, 1.27),
        "4": (12.70, -6.35), "5": (12.70, -1.27), "6": (12.70, 1.27),
        "7": (12.70, 6.35), "8": (-12.70, -6.35),
    },
    "FH12_10S": {
        "1": (-5.08, 11.43), "2": (-5.08, 8.89), "3": (-5.08, 6.35),
        "4": (-5.08, 3.81), "5": (-5.08, 1.27), "6": (-5.08, -1.27),
        "7": (-5.08, -3.81), "8": (-5.08, -6.35), "9": (-5.08, -8.89),
        "10": (-5.08, -11.43), "11": (3.81, -16.51), "12": (3.81, 16.51),
    },
    "FTSH_107": {
        "01": (-7.62, 7.62), "02": (7.62, 7.62), "03": (-7.62, 5.08),
        "04": (7.62, 5.08), "05": (-7.62, 2.54), "06": (7.62, 2.54),
        "07": (-7.62, 0.00), "08": (7.62, 0.00), "09": (-7.62, -2.54),
        "10": (7.62, -2.54), "11": (-7.62, -5.08), "12": (7.62, -5.08),
        "13": (-7.62, -7.62), "14": (7.62, -7.62),
    },
    "X50328MSB2GI": {
        "1": (-5.08, 0.00), "2": (5.08, 0.00),
    },
    "CPT_9019A": {
        "1": (-6.35, 1.27), "2": (-6.35, -1.27),
    },
    "LS027B7DH01": {
        "1": (-10.16, 11.43), "2": (-10.16, 8.89), "3": (-10.16, 6.35),
        "4": (-10.16, 3.81), "5": (-10.16, 1.27), "6": (-10.16, -1.27),
        "7": (-10.16, -3.81), "8": (-10.16, -6.35), "9": (-10.16, -8.89),
        "10": (-10.16, -11.43),
    },
    # Inline symbols
    "R": {"1": (0.0, 3.81), "2": (0.0, -3.81)},
    "C": {"1": (0.0, 2.54), "2": (0.0, -2.54)},
    "LED": {"1": (0.0, 2.54), "2": (0.0, -2.54)},
}


def pin(sym_key, pin_num, sx, sy, sym_rot=0):
    """Calculate schematic (x, y) of a pin's wire connection point.

    sym_key:  key into PINS dict
    pin_num:  pin number/name as string
    sx, sy:   symbol placement position in schematic
    sym_rot:  symbol rotation (0, 90, 180, 270)
    """
    px, py = PINS[sym_key][pin_num]
    if sym_rot == 0:
        return (sx + px, sy - py)
    elif sym_rot == 90:
        return (sx - py, sy - px)
    elif sym_rot == 180:
        return (sx - px, sy + py)
    elif sym_rot == 270:
        return (sx + py, sy + px)
    return (sx + px, sy - py)


# ═══════════════════════════════════════════════════════════════════════════
# SYMBOL EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_symbol(lib_path: Path, symbol_name: str) -> str:
    """Extract a single symbol definition from a .kicad_sym file."""
    content = lib_path.read_text(encoding="utf-8")
    pattern = f'(symbol "{symbol_name}"'
    start = content.find(f'\t{pattern}')
    if start == -1:
        start = content.find(pattern)
    if start == -1:
        raise ValueError(f"Symbol '{symbol_name}' not found in {lib_path}")
    if start > 0 and content[start - 1] == '\t':
        start = start  # keep the tab
    depth = 0
    i = start
    while i < len(content):
        if content[i] == '(':
            depth += 1
        elif content[i] == ')':
            depth -= 1
            if depth == 0:
                return content[start:i + 1]
        i += 1
    raise ValueError(f"Unmatched parentheses for symbol '{symbol_name}'")


def get_local_symbol(lib_name: str, sym_name: str) -> tuple:
    """Load symbol from local library. Returns (lib_id, symbol_text)."""
    lib_path = LOCAL_LIB_DIR / f"{lib_name}.kicad_sym"
    sym_text = extract_symbol(lib_path, sym_name)
    lib_id = f"local_{lib_name}:{sym_name}"
    sym_text = sym_text.replace(f'(symbol "{sym_name}"', f'(symbol "local_{lib_name}:{sym_name}"')
    return lib_id, sym_text


# ═══════════════════════════════════════════════════════════════════════════
# S-EXPRESSION BUILDERS
# ═══════════════════════════════════════════════════════════════════════════

def sexp_symbol_instance(lib_id, ref, value, footprint, x, y, rotation=0,
                         unit=1, mirror_y=False, dnp=False,
                         extra_props=None, project_name=PROJECT_NAME,
                         sheet_uuid=None, label_offset=None):
    """Generate a component symbol instance.

    label_offset: (dx, dy) for reference label relative to (x, y).
                  If None, defaults to (2.54, -2.54) for small symbols.
    """
    mirror_str = "\t\t(mirror y)\n" if mirror_y else ""
    dnp_str = "yes" if dnp else "no"
    sym_uuid = uid()
    inst_path = _current_instance_path or f"/{uid()}"

    # Property positions offset from symbol — pushed clear of body
    if label_offset:
        dx, dy = label_offset
    else:
        dx, dy = 2.54, -2.54
    ref_x, ref_y = x + dx, y + dy
    val_x, val_y = x + dx, y + dy - 2.54

    props = f"""\t\t(property "Reference" "{ref}"
\t\t\t(at {ref_x} {ref_y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {val_x} {val_y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t)
\t\t(property "Footprint" "{footprint}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" "~"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" ""
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)"""

    if extra_props:
        for pname, pval in extra_props.items():
            props += f"""
\t\t(property "{pname}" "{pval}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)"""

    return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rotation})
{mirror_str}\t\t(unit {unit})
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp {dnp_str})
\t\t(uuid "{sym_uuid}")
{props}
\t\t(instances
\t\t\t(project "{project_name}"
\t\t\t\t(path "{inst_path}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit {unit})
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""


def sexp_power_symbol(lib_id, ref, value, x, y, rotation=0,
                      project_name=PROJECT_NAME, sheet_uuid=None):
    """Generate a power symbol instance (GND, +3V3, etc.)."""
    sym_uuid = uid()
    inst_path = _current_instance_path or f"/{uid()}"
    return f"""\t(symbol
\t\t(lib_id "{lib_id}")
\t\t(at {x} {y} {rotation})
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom no)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(uuid "{sym_uuid}")
\t\t(property "Reference" "{ref}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Value" "{value}"
\t\t\t(at {x} {y + 2.54} 0)
\t\t\t(effects (font (size 1.27 1.27)))
\t\t)
\t\t(property "Footprint" ""
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Datasheet" ""
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(property "Description" ""
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t\t(pin "1"
\t\t\t(uuid "{uid()}")
\t\t)
\t\t(instances
\t\t\t(project "{project_name}"
\t\t\t\t(path "{inst_path}"
\t\t\t\t\t(reference "{ref}")
\t\t\t\t\t(unit 1)
\t\t\t\t)
\t\t\t)
\t\t)
\t)"""


def sexp_wire(x1, y1, x2, y2):
    return f"""\t(wire
\t\t(pts (xy {x1} {y1}) (xy {x2} {y2}))
\t\t(stroke (width 0) (type default))
\t\t(uuid "{uid()}")
\t)"""


def sexp_label(name, x, y, rotation=0):
    return f"""\t(label "{name}"
\t\t(at {x} {y} {rotation})
\t\t(effects (font (size 1.27 1.27)) (justify left bottom))
\t\t(uuid "{uid()}")
\t)"""


def sexp_global_label(name, x, y, rotation=0, shape="bidirectional"):
    return f"""\t(global_label "{name}"
\t\t(shape {shape})
\t\t(at {x} {y} {rotation})
\t\t(effects (font (size 1.27 1.27)) (justify left))
\t\t(uuid "{uid()}")
\t\t(property "Intersheetref" "${{INTERSHEET_REFS}}"
\t\t\t(at {x} {y} 0)
\t\t\t(effects (font (size 1.27 1.27)) (hide yes))
\t\t)
\t)"""


def sexp_no_connect(x, y):
    return f"""\t(no_connect
\t\t(at {x} {y})
\t\t(uuid "{uid()}")
\t)"""


def sexp_junction(x, y):
    return f"""\t(junction
\t\t(at {x} {y})
\t\t(diameter 0)
\t\t(color 0 0 0 0)
\t\t(uuid "{uid()}")
\t)"""


def sexp_text(text, x, y, size=2.54):
    return f"""\t(text "{text}"
\t\t(at {x} {y} 0)
\t\t(effects (font (size {size} {size})) (justify left bottom))
\t\t(uuid "{uid()}")
\t)"""


def sexp_rect(x1, y1, x2, y2, dash=True):
    """Dashed or solid rectangle for visual grouping."""
    stype = "dash" if dash else "default"
    return f"""\t(polyline
\t\t(pts (xy {x1} {y1}) (xy {x2} {y1}) (xy {x2} {y2}) (xy {x1} {y2}) (xy {x1} {y1}))
\t\t(stroke (width 0.254) (type {stype}))
\t\t(fill (type none))
\t\t(uuid "{uid()}")
\t)"""


def sexp_sheet(name, filename, x, y, w, h, page_num,
               project_name=PROJECT_NAME, root_uuid=None, sheet_uuid=None):
    """Generate a hierarchical sheet reference."""
    sheet_uuid = sheet_uuid or uid()
    return f"""\t(sheet
\t\t(at {x} {y})
\t\t(size {w} {h})
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(stroke (width 0) (type solid))
\t\t(fill (color 0 0 0 0.0000))
\t\t(uuid "{sheet_uuid}")
\t\t(property "Sheetname" "{name}"
\t\t\t(at {x} {y - 0.762} 0)
\t\t\t(effects (font (size 1.524 1.524)) (justify left bottom))
\t\t)
\t\t(property "Sheetfile" "{filename}"
\t\t\t(at {x} {y + h + 0.762} 0)
\t\t\t(effects (font (size 1.524 1.524)) (justify left top))
\t\t)
\t\t(instances
\t\t\t(project "{project_name}"
\t\t\t\t(path "/{root_uuid}"
\t\t\t\t\t(page "{page_num}")
\t\t\t\t)
\t\t\t)
\t\t)
\t)""", sheet_uuid


def wrap_schematic(content, title="", paper="A4", root_uuid=None,
                   page_num="1", lib_symbols_text="",
                   sheet_instances_extra=""):
    r_uuid = root_uuid or uid()
    si = f"""\t(sheet_instances
\t\t(path "/"
\t\t\t(page "{page_num}")
\t\t)
{sheet_instances_extra}\t)"""

    return f"""(kicad_sch
\t(version 20250114)
\t(generator "eeschema")
\t(generator_version "10.0")
\t(uuid "{r_uuid}")
\t(paper "{paper}")
\t(title_block
\t\t(title "{title}")
\t\t(date "{DATE}")
\t\t(rev "{REV}")
\t)
\t(lib_symbols
{lib_symbols_text}\t)
{content}
{si}
\t(embedded_fonts no)
)
"""


# ═══════════════════════════════════════════════════════════════════════════
# POWER SYMBOL COUNTERS
# ═══════════════════════════════════════════════════════════════════════════

_pwr_counter = [0]
def next_pwr():
    _pwr_counter[0] += 1
    return f"#PWR{_pwr_counter[0]:03d}"

_ref_counters = {}
def next_ref(prefix):
    """Get next reference designator: next_ref('R') -> 'R1', 'R2', ..."""
    _ref_counters.setdefault(prefix, 0)
    _ref_counters[prefix] += 1
    return f"{prefix}{_ref_counters[prefix]}"


# ═══════════════════════════════════════════════════════════════════════════
# WIRING PATTERN HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def gnd(elements, x, y):
    """Place GND power symbol and wire from (x,y) down 2.54mm to it."""
    gy = y + 2.54
    elements.append(sexp_wire(x, y, x, gy))
    elements.append(sexp_power_symbol("power:GND", next_pwr(), "GND", x, gy))


def pwr33(elements, x, y):
    """Place +3V3 symbol and wire from (x,y) up 2.54mm to it."""
    py = y - 2.54
    elements.append(sexp_wire(x, y, x, py))
    elements.append(sexp_power_symbol("power:+3V3", next_pwr(), "+3V3", x, py))


def pwr5v(elements, x, y):
    """Place +5V symbol above."""
    py = y - 2.54
    elements.append(sexp_wire(x, y, x, py))
    elements.append(sexp_power_symbol("power:+5V", next_pwr(), "+5V", x, py))


def pwr_vbat(elements, x, y):
    """Place VBAT symbol above."""
    py = y - 2.54
    elements.append(sexp_wire(x, y, x, py))
    elements.append(sexp_power_symbol("power:VBAT", next_pwr(), "VBAT", x, py))


def pwr_vbus(elements, x, y):
    """Place VBUS symbol above."""
    py = y - 2.54
    elements.append(sexp_wire(x, y, x, py))
    elements.append(sexp_power_symbol("power:VBUS", next_pwr(), "VBUS", x, py))


def label_right(elements, x, y, name, length=7.62):
    """Wire right from (x,y) then place net label."""
    lx = x + length
    elements.append(sexp_wire(x, y, lx, y))
    elements.append(sexp_label(name, lx, y, 0))


def label_left(elements, x, y, name, length=7.62):
    """Wire left from (x,y) then place net label."""
    lx = x - length
    elements.append(sexp_wire(x, y, lx, y))
    elements.append(sexp_label(name, lx, y, 180))


def glabel_right(elements, x, y, name, shape="bidirectional", length=5.08):
    """Wire right then place global label."""
    lx = x + length
    elements.append(sexp_wire(x, y, lx, y))
    elements.append(sexp_global_label(name, lx, y, 0, shape))


def glabel_left(elements, x, y, name, shape="bidirectional", length=5.08):
    """Wire left then place global label."""
    lx = x - length
    elements.append(sexp_wire(x, y, lx, y))
    elements.append(sexp_global_label(name, lx, y, 180, shape))


def place_bypass_cap(elements, x, y, ref, value="100nF",
                     fp="Capacitor_SMD:C_0603_1608Metric",
                     rail="+3V3"):
    """Place vertical bypass cap with power above and GND below."""
    elements.append(sexp_symbol_instance("inline:C", ref, value, fp, x, y))
    cx1 = pin("C", "1", x, y)  # top
    cx2 = pin("C", "2", x, y)  # bottom
    if rail == "+3V3":
        pwr33(elements, cx1[0], cx1[1])
    elif rail == "+5V":
        pwr5v(elements, cx1[0], cx1[1])
    elif rail == "VBAT":
        pwr_vbat(elements, cx1[0], cx1[1])
    elif rail == "VBUS":
        pwr_vbus(elements, cx1[0], cx1[1])
    gnd(elements, cx2[0], cx2[1])


def place_resistor(elements, x, y, ref, value, rot=0,
                   fp="Resistor_SMD:R_0603_1608Metric"):
    """Place a resistor at (x,y) with given rotation."""
    elements.append(sexp_symbol_instance("inline:R", ref, value, fp, x, y, rotation=rot))


# ═══════════════════════════════════════════════════════════════════════════
# INLINE SYMBOL DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

POWER_GND = """\t\t(symbol "power:GND"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR" (at 0 -6.35 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Value" "GND" (at 0 -3.81 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "GND_0_1"
\t\t\t\t(polyline
\t\t\t\t\t(pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27))
\t\t\t\t\t(stroke (width 0) (type default)) (fill (type none))
\t\t\t\t)
\t\t\t)
\t\t\t(symbol "GND_1_1"
\t\t\t\t(pin power_in line (at 0 0 270) (length 0)
\t\t\t\t\t(name "GND" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

POWER_3V3 = """\t\t(symbol "power:+3V3"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Value" "+3V3" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "+3V3_0_1"
\t\t\t\t(polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "+3V3_1_1"
\t\t\t\t(pin power_in line (at 0 0 90) (length 0)
\t\t\t\t\t(name "+3V3" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

POWER_5V = """\t\t(symbol "power:+5V"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Value" "+5V" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "+5V_0_1"
\t\t\t\t(polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "+5V_1_1"
\t\t\t\t(pin power_in line (at 0 0 90) (length 0)
\t\t\t\t\t(name "+5V" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

POWER_VBAT = """\t\t(symbol "power:VBAT"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Value" "VBAT" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "VBAT_0_1"
\t\t\t\t(polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "VBAT_1_1"
\t\t\t\t(pin power_in line (at 0 0 90) (length 0)
\t\t\t\t\t(name "VBAT" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

POWER_VBUS = """\t\t(symbol "power:VBUS"
\t\t\t(power)
\t\t\t(pin_names (offset 0))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "#PWR" (at 0 -3.81 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Value" "VBUS" (at 0 3.556 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "VBUS_0_1"
\t\t\t\t(polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "VBUS_1_1"
\t\t\t\t(pin power_in line (at 0 0 90) (length 0)
\t\t\t\t\t(name "VBUS" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

ALL_POWER_DEFS = "\n".join([POWER_GND, POWER_3V3, POWER_5V, POWER_VBAT, POWER_VBUS])

# ── Inline passive symbols ──

INLINE_R = """\t\t(symbol "inline:R"
\t\t\t(pin_names (offset 0) hide)
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "R" (at 2.032 0 90) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "R" (at -2.032 0 90) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "Resistor" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "R_0_1"
\t\t\t\t(rectangle (start -1.016 -2.54) (end 1.016 2.54)
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "R_1_1"
\t\t\t\t(pin passive line (at 0 3.81 270) (length 1.27)
\t\t\t\t\t(name "~" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin passive line (at 0 -3.81 90) (length 1.27)
\t\t\t\t\t(name "~" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

INLINE_C = """\t\t(symbol "inline:C"
\t\t\t(pin_names (offset 0) hide)
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "C" (at 2.54 0 90) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "C" (at -2.54 0 90) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "Capacitor" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "C_0_1"
\t\t\t\t(polyline (pts (xy -1.524 -0.508) (xy 1.524 -0.508))
\t\t\t\t\t(stroke (width 0.3048) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -1.524 0.508) (xy 1.524 0.508))
\t\t\t\t\t(stroke (width 0.3048) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "C_1_1"
\t\t\t\t(pin passive line (at 0 2.54 270) (length 2.032)
\t\t\t\t\t(name "~" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin passive line (at 0 -2.54 90) (length 2.032)
\t\t\t\t\t(name "~" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

INLINE_LED = """\t\t(symbol "inline:LED"
\t\t\t(pin_names (offset 0) hide)
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "D" (at 2.54 0 90) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "LED" (at -2.54 0 90) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "LED" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "LED_0_1"
\t\t\t\t(polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy -1.27 0) (xy 1.27 0)) (stroke (width 0) (type default)) (fill (type none)))
\t\t\t\t(polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27) (xy -1.27 0) (xy 1.27 1.27))
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type none)))
\t\t\t)
\t\t\t(symbol "LED_1_1"
\t\t\t\t(pin passive line (at 0 2.54 270) (length 2.54)
\t\t\t\t\t(name "A" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin passive line (at 0 -2.54 90) (length 2.54)
\t\t\t\t\t(name "K" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

INLINE_LM35 = """\t\t(symbol "inline:LM35"
\t\t\t(pin_names (offset 1.016))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "U" (at 0 6.35 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "LM35" (at 0 -6.35 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "Package_TO_SOT_SMD:SOT-23" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "LM35 Analog Temperature Sensor 10mV/C" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "LCSC Part" "C9900081740" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "LM35_0_1"
\t\t\t\t(rectangle (start -5.08 5.08) (end 5.08 -5.08)
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))
\t\t\t)
\t\t\t(symbol "LM35_1_1"
\t\t\t\t(pin power_in line (at -7.62 2.54 0) (length 2.54)
\t\t\t\t\t(name "VS+" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "1" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin output line (at 7.62 0 180) (length 2.54)
\t\t\t\t\t(name "VOUT" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "2" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t\t(pin power_in line (at -7.62 -2.54 0) (length 2.54)
\t\t\t\t\t(name "GND" (effects (font (size 1.27 1.27))))
\t\t\t\t\t(number "3" (effects (font (size 1.27 1.27))))
\t\t\t\t)
\t\t\t)
\t\t)"""

PINS["LM35"] = {"1": (-7.62, 2.54), "2": (7.62, 0), "3": (-7.62, -2.54)}

ALL_INLINE_DEFS = "\n".join([INLINE_R, INLINE_C, INLINE_LED, INLINE_LM35])

# ── Custom STM32G0B1RET6 symbol (functional pin arrangement, 46 used pins) ──

def _stm32_pin(name, x, y, rot, etype="unspecified", num=""):
    pnum = num or name
    return (f'\t\t\t\t(pin {etype} line (at {x} {y} {rot}) (length 5.08)\n'
            f'\t\t\t\t\t(name "{name}" (effects (font (size 1.016 1.016))))\n'
            f'\t\t\t\t\t(number "{pnum}" (effects (font (size 1.016 1.016))))\n'
            f'\t\t\t\t)')

def build_stm32_symbol():
    """Build STM32G0B1RET6 symbol with physical LQFP-64 pin layout.

    Physical pinout (counterclockwise from pin 1 marker):
      Left (1-16, top to bottom), Bottom (17-32, left to right),
      Right (33-48, bottom to top), Top (49-64, right to left).
    """
    # Complete LQFP-64 pinout from STM32_PinAssignment.md
    # Pin names: port-only (short) to avoid overlap on the dense 2.54mm grid.
    # Signal assignments are documented via global labels on the schematic sheet.
    # (name, pin_number, electrical_type)
    # Left side: pins 1–16 (top to bottom)
    left_pins = [
        ("PC11",    "1",  "bidirectional"),
        ("PC12",    "2",  "bidirectional"),
        ("PC13",    "3",  "bidirectional"),
        ("PC14",    "4",  "bidirectional"),
        ("PC15",    "5",  "bidirectional"),
        ("VBAT",    "6",  "power_in"),
        ("VREF+",   "7",  "power_in"),
        ("VDD",     "8",  "power_in"),
        ("VSS",     "9",  "power_in"),
        ("PF0",     "10", "input"),
        ("PF1",     "11", "output"),
        ("~{NRST}", "12", "input"),
        ("PC0",     "13", "bidirectional"),
        ("PC1",     "14", "bidirectional"),
        ("PC2",     "15", "bidirectional"),
        ("PC3",     "16", "bidirectional"),
    ]
    # Bottom side: pins 17–32 (left to right)
    bot_pins = [
        ("PA0",     "17", "bidirectional"),
        ("PA1",     "18", "bidirectional"),
        ("PA2",     "19", "bidirectional"),
        ("PA3",     "20", "bidirectional"),
        ("PA4",     "21", "bidirectional"),
        ("PA5",     "22", "bidirectional"),
        ("PA6",     "23", "bidirectional"),
        ("PA7",     "24", "bidirectional"),
        ("PC4",     "25", "bidirectional"),
        ("PC5",     "26", "bidirectional"),
        ("PB0",     "27", "bidirectional"),
        ("PB1",     "28", "bidirectional"),
        ("PB2",     "29", "bidirectional"),
        ("PB10",    "30", "bidirectional"),
        ("PB11",    "31", "bidirectional"),
        ("PB12",    "32", "bidirectional"),
    ]
    # Right side: pins 33–48 (bottom to top)
    right_pins = [
        ("PB13",    "33", "bidirectional"),
        ("PB14",    "34", "bidirectional"),
        ("PB15",    "35", "bidirectional"),
        ("PA8",     "36", "bidirectional"),
        ("PA9",     "37", "bidirectional"),
        ("PC6",     "38", "bidirectional"),
        ("PC7",     "39", "bidirectional"),
        ("PD8",     "40", "bidirectional"),
        ("PD9",     "41", "bidirectional"),
        ("PA10",    "42", "bidirectional"),
        ("PA11",    "43", "bidirectional"),
        ("PA12",    "44", "bidirectional"),
        ("PA13",    "45", "bidirectional"),
        ("PA14",    "46", "input"),
        ("PA15",    "47", "bidirectional"),
        ("PC8",     "48", "bidirectional"),
    ]
    # Top side: pins 49–64 (right to left)
    top_pins = [
        ("PC9",     "49", "bidirectional"),
        ("PD0",     "50", "bidirectional"),
        ("PD1",     "51", "bidirectional"),
        ("PD2",     "52", "bidirectional"),
        ("PD3",     "53", "bidirectional"),
        ("PD4",     "54", "bidirectional"),
        ("PD5",     "55", "bidirectional"),
        ("PD6",     "56", "bidirectional"),
        ("PB3",     "57", "bidirectional"),
        ("PB4",     "58", "bidirectional"),
        ("PB5",     "59", "bidirectional"),
        ("PB6",     "60", "bidirectional"),
        ("PB7",     "61", "bidirectional"),
        ("PB8",     "62", "bidirectional"),
        ("PB9",     "63", "bidirectional"),
        ("PC10",    "64", "bidirectional"),
    ]

    # Geometry: 16 pins per side, 2.54 mm spacing
    # Pin span = 15 * 2.54 = 38.1 mm, centered → ±19.05
    pin_len = 5.08
    n = 16  # pins per side
    span = (n - 1) * 2.54  # 38.1
    half_span = span / 2   # 19.05
    body_half = half_span + 1.27  # 20.32 — body extends 1.27 past outermost pin

    pin_defs = []
    stm_pins = {}  # for PINS dict

    # Left side: pins at x = -(body_half + pin_len), rotation 0 (extends right)
    lx = -(body_half + pin_len)  # -25.4
    for i, (name, num, etype) in enumerate(left_pins):
        y = half_span - i * 2.54
        pin_defs.append(_stm32_pin(name, lx, y, 0, etype, num))
        stm_pins[num] = (lx, y)

    # Bottom side: pins at y = -(body_half + pin_len), rotation 90 (extends up)
    by = -(body_half + pin_len)  # -25.4
    for i, (name, num, etype) in enumerate(bot_pins):
        x = -half_span + i * 2.54
        pin_defs.append(_stm32_pin(name, x, by, 90, etype, num))
        stm_pins[num] = (x, by)

    # Right side: pins at x = (body_half + pin_len), rotation 180 (extends left)
    # Pin 33 at bottom, 48 at top
    rx = body_half + pin_len  # 25.4
    for i, (name, num, etype) in enumerate(right_pins):
        y = -half_span + i * 2.54
        pin_defs.append(_stm32_pin(name, rx, y, 180, etype, num))
        stm_pins[num] = (rx, y)

    # Top side: pins at y = (body_half + pin_len), rotation 270 (extends down)
    # Pin 49 at right, 64 at left
    ty = body_half + pin_len  # 25.4
    for i, (name, num, etype) in enumerate(top_pins):
        x = half_span - i * 2.54
        pin_defs.append(_stm32_pin(name, x, ty, 270, etype, num))
        stm_pins[num] = (x, ty)

    # Store in PINS
    PINS["STM32"] = stm_pins

    pins_text = "\n".join(pin_defs)

    return f"""\t\t(symbol "inline:STM32G0B1RET6"
\t\t\t(pin_names (offset 1.016))
\t\t\t(exclude_from_sim no)
\t\t\t(in_bom yes)
\t\t\t(on_board yes)
\t\t\t(property "Reference" "U" (at 0 {body_half + 1.27} 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Value" "STM32G0B1RET6" (at 0 {-body_half - 1.27} 0) (effects (font (size 1.27 1.27))))
\t\t\t(property "Footprint" "Package_QFP:LQFP-64_10x10mm_P0.5mm" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Datasheet" "~" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "Description" "STM32G0B1RET6 ARM Cortex-M0+ 64MHz 512KB Flash" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(property "LCSC Part" "C2829307" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
\t\t\t(symbol "STM32G0B1RET6_0_1"
\t\t\t\t(rectangle (start {-body_half} {-body_half}) (end {body_half} {body_half})
\t\t\t\t\t(stroke (width 0.254) (type default)) (fill (type background)))
\t\t\t)
\t\t\t(symbol "STM32G0B1RET6_1_1"
{pins_text}
\t\t\t)
\t\t)"""


# ═══════════════════════════════════════════════════════════════════════════
# SHEET GENERATORS
# ═══════════════════════════════════════════════════════════════════════════

def generate_power_sheet(root_uuid, sheet_uuid):
    """Page 2: Power supply — battery, charger, protection, LDO, charge pump."""
    global _current_instance_path
    _current_instance_path = f"/{root_uuid}/{sheet_uuid}"
    el = []  # elements
    lib_syms = [ALL_POWER_DEFS, ALL_INLINE_DEFS]

    # Load local symbols
    for lib in ["TP4056", "DW01A", "FS8205A", "DMG2305UX", "LP5907", "SD6210A"]:
        try:
            sym_map = {
                "TP4056": ("TP4056", "TP4056_C382139"),
                "DW01A": ("DW01A", "DW01A"),
                "FS8205A": ("FS8205A", "8205A_C14212"),
                "DMG2305UX": ("DMG2305UX", "DMG2305UX-13"),
                "LP5907": ("LP5907", "LP5907MFX-3.3_NOPB"),
                "SD6210A": ("SD6210A", "SD6210A"),
            }
            ln, sn = sym_map[lib]
            _, sym_text = get_local_symbol(ln, sn)
            lib_syms.append(sym_text)
        except Exception as e:
            print(f"  Warning: Could not load {lib}: {e}")

    # ── Section 1: Reverse Polarity Protection (left) ──
    el.append(sexp_rect(27, 35, 120, 130))
    el.append(sexp_text("Reverse Polarity Protection", 29, 37))

    # Battery connector label
    el.append(sexp_text("J1 Battery", 30, 55, 1.524))
    el.append(sexp_global_label("VBAT_RAW", 50, 65, 0, "passive"))
    el.append(sexp_global_label("CELL_NEG", 50, 80, 0, "passive"))

    # Q3 DMG2305UX at (80, 90)
    q3x, q3y = 80, 95
    el.append(sexp_symbol_instance(
        "local_DMG2305UX:DMG2305UX-13", "Q3", "DMG2305UX",
        "local_DMG2305UX:SOT-23-3_L2.9-W1.3-P1.90-LS2.4-BR", q3x, q3y))
    # Gate (pin 1): wire left to R_RPP
    g = pin("DMG2305UX", "1", q3x, q3y)
    # Source (pin 2, below): VBAT_RAW
    s = pin("DMG2305UX", "2", q3x, q3y)
    # Drain (pin 3, above): VBAT (protected)
    d = pin("DMG2305UX", "3", q3x, q3y)
    label_left(el, s[0], s[1], "VBAT_RAW")
    label_right(el, d[0], d[1], "VBAT")

    # R_RPP 100k gate pull-down
    rpx, rpy = g[0] - 10, g[1]
    place_resistor(el, rpx, rpy, next_ref("R"), "100k", rot=90)
    rp1 = pin("R", "1", rpx, rpy, 90)  # left end
    rp2 = pin("R", "2", rpx, rpy, 90)  # right end
    el.append(sexp_wire(rp2[0], rp2[1], g[0], g[1]))
    gnd(el, rp1[0], rp1[1])

    # ── Section 2: TP4056 LiPo Charger ──
    el.append(sexp_rect(130, 35, 280, 130))
    el.append(sexp_text("TP4056 LiPo Charger", 132, 37))

    tpx, tpy = 200, 80
    el.append(sexp_symbol_instance(
        "local_TP4056:TP4056_C382139", "U3", "TP4056",
        "local_TP4056:ESOP-8_L4.9-W3.9-P1.27-LS6.0-BL-EP", tpx, tpy,
        label_offset=(15, -10)))

    # Pin connections
    tp_temp = pin("TP4056", "1", tpx, tpy)   # TEMP -> GND (NTC disabled)
    tp_prog = pin("TP4056", "2", tpx, tpy)   # PROG -> R to GND
    tp_gnd = pin("TP4056", "3", tpx, tpy)    # GND
    tp_vcc = pin("TP4056", "4", tpx, tpy)    # VCC <- VUSB
    tp_bat = pin("TP4056", "5", tpx, tpy)    # BAT -> VBAT
    tp_stdby = pin("TP4056", "6", tpx, tpy)  # STDBY (NC)
    tp_chrg = pin("TP4056", "7", tpx, tpy)   # CHRG -> CHG_SENSE
    tp_ce = pin("TP4056", "8", tpx, tpy)     # CE <- VUSB
    tp_ep = pin("TP4056", "9", tpx, tpy)     # EP (pad) -> GND

    # TEMP to GND
    gnd(el, tp_temp[0], tp_temp[1])
    # GND pin
    gnd(el, tp_gnd[0], tp_gnd[1])
    # EP to GND
    gnd(el, tp_ep[0], tp_ep[1])
    # VCC from VBUS
    pwr_vbus(el, tp_vcc[0], tp_vcc[1])
    # CE tied to VBUS
    pwr_vbus(el, tp_ce[0], tp_ce[1])
    # BAT output -> VBAT label
    label_right(el, tp_bat[0], tp_bat[1], "VBAT")
    # CHRG -> global label
    glabel_right(el, tp_chrg[0], tp_chrg[1], "CHG_SENSE", "output")
    # STDBY -> no connect
    el.append(sexp_no_connect(tp_stdby[0], tp_stdby[1]))

    # R_PROG 2.4k
    rpgx, rpgy = tp_prog[0] - 10, tp_prog[1]
    place_resistor(el, rpgx, rpgy, next_ref("R"), "2.4k", rot=90)
    rp1 = pin("R", "1", rpgx, rpgy, 90)
    rp2 = pin("R", "2", rpgx, rpgy, 90)
    el.append(sexp_wire(rp2[0], rp2[1], tp_prog[0], tp_prog[1]))
    gnd(el, rp1[0], rp1[1])

    # Input decoupling C_VUSB 10uF
    place_bypass_cap(el, tpx - 30, tpy, next_ref("C"), "10uF", rail="VBUS")

    # ── Section 3: Cell Protection (DW01A + FS8205A) ──
    el.append(sexp_rect(27, 145, 280, 240))
    el.append(sexp_text("Cell Protection (DW01A + FS8205A)", 29, 147))

    dwx, dwy = 100, 185
    el.append(sexp_symbol_instance(
        "local_DW01A:DW01A", "U4", "DW01A",
        "local_DW01A:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL", dwx, dwy,
        label_offset=(15, -6)))

    dw_od = pin("DW01A", "1", dwx, dwy)   # OD -> FS8205A G1
    dw_cs = pin("DW01A", "2", dwx, dwy)   # CS -> R_CS to GND
    dw_oc = pin("DW01A", "3", dwx, dwy)   # OC -> FS8205A G2
    dw_td = pin("DW01A", "4", dwx, dwy)   # TD (NC)
    dw_vdd = pin("DW01A", "5", dwx, dwy)  # VDD <- via R_DW from VBAT
    dw_vss = pin("DW01A", "6", dwx, dwy)  # VSS <- CELL_NEG

    # OD, OC -> labels for FS8205A
    label_left(el, dw_od[0], dw_od[1], "PROT_OD")
    label_left(el, dw_oc[0], dw_oc[1], "PROT_OC")
    # CS -> R_CS 1k to GND
    rcsx = dw_cs[0] - 10
    place_resistor(el, rcsx, dw_cs[1], next_ref("R"), "1k", rot=90)
    rc1 = pin("R", "1", rcsx, dw_cs[1], 90)
    rc2 = pin("R", "2", rcsx, dw_cs[1], 90)
    el.append(sexp_wire(rc2[0], rc2[1], dw_cs[0], dw_cs[1]))
    gnd(el, rc1[0], rc1[1])
    # TD -> NC
    el.append(sexp_no_connect(dw_td[0], dw_td[1]))
    # VDD <- R_DW 470R from VBAT
    label_right(el, dw_vdd[0], dw_vdd[1], "DW01_VDD")
    # VSS -> CELL_NEG label
    label_right(el, dw_vss[0], dw_vss[1], "CELL_NEG")

    # FS8205A — well separated from DW01A
    fsx, fsy = 210, 195
    el.append(sexp_symbol_instance(
        "local_FS8205A:8205A_C14212", "Q1", "FS8205A",
        "local_FS8205A:TSSOP-8_L4.4-W3.0-P0.65-LS6.4-BL-2", fsx, fsy,
        label_offset=(12, -8)))

    fs_d1 = pin("FS8205A", "1", fsx, fsy)   # D (shared drain)
    fs_s11 = pin("FS8205A", "2", fsx, fsy)  # S1
    fs_s12 = pin("FS8205A", "3", fsx, fsy)  # S1
    fs_g1 = pin("FS8205A", "4", fsx, fsy)   # G1 <- PROT_OD
    fs_g2 = pin("FS8205A", "5", fsx, fsy)   # G2 <- PROT_OC
    fs_s21 = pin("FS8205A", "6", fsx, fsy)  # S2 -> GND
    fs_s22 = pin("FS8205A", "7", fsx, fsy)  # S2 -> GND
    fs_d2 = pin("FS8205A", "8", fsx, fsy)   # D (shared drain)

    label_left(el, fs_g1[0], fs_g1[1], "PROT_OD")
    label_right(el, fs_g2[0], fs_g2[1], "PROT_OC")
    label_left(el, fs_s11[0], fs_s11[1], "CELL_NEG")
    label_left(el, fs_s12[0], fs_s12[1], "CELL_NEG")
    glabel_right(el, fs_s21[0], fs_s21[1], "GND", "passive")
    glabel_right(el, fs_s22[0], fs_s22[1], "GND", "passive")

    # ── Section 4: LP5907 3.3V LDO ──
    el.append(sexp_rect(295, 35, 410, 130))
    el.append(sexp_text("LP5907MFX-3.3 LDO", 297, 37))

    lx, ly = 350, 80
    el.append(sexp_symbol_instance(
        "local_LP5907:LP5907MFX-3.3_NOPB", "U5", "LP5907MFX-3.3",
        "local_LP5907:SOT-23-5_L3.0-W1.7-P0.95-LS2.8-BR", lx, ly))

    lp_in = pin("LP5907", "1", lx, ly)    # IN <- VBAT
    lp_gnd = pin("LP5907", "2", lx, ly)   # GND
    lp_en = pin("LP5907", "3", lx, ly)    # EN <- LDO_EN
    lp_nc = pin("LP5907", "4", lx, ly)    # NC
    lp_out = pin("LP5907", "5", lx, ly)   # OUT -> +3V3

    pwr_vbat(el, lp_in[0], lp_in[1])
    gnd(el, lp_gnd[0], lp_gnd[1])
    glabel_left(el, lp_en[0], lp_en[1], "LDO_EN", "input")
    el.append(sexp_no_connect(lp_nc[0], lp_nc[1]))
    pwr33(el, lp_out[0], lp_out[1])

    # Input cap 1uF
    place_bypass_cap(el, lx - 22, ly, next_ref("C"), "1uF", rail="VBAT")
    # Output cap 10uF
    place_bypass_cap(el, lx + 22, ly, next_ref("C"), "10uF", rail="+3V3")

    # ── Section 5: SD6210A 5V Charge Pump ──
    el.append(sexp_rect(295, 145, 410, 240))
    el.append(sexp_text("SD6210A 5V Charge Pump", 297, 147))

    sdx, sdy = 350, 190
    el.append(sexp_symbol_instance(
        "local_SD6210A:SD6210A", "U6", "SD6210A",
        "local_SD6210A:SOT-23-6_L2.9-W1.6-P0.95-LS2.8-BL", sdx, sdy))

    sd_vout = pin("SD6210A", "1", sdx, sdy)  # VOUT -> +5V
    sd_gnd = pin("SD6210A", "2", sdx, sdy)   # GND
    sd_en = pin("SD6210A", "3", sdx, sdy)    # EN <- +3V3
    sd_cn = pin("SD6210A", "4", sdx, sdy)    # C- -> flying cap
    sd_vin = pin("SD6210A", "5", sdx, sdy)   # VIN <- VBAT
    sd_cp = pin("SD6210A", "6", sdx, sdy)    # C+ -> flying cap

    pwr5v(el, sd_vout[0], sd_vout[1])
    gnd(el, sd_gnd[0], sd_gnd[1])
    pwr33(el, sd_en[0], sd_en[1])
    pwr_vbat(el, sd_vin[0], sd_vin[1])
    # Flying cap between C+ and C-
    label_right(el, sd_cp[0], sd_cp[1], "CFLY_P")
    label_right(el, sd_cn[0], sd_cn[1], "CFLY_N")

    # Flying cap — offset from SD6210A
    fcx = sdx + 35
    el.append(sexp_symbol_instance("inline:C", next_ref("C"), "1uF",
                                   "Capacitor_SMD:C_0603_1608Metric", fcx, sdy))
    fc1 = pin("C", "1", fcx, sdy)
    fc2 = pin("C", "2", fcx, sdy)
    label_left(el, fc1[0], fc1[1], "CFLY_P", 5.08)
    label_left(el, fc2[0], fc2[1], "CFLY_N", 5.08)

    # Output cap 10uF
    place_bypass_cap(el, sdx - 25, sdy, next_ref("C"), "10uF", rail="+5V")

    # ── Section 6: VBAT Monitoring ──
    el.append(sexp_rect(27, 255, 200, 325))
    el.append(sexp_text("VBAT Monitoring (ADC)", 29, 257))

    # Voltage divider: VBAT -> R1 100k -> midpoint -> R2 390k -> GND
    vdx = 80
    place_resistor(el, vdx, 280, next_ref("R"), "100k")
    place_resistor(el, vdx, 305, next_ref("R"), "390k")
    r1_top = pin("R", "1", vdx, 280)
    r1_bot = pin("R", "2", vdx, 280)
    r2_top = pin("R", "1", vdx, 305)
    r2_bot = pin("R", "2", vdx, 305)
    pwr_vbat(el, r1_top[0], r1_top[1])
    el.append(sexp_wire(r1_bot[0], r1_bot[1], r2_top[0], r2_top[1]))
    gnd(el, r2_bot[0], r2_bot[1])
    # Midpoint label -> VBAT_SENSE
    mid_y = (r1_bot[1] + r2_top[1]) / 2
    glabel_right(el, r1_bot[0] + 2.54, mid_y, "VBAT_SENSE", "output", 5.08)
    el.append(sexp_wire(r1_bot[0], r1_bot[1], r1_bot[0] + 2.54, mid_y))
    # Filter cap 100nF
    place_bypass_cap(el, vdx + 25, 295, next_ref("C"), "100nF")

    content = "\n".join(el)
    lib_text = "\n".join(lib_syms)
    return wrap_schematic(content, title="Power Supply", paper="A3",
                          root_uuid=sheet_uuid, page_num="2",
                          lib_symbols_text=lib_text), sheet_uuid


def generate_mcu_sheet(root_uuid, sheet_uuid):
    """Page 3: STM32G0B1RET6 MCU with crystal, decoupling, reset."""
    global _current_instance_path
    _current_instance_path = f"/{root_uuid}/{sheet_uuid}"
    el = []
    stm32_sym = build_stm32_symbol()
    lib_syms = [ALL_POWER_DEFS, ALL_INLINE_DEFS, stm32_sym]

    # Load crystal symbol
    try:
        _, xtal_sym = get_local_symbol("X50328MSB2GI", "X50328MSB2GI")
        lib_syms.append(xtal_sym)
    except Exception as e:
        print(f"  Warning: Crystal symbol: {e}")

    # ── MCU placement (center of A3) ──
    mx, my = 210, 165
    el.append(sexp_symbol_instance(
        "inline:STM32G0B1RET6", "U1", "STM32G0B1RET6",
        "Package_QFP:LQFP-64_10x10mm_P0.5mm", mx, my,
        label_offset=(0, -24)))

    # ── Power connections (left side: pins 6=VBAT, 7=VREF+, 8=VDD, 9=VSS) ──
    vdd = pin("STM32", "8", mx, my)
    pwr33(el, vdd[0], vdd[1])
    vref = pin("STM32", "7", mx, my)
    pwr33(el, vref[0], vref[1])
    vbat_p = pin("STM32", "6", mx, my)
    pwr33(el, vbat_p[0], vbat_p[1])
    vss = pin("STM32", "9", mx, my)
    gnd(el, vss[0], vss[1])

    # ── Decoupling caps near MCU ──
    # Place in a row above the MCU, spaced 15mm apart to avoid label overlap
    cap_x = mx - 50
    cap_y = my - 35
    cap_sp = 15  # spacing between caps
    place_bypass_cap(el, cap_x,              cap_y, next_ref("C"), "100nF")      # VDD 100nF
    place_bypass_cap(el, cap_x + cap_sp,     cap_y, next_ref("C"), "100nF")      # VDD 100nF
    place_bypass_cap(el, cap_x + cap_sp * 2, cap_y, next_ref("C"), "4.7uF",
                     fp="Capacitor_SMD:C_0805_2012Metric")                        # VDD bulk
    place_bypass_cap(el, cap_x + cap_sp * 3, cap_y, next_ref("C"), "1uF")        # VREF+ 1uF
    place_bypass_cap(el, cap_x + cap_sp * 4, cap_y, next_ref("C"), "10nF")       # VREF+ 10nF NP0
    place_bypass_cap(el, cap_x + cap_sp * 5, cap_y, next_ref("C"), "100nF")      # VBAT 100nF
    el.append(sexp_text("Decoupling capacitors", cap_x - 2, cap_y - 10, 1.524))

    # ── Crystal (near pins 10/11 on left side) ──
    el.append(sexp_rect(mx - 85, my - 20, mx - 38, my + 25))
    el.append(sexp_text("8 MHz Crystal", mx - 83, my - 18))

    yx, yy = mx - 55, my
    el.append(sexp_symbol_instance(
        "local_X50328MSB2GI:X50328MSB2GI", "Y1", "8MHz",
        "local_X50328MSB2GI:CRYSTAL-SMD_L5.0-W3.2", yx, yy))

    y1p = pin("X50328MSB2GI", "1", yx, yy)
    y2p = pin("X50328MSB2GI", "2", yx, yy)
    label_left(el, y1p[0], y1p[1], "OSC_IN")
    label_right(el, y2p[0], y2p[1], "OSC_OUT")

    # Load caps 33pF
    cx1, cy1 = yx - 12, yy + 15
    el.append(sexp_symbol_instance("inline:C", next_ref("C"), "33pF",
                                   "Capacitor_SMD:C_0603_1608Metric", cx1, cy1))
    c1t = pin("C", "1", cx1, cy1)
    c1b = pin("C", "2", cx1, cy1)
    el.append(sexp_wire(c1t[0], c1t[1], y1p[0], y1p[1]))
    gnd(el, c1b[0], c1b[1])

    cx2, cy2 = yx + 12, yy + 15
    el.append(sexp_symbol_instance("inline:C", next_ref("C"), "33pF",
                                   "Capacitor_SMD:C_0603_1608Metric", cx2, cy2))
    c2t = pin("C", "1", cx2, cy2)
    c2b = pin("C", "2", cx2, cy2)
    el.append(sexp_wire(c2t[0], c2t[1], y2p[0], y2p[1]))
    gnd(el, c2b[0], c2b[1])

    # ── Signal connections — labels extend AWAY from MCU body per side ──
    # Left side (pins 1–16): labels go LEFT with generous spacing
    left_signals = [
        ("10", "OSC_IN", "input"), ("11", "OSC_OUT", "output"),
        ("12", "NRST", "input"),
        ("13", "LDO_EN", "output"), ("14", "LED_PWR", "output"),
        ("15", "LED_STS", "output"),
    ]
    for pnum, name, shape in left_signals:
        p = pin("STM32", pnum, mx, my)
        glabel_left(el, p[0], p[1], name, shape, length=10)

    # Bottom side (pins 17–32): FAN OUT — alternate wires left/right to avoid overlap
    # Each pin fans out to a staggered position so labels don't collide.
    bottom_signals = [
        ("17", "ENC1_A", "input"), ("18", "ENC1_B", "input"),
        ("19", "ENC1_SW", "input"), ("20", "ENC2_A", "input"),
        ("21", "DISP_CS", "output"), ("22", "DISP_SCK", "output"),
        ("23", "DISP_VCOM", "output"), ("24", "DISP_MOSI", "output"),
        ("25", "ENC2_B", "input"), ("26", "ENC2_SW", "input"),
        ("27", "VBAT_SENSE", "input"), ("28", "TEMP_SENSE", "input"),
        ("30", "I2C2_SCL", "output"), ("31", "I2C2_SDA", "bidirectional"),
        ("32", "SCL_CS", "output"),
    ]
    # Fan out: each signal gets its own row, wires down then jog to staggered Y
    for idx, (pnum, name, shape) in enumerate(bottom_signals):
        p = pin("STM32", pnum, mx, my)
        # Stagger depth: each label 5.08mm further down than the previous
        drop = 8 + idx * 5.08
        wy = p[1] + drop
        # Wire straight down, then place label going right
        el.append(sexp_wire(p[0], p[1], p[0], wy))
        el.append(sexp_global_label(name, p[0], wy, 0, shape))

    # Right side (pins 33–48): labels go RIGHT with generous spacing
    right_signals = [
        ("33", "SPI2_SCK", "output"), ("34", "SPI2_MISO", "input"),
        ("35", "SPI2_MOSI", "output"), ("36", "DISP_ON", "output"),
        ("37", "CHG_SENSE", "input"),
        ("38", "PCAP1_INT", "input"), ("39", "PCAP2_INT", "input"),
        ("42", "VBUS_SENSE", "input"),
        ("43", "USB_DM", "bidirectional"), ("44", "USB_DP", "bidirectional"),
        ("45", "SWDIO", "bidirectional"), ("46", "SWCLK", "input"),
        ("47", "BLE_RST", "output"), ("48", "BLE_STATUS", "input"),
    ]
    for pnum, name, shape in right_signals:
        p = pin("STM32", pnum, mx, my)
        glabel_right(el, p[0], p[1], name, shape, length=10)

    # Top side (pins 49–64): FAN OUT upward — staggered like bottom
    top_signals = [
        ("49", "PCAP1_RST", "output"), ("50", "PCAP2_RST", "output"),
        ("57", "BUZZER", "output"),
        ("60", "BLE_TX", "output"), ("61", "BLE_RX", "input"),
        ("62", "I2C1_SCL", "output"), ("63", "I2C1_SDA", "bidirectional"),
    ]
    for idx, (pnum, name, shape) in enumerate(top_signals):
        p = pin("STM32", pnum, mx, my)
        # Stagger depth: each label 5.08mm further up
        rise = 8 + idx * 5.08
        wy = p[1] - rise
        el.append(sexp_wire(p[0], p[1], p[0], wy))
        el.append(sexp_global_label(name, p[0], wy, 0, shape))

    content = "\n".join(el)
    lib_text = "\n".join(lib_syms)
    return wrap_schematic(content, title="Microcontroller — STM32G0B1RET6",
                          paper="A3", root_uuid=sheet_uuid, page_num="3",
                          lib_symbols_text=lib_text), sheet_uuid


def generate_display_sheet(root_uuid, sheet_uuid):
    """Page 4: Display — 74AHCT244 level shifter + Sharp LCD connector."""
    global _current_instance_path
    _current_instance_path = f"/{root_uuid}/{sheet_uuid}"
    el = []
    lib_syms = [ALL_POWER_DEFS, ALL_INLINE_DEFS]

    for lib, sym in [("SN74AHCT244DBR", "SN74AHCT244DBR"),
                     ("FH12-10S", "FH12-10S-0.5SH"),
                     ("LS027B7DH01", "LS027B7DH01")]:
        try:
            _, st = get_local_symbol(lib, sym)
            lib_syms.append(st)
        except Exception as e:
            print(f"  Warning: {lib}: {e}")

    # ── 74AHCT244 Level Shifter ──
    el.append(sexp_rect(27, 30, 185, 150))
    el.append(sexp_text("SN74AHCT244 Level Shifter (3.3V to 5V)", 29, 32))

    ax, ay = 100, 88
    el.append(sexp_symbol_instance(
        "local_SN74AHCT244DBR:SN74AHCT244DBR", "U7", "SN74AHCT244DBR",
        "local_SN74AHCT244DBR:SSOP-20_L7.2-W5.3-P0.65-LS7.8-BL", ax, ay,
        label_offset=(0, -15)))

    # Pin connections per Netlist.md
    # Left side (pins 1-10): inputs from MCU (3.3V signals)
    p1 = pin("SN74AHCT244", "1", ax, ay)   # 1OE -> GND
    p2 = pin("SN74AHCT244", "2", ax, ay)   # 1A1 <- DISP_SCK
    p4 = pin("SN74AHCT244", "4", ax, ay)   # 1A2 <- DISP_MOSI
    p6 = pin("SN74AHCT244", "6", ax, ay)   # 1A3 <- DISP_CS
    p8 = pin("SN74AHCT244", "8", ax, ay)   # 1A4 <- DISP_VCOM
    p10 = pin("SN74AHCT244", "10", ax, ay)  # GND

    gnd(el, p1[0], p1[1])   # 1OE always enabled
    gnd(el, p10[0], p10[1])  # GND pin

    glabel_left(el, p2[0], p2[1], "DISP_SCK", "input")
    glabel_left(el, p4[0], p4[1], "DISP_MOSI", "input")
    glabel_left(el, p6[0], p6[1], "DISP_CS", "input")
    glabel_left(el, p8[0], p8[1], "DISP_VCOM", "input")

    # Spare inputs (3, 5, 7) - tie unused to GND (pin 9 is 2OE, handled below)
    for pn in ["3", "5", "7"]:
        pp = pin("SN74AHCT244", pn, ax, ay)
        gnd(el, pp[0], pp[1])

    # Right side (pins 11-20): outputs (5V signals)
    p11 = pin("SN74AHCT244", "11", ax, ay)  # 2A1 <- DISP_ON
    p18 = pin("SN74AHCT244", "18", ax, ay)  # 1Y1 -> DISP_SCK_5V
    p16 = pin("SN74AHCT244", "16", ax, ay)  # 1Y2 -> DISP_MOSI_5V
    p14 = pin("SN74AHCT244", "14", ax, ay)  # 1Y3 -> DISP_CS_5V
    p12 = pin("SN74AHCT244", "12", ax, ay)  # 1Y4 -> DISP_VCOM_5V
    p9_r = pin("SN74AHCT244", "9", ax, ay)  # 2Y1 -> DISP_ON_5V
    p19 = pin("SN74AHCT244", "19", ax, ay)  # 2OE -> GND
    p20 = pin("SN74AHCT244", "20", ax, ay)  # VCC -> +5V

    glabel_left(el, p11[0], p11[1], "DISP_ON", "input")

    pwr5v(el, p20[0], p20[1])
    gnd(el, p19[0], p19[1])  # 2OE always enabled

    label_right(el, p18[0], p18[1], "DISP_SCK_5V")
    label_right(el, p16[0], p16[1], "DISP_MOSI_5V")
    label_right(el, p14[0], p14[1], "DISP_CS_5V")
    label_right(el, p12[0], p12[1], "DISP_VCOM_5V")
    label_right(el, p9_r[0], p9_r[1], "DISP_ON_5V")

    # Spare outputs: pins 13, 15, 17 -> tie inputs to GND already done above
    for pn in ["13", "15", "17"]:
        pp = pin("SN74AHCT244", pn, ax, ay)
        el.append(sexp_no_connect(pp[0], pp[1]))

    # Decoupling 100nF on VCC
    place_bypass_cap(el, ax + 25, ay - 5, next_ref("C"), "100nF", rail="+5V")

    # ── FPC Connector J4 ──
    el.append(sexp_rect(195, 30, 290, 165))
    el.append(sexp_text("J4 — FH12-10S-0.5SH (Display FPC)", 197, 32))

    jx, jy = 240, 90
    el.append(sexp_symbol_instance(
        "local_FH12-10S:FH12-10S-0.5SH", "J4", "FH12-10S-0.5SH",
        "local_FH12-10S:FPC-SMD_FH12-10S-0.5SH-55", jx, jy))

    # Display connector pinout per Netlist.md
    jp = lambda n: pin("FH12_10S", str(n), jx, jy)
    label_left(el, jp(1)[0], jp(1)[1], "DISP_SCK_5V")
    label_left(el, jp(2)[0], jp(2)[1], "DISP_MOSI_5V")
    label_left(el, jp(3)[0], jp(3)[1], "DISP_CS_5V")
    label_left(el, jp(4)[0], jp(4)[1], "DISP_VCOM_5V")
    label_left(el, jp(5)[0], jp(5)[1], "DISP_ON_5V")
    pwr5v(el, jp(6)[0], jp(6)[1])   # EXTMODE tied to +5V
    pwr5v(el, jp(7)[0], jp(7)[1])   # VDD
    gnd(el, jp(8)[0], jp(8)[1])     # VSS
    pwr5v(el, jp(9)[0], jp(9)[1])   # VDDA
    gnd(el, jp(10)[0], jp(10)[1])   # VSSA

    # Display decoupling: 1uF on VDD and VDDA
    place_bypass_cap(el, jx + 15, jy - 5, next_ref("C"), "1uF", rail="+5V")
    place_bypass_cap(el, jx + 15, jy + 10, next_ref("C"), "1uF", rail="+5V")

    content = "\n".join(el)
    return wrap_schematic(content, title="Display — Sharp LS027B7DH01",
                          paper="A4", root_uuid=sheet_uuid, page_num="4",
                          lib_symbols_text="\n".join(lib_syms)), sheet_uuid


def generate_ble_sheet(root_uuid, sheet_uuid):
    """Page 5: Bluetooth — RN4871 module."""
    global _current_instance_path
    _current_instance_path = f"/{root_uuid}/{sheet_uuid}"
    el = []
    lib_syms = [ALL_POWER_DEFS, ALL_INLINE_DEFS]

    try:
        _, rn_sym = get_local_symbol("RN4871", "RN4871-I_RM128")
        lib_syms.append(rn_sym)
    except Exception as e:
        print(f"  Warning: RN4871: {e}")

    el.append(sexp_rect(30, 30, 250, 160))
    el.append(sexp_text("RN4871-I_RM128 Bluetooth Low Energy", 32, 32))

    rx, ry = 140, 90
    el.append(sexp_symbol_instance(
        "local_RN4871:RN4871-I_RM128", "U2", "RN4871-I_RM128",
        "local_RN4871:BULETM-SMD_RN4871-V-RM118", rx, ry,
        label_offset=(0, -13)))

    rp = lambda n: pin("RN4871", str(n), rx, ry)

    # Left pins
    el.append(sexp_no_connect(rp(1)[0], rp(1)[1]))   # NC
    gnd(el, rp(2)[0], rp(2)[1])                        # GND
    el.append(sexp_no_connect(rp(3)[0], rp(3)[1]))   # P1_2 (unused)
    el.append(sexp_no_connect(rp(4)[0], rp(4)[1]))   # P1_3 (unused)
    el.append(sexp_no_connect(rp(5)[0], rp(5)[1]))   # P1_7
    el.append(sexp_no_connect(rp(6)[0], rp(6)[1]))   # P1_6
    glabel_left(el, rp(7)[0], rp(7)[1], "BLE_TX", "input")   # UART_RX <- STM32 TX
    glabel_left(el, rp(8)[0], rp(8)[1], "BLE_RX", "output")  # UART_TX -> STM32 RX

    # Right pins
    el.append(sexp_no_connect(rp(9)[0], rp(9)[1]))    # P3_6
    glabel_right(el, rp(10)[0], rp(10)[1], "BLE_RST", "input")  # RST_N
    glabel_right(el, rp(11)[0], rp(11)[1], "BLE_STATUS", "output")  # P0_0 status
    el.append(sexp_no_connect(rp(12)[0], rp(12)[1]))  # P0_2
    gnd(el, rp(13)[0], rp(13)[1])                      # GND
    pwr33(el, rp(14)[0], rp(14)[1])                    # VBAT -> +3V3
    el.append(sexp_no_connect(rp(15)[0], rp(15)[1]))  # P2_7
    pwr33(el, rp(16)[0], rp(16)[1])                    # P2_0 -> +3V3 (app mode)

    # Decoupling
    place_bypass_cap(el, rx + 28, ry - 5, next_ref("C"), "100nF")
    place_bypass_cap(el, rx + 28, ry + 10, next_ref("C"), "10uF",
                     fp="Capacitor_SMD:C_0805_2012Metric")

    # BLE reset series resistor 100R
    el.append(sexp_text("R_BLE_RST 100R in series on BLE_RST line", 32, 140, 1.27))

    content = "\n".join(el)
    return wrap_schematic(content, title="Bluetooth — RN4871",
                          paper="A4", root_uuid=sheet_uuid, page_num="5",
                          lib_symbols_text="\n".join(lib_syms)), sheet_uuid


def generate_connectors_sheet(root_uuid, sheet_uuid):
    """Page 6: Connectors — USB-C, SWD, FFC daughter boards, expansion."""
    global _current_instance_path
    _current_instance_path = f"/{root_uuid}/{sheet_uuid}"
    el = []
    lib_syms = [ALL_POWER_DEFS, ALL_INLINE_DEFS]

    try:
        _, ftsh_sym = get_local_symbol("FTSH-107", "FTSH-107-01-L-DV-K")
        lib_syms.append(ftsh_sym)
    except Exception as e:
        print(f"  Warning: FTSH-107: {e}")

    # ── USB-C Connector (schematic representation) ──
    el.append(sexp_rect(27, 30, 165, 130))
    el.append(sexp_text("USB-C Connector (J2)", 29, 32))

    el.append(sexp_text("USB-C SMD Receptacle", 35, 48, 1.524))
    el.append(sexp_global_label("VBUS", 50, 60, 0, "output"))
    el.append(sexp_global_label("USB_DP", 50, 68, 0, "bidirectional"))
    el.append(sexp_global_label("USB_DM", 50, 76, 0, "bidirectional"))
    el.append(sexp_global_label("GND", 50, 84, 0, "passive"))

    # CC resistors
    el.append(sexp_text("CC1/CC2: 5.1k to GND", 60, 95, 1.27))
    # USB series resistors
    el.append(sexp_text("22R series on D+/D-", 60, 102, 1.27))

    # VBUS sense
    el.append(sexp_global_label("VBUS_SENSE", 50, 115, 0, "output"))
    el.append(sexp_text("Optional VBUS detect", 60, 122, 1.27))

    # ── SWD Debug Header J3 ──
    el.append(sexp_rect(175, 30, 355, 145))
    el.append(sexp_text("SWD Debug — Samtec FTSH-107 (J3)", 177, 32))

    sx, sy = 260, 85
    el.append(sexp_symbol_instance(
        "local_FTSH-107:FTSH-107-01-L-DV-K", "J3", "FTSH-107-01-L-DV-K",
        "local_FTSH-107:HDR-SMD_14P-P1.27_FTSH-107-01-L-DV-K", sx, sy,
        label_offset=(0, -15)))

    fp = lambda n: pin("FTSH_107", n, sx, sy)

    # STDC14 pinout per spec
    pwr33(el, fp("01")[0], fp("01")[1])                          # Pin 1: VCC
    glabel_left(el, fp("02")[0], fp("02")[1], "SWDIO", "bidirectional")  # Pin 2: SWDIO (via 100R)
    gnd(el, fp("03")[0], fp("03")[1])                            # Pin 3: GND
    glabel_right(el, fp("04")[0], fp("04")[1], "SWCLK", "output")       # Pin 4: SWCLK (via 100R)
    gnd(el, fp("05")[0], fp("05")[1])                            # Pin 5: GND
    el.append(sexp_no_connect(fp("06")[0], fp("06")[1]))        # Pin 6: SWO (NC)
    el.append(sexp_no_connect(fp("07")[0], fp("07")[1]))        # Pin 7: NC
    el.append(sexp_no_connect(fp("08")[0], fp("08")[1]))        # Pin 8: NC
    gnd(el, fp("09")[0], fp("09")[1])                            # Pin 9: GND
    glabel_right(el, fp("10")[0], fp("10")[1], "NRST", "output")       # Pin 10: NRST
    el.append(sexp_no_connect(fp("11")[0], fp("11")[1]))        # Pin 11: NC
    el.append(sexp_no_connect(fp("12")[0], fp("12")[1]))        # Pin 12: NC
    gnd(el, fp("13")[0], fp("13")[1])                            # Pin 13: GND
    gnd(el, fp("14")[0], fp("14")[1])                            # Pin 14: GND

    el.append(sexp_text("100R series on SWDIO/SWCLK", 177, 120, 1.27))
    el.append(sexp_text("10k BOOT0 pull-down on PA14/SWCLK", 177, 127, 1.27))
    el.append(sexp_text("10k pull-up + 100nF on NRST", 177, 134, 1.27))

    # ── FFC Connectors (J5, J6, J7) ──
    el.append(sexp_rect(27, 155, 355, 270))
    el.append(sexp_text("Daughter Board FFC Connectors (6-pin, 1.0mm pitch)", 29, 157))

    # J5 SCL3300
    el.append(sexp_text("J5 — SCL3300 (SPI2)", 35, 172, 1.524))
    spi_labels = [("GND", "passive"), ("+3V3", "input"), ("SPI2_SCK", "output"),
                  ("SPI2_MOSI", "output"), ("SPI2_MISO", "input"), ("SCL_CS", "output")]
    for i, (name, shape) in enumerate(spi_labels):
        y = 185 + i * 7.62
        el.append(sexp_global_label(name, 50, y, 0, shape))
        el.append(sexp_text(f"Pin {i+1}", 35, y, 1.27))

    # J6 PCAP04 #1
    el.append(sexp_text("J6 — PCAP04 #1 (I2C1)", 145, 172, 1.524))
    pcap1_labels = [("I2C1_SDA", "bidirectional"), ("I2C1_SCL", "output"),
                    ("GND", "passive"), ("PCAP1_RST", "output"),
                    ("+3V3", "input"), ("PCAP1_INT", "input")]
    for i, (name, shape) in enumerate(pcap1_labels):
        y = 185 + i * 7.62
        el.append(sexp_global_label(name, 160, y, 0, shape))
        el.append(sexp_text(f"Pin {i+1}", 145, y, 1.27))

    # J7 PCAP04 #2
    el.append(sexp_text("J7 — PCAP04 #2 (I2C2)", 255, 172, 1.524))
    pcap2_labels = [("I2C2_SDA", "bidirectional"), ("I2C2_SCL", "output"),
                    ("GND", "passive"), ("PCAP2_RST", "output"),
                    ("+3V3", "input"), ("PCAP2_INT", "input")]
    for i, (name, shape) in enumerate(pcap2_labels):
        y = 185 + i * 7.62
        el.append(sexp_global_label(name, 270, y, 0, shape))
        el.append(sexp_text(f"Pin {i+1}", 255, y, 1.27))

    content = "\n".join(el)
    return wrap_schematic(content, title="Connectors",
                          paper="A3", root_uuid=sheet_uuid, page_num="6",
                          lib_symbols_text="\n".join(lib_syms)), sheet_uuid


def generate_ui_sheet(root_uuid, sheet_uuid):
    """Page 7: UI — Encoders, 74HC14, LEDs, buzzer, EEPROM, LM35."""
    global _current_instance_path
    _current_instance_path = f"/{root_uuid}/{sheet_uuid}"
    el = []
    lib_syms = [ALL_POWER_DEFS, ALL_INLINE_DEFS]

    for lib, sym in [("SN74HC14", "SN74HC14PWR"),
                     ("24LC256", "24LC256-I_ST"),
                     ("CPT-9019A", "CPT-9019A-SMT-TR")]:
        try:
            _, st = get_local_symbol(lib, sym)
            lib_syms.append(st)
        except Exception as e:
            print(f"  Warning: {lib}: {e}")

    # ── 74HC14 Schmitt Trigger ──
    el.append(sexp_rect(27, 30, 205, 160))
    el.append(sexp_text("SN74HC14 Schmitt Trigger + Encoder Debounce", 29, 32))

    hx, hy = 110, 90
    el.append(sexp_symbol_instance(
        "local_SN74HC14:SN74HC14PWR", "U8", "SN74HC14PWR",
        "local_SN74HC14:TSSOP-14_L5.0-W4.4-P0.65-LS6.4-BL", hx, hy,
        label_offset=(0, -12)))

    hp = lambda n: pin("SN74HC14", str(n), hx, hy)

    # Encoder signal flow: raw -> RC filter -> 74HC14 input -> inverted output -> MCU
    # Left pins 1,3,5 = inputs A; 2,4,6 = outputs Y (inverted)
    # Right pins 9,11,13 = inputs A; 8,10,12 = outputs Y
    label_left(el, hp(1)[0], hp(1)[1], "ENC1_A_RAW")
    glabel_right(el, hp(2)[0], hp(2)[1], "ENC1_A", "output", 12)
    label_left(el, hp(3)[0], hp(3)[1], "ENC1_B_RAW")
    glabel_right(el, hp(4)[0], hp(4)[1], "ENC1_B", "output", 12)
    label_left(el, hp(5)[0], hp(5)[1], "ENC1_SW_RAW")
    glabel_right(el, hp(6)[0], hp(6)[1], "ENC1_SW", "output", 12)
    gnd(el, hp(7)[0], hp(7)[1])  # GND

    glabel_left(el, hp(8)[0], hp(8)[1], "ENC2_A", "output")     # 4Y
    label_right(el, hp(9)[0], hp(9)[1], "ENC2_A_RAW")          # 4A
    glabel_left(el, hp(10)[0], hp(10)[1], "ENC2_B", "output")   # 5Y
    label_right(el, hp(11)[0], hp(11)[1], "ENC2_B_RAW")        # 5A
    glabel_left(el, hp(12)[0], hp(12)[1], "ENC2_SW", "output")  # 6Y
    label_right(el, hp(13)[0], hp(13)[1], "ENC2_SW_RAW")       # 6A
    pwr33(el, hp(14)[0], hp(14)[1])  # VCC

    place_bypass_cap(el, hx + 22, hy, next_ref("C"), "100nF")

    el.append(sexp_text("RC debounce: 10k + 10nF per line (6x)", 29, 145, 1.27))
    el.append(sexp_text("Note: 74HC14 inverts all signals", 29, 152, 1.27))

    # ── LEDs ──
    el.append(sexp_rect(215, 30, 335, 100))
    el.append(sexp_text("Status LEDs", 217, 32))

    # LED1 Green Power
    el.append(sexp_text("LED1 Green (Power)", 220, 45, 1.27))
    ld1x, ld1y = 260, 58
    place_resistor(el, ld1x, ld1y, next_ref("R"), "330R")
    r1t = pin("R", "1", ld1x, ld1y)
    r1b = pin("R", "2", ld1x, ld1y)
    glabel_left(el, r1t[0], r1t[1], "LED_PWR", "input", 10)
    el.append(sexp_symbol_instance("inline:LED", next_ref("D"), "Green",
                                   "LED_SMD:LED_0603_1608Metric", ld1x, ld1y + 10))
    la = pin("LED", "1", ld1x, ld1y + 10)
    lk = pin("LED", "2", ld1x, ld1y + 10)
    el.append(sexp_wire(r1b[0], r1b[1], la[0], la[1]))
    gnd(el, lk[0], lk[1])

    # LED2 Blue Status
    el.append(sexp_text("LED2 Blue (Status)", 220, 78, 1.27))
    ld2x, ld2y = 305, 58
    place_resistor(el, ld2x, ld2y, next_ref("R"), "330R")
    r2t = pin("R", "1", ld2x, ld2y)
    r2b = pin("R", "2", ld2x, ld2y)
    glabel_left(el, r2t[0], r2t[1], "LED_STS", "input", 10)
    el.append(sexp_symbol_instance("inline:LED", next_ref("D"), "Blue",
                                   "LED_SMD:LED_0603_1608Metric", ld2x, ld2y + 10))
    la2 = pin("LED", "1", ld2x, ld2y + 10)
    lk2 = pin("LED", "2", ld2x, ld2y + 10)
    el.append(sexp_wire(r2b[0], r2b[1], la2[0], la2[1]))
    gnd(el, lk2[0], lk2[1])

    # ── Buzzer ──
    el.append(sexp_rect(215, 105, 335, 160))
    el.append(sexp_text("Piezo Buzzer (BZ1)", 217, 107))

    bx, by = 275, 132
    el.append(sexp_symbol_instance(
        "local_CPT-9019A:CPT-9019A-SMT-TR", "BZ1", "CPT-9019A",
        "local_CPT-9019A:BUZ-SMD_L9.0-W9.0_CPT-9019A-SMT-TR", bx, by))

    bp1 = pin("CPT_9019A", "1", bx, by)
    bp2 = pin("CPT_9019A", "2", bx, by)
    glabel_left(el, bp1[0], bp1[1], "BUZZER", "input")
    gnd(el, bp2[0], bp2[1])
    el.append(sexp_text("PWM 4kHz from TIM1_CH2 (PB3)", 217, 152, 1.27))

    # ── EEPROM ──
    el.append(sexp_rect(27, 170, 195, 270))
    el.append(sexp_text("24LC256 EEPROM (U9)", 29, 172))

    ex, ey = 110, 215
    el.append(sexp_symbol_instance(
        "local_24LC256:24LC256-I_ST", "U9", "24LC256-I_ST",
        "local_24LC256:TSSOP-8_L4.4-W3.0-P0.65-LS6.4-BL", ex, ey,
        label_offset=(12, -8)))

    ep = lambda n: pin("24LC256", str(n), ex, ey)
    # A0, A1, A2 -> GND (address 0x50)
    gnd(el, ep(1)[0], ep(1)[1])
    gnd(el, ep(2)[0], ep(2)[1])
    gnd(el, ep(3)[0], ep(3)[1])
    # VCC
    pwr33(el, ep(8)[0], ep(8)[1])
    # VSS
    gnd(el, ep(4)[0], ep(4)[1])
    # SDA, SCL -> I2C1 bus
    glabel_right(el, ep(5)[0], ep(5)[1], "I2C1_SDA", "bidirectional")
    glabel_right(el, ep(6)[0], ep(6)[1], "I2C1_SCL", "input")
    # WP -> GND (write enabled)
    gnd(el, ep(7)[0], ep(7)[1])

    place_bypass_cap(el, ex - 22, ey, next_ref("C"), "100nF")

    # ── Temperature Sensor LM35 ──
    el.append(sexp_rect(215, 170, 335, 270))
    el.append(sexp_text("LM35 Temperature Sensor", 217, 172))

    lmx, lmy = 255, 200
    el.append(sexp_symbol_instance(
        "inline:LM35", "U11", "LM35DGS",
        "Package_TO_SOT_SMD:SOT-23", lmx, lmy))

    # Pin 1 (VS+) → +3V3
    lm_vdd = pin("LM35", "1", lmx, lmy)
    pwr33(el, lm_vdd[0], lm_vdd[1])
    # Pin 3 (GND) → GND
    lm_gnd = pin("LM35", "3", lmx, lmy)
    gnd(el, lm_gnd[0], lm_gnd[1])
    # Pin 2 (VOUT) → R_TEMP 100R → C_TEMP 10nF → TEMP_SENSE global label
    lm_out = pin("LM35", "2", lmx, lmy)
    # Series resistor R_TEMP
    rt_ref = next_ref("R")
    rtx, rty = lmx + 20, lmy
    place_resistor(el, rtx, rty, rt_ref, "100R")
    rt_top = pin("R", "1", rtx, rty)
    rt_bot = pin("R", "2", rtx, rty)
    el.append(sexp_wire(lm_out[0], lm_out[1], rt_top[0], rt_top[1]))
    # Filter cap C_TEMP (from R output to GND)
    ct_ref = next_ref("C")
    ctx, cty = rtx + 7, rty + 5
    place_bypass_cap(el, ctx, cty, ct_ref, "10nF")
    # Wire from R bottom to junction, then to cap and to TEMP_SENSE label
    jx, jy = rt_bot[0], rt_bot[1]
    el.append(sexp_wire(jx, jy, ctx, jy))
    el.append(sexp_junction(ctx, jy))
    glabel_right(el, jx, jy, "TEMP_SENSE", "output")

    content = "\n".join(el)
    return wrap_schematic(content, title="User Interface & Peripherals",
                          paper="A3", root_uuid=sheet_uuid, page_num="7",
                          lib_symbols_text="\n".join(lib_syms)), sheet_uuid


def generate_root_sheet(sheet_uuids):
    """Page 1: Root sheet with hierarchical sub-sheet references.

    sheet_uuids: dict mapping sheet name to pre-generated UUID, e.g.
        {"power": "abc...", "mcu": "def...", ...}
    """
    root_uuid = uid()
    el = []

    el.append(sexp_text("Precision Electronic Level Instrument", 76.2, 30))
    el.append(sexp_text("Main Board Schematic — Hierarchical Overview", 76.2, 38, 1.524))

    sheets_def = [
        ("Power Supply", "power.kicad_sch", 30, 60, 65, 30, "2", "power"),
        ("MCU — STM32G0B1", "mcu.kicad_sch", 115, 60, 65, 30, "3", "mcu"),
        ("Display", "display.kicad_sch", 200, 60, 65, 30, "4", "display"),
        ("Bluetooth", "ble.kicad_sch", 30, 110, 65, 30, "5", "ble"),
        ("Connectors", "connectors.kicad_sch", 115, 110, 65, 30, "6", "connectors"),
        ("UI & Peripherals", "ui.kicad_sch", 200, 110, 65, 30, "7", "ui"),
    ]

    sheet_instances = ""
    for name, filename, x, y, w, h, page, key in sheets_def:
        s_uuid = sheet_uuids[key]
        sexp, _ = sexp_sheet(name, filename, x, y, w, h, page,
                             root_uuid=root_uuid, sheet_uuid=s_uuid)
        el.append(sexp)
        sheet_instances += f'\t\t(path "/{root_uuid}/{s_uuid}"\n\t\t\t(page "{page}")\n\t\t)\n'

    content = "\n".join(el)
    return wrap_schematic(content, title="Precision Electronic Level Instrument",
                          paper="A4", root_uuid=root_uuid, page_num="1",
                          lib_symbols_text="",
                          sheet_instances_extra=sheet_instances), root_uuid


# ═══════════════════════════════════════════════════════════════════════════
# PROJECT FILES
# ═══════════════════════════════════════════════════════════════════════════

def generate_project_file():
    return json.dumps({
        "board": {"design_settings": {"defaults": {
            "board_outline_line_width": 0.1, "copper_line_width": 0.2,
            "copper_text_size_h": 1.5, "copper_text_size_v": 1.5,
            "copper_text_thickness": 0.3, "silk_line_width": 0.15,
            "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
        }}},
        "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
        "meta": {"filename": f"{PROJECT_NAME}.kicad_pro", "version": 3},
        "net_settings": {"classes": [{
            "bus_width": 12, "clearance": 0.2, "name": "Default",
            "track_width": 0.2, "via_diameter": 0.6, "via_drill": 0.3,
        }]},
        "schematic": {"drawing": {
            "default_line_thickness": 6.0, "default_text_size": 50.0,
            "intersheets_ref_show": True,
        }},
    }, indent=2)


def generate_sym_lib_table():
    local_libs = [
        "24LC256", "CPT-9019A", "DMG2305UX", "DW01A", "FH12-10S",
        "FS8205A", "FTSH-107", "LP5907", "LS027B7DH01", "RN4871",
        "SD6210A", "SN74AHCT244DBR", "SN74HC14", "TP4056", "X50328MSB2GI",
    ]
    entries = []
    for lib in local_libs:
        entries.append(
            f'  (lib (name "local_{lib}")(type "KiCad")'
            f'(uri "${{KIPRJMOD}}/../Libraries/KiCad/{lib}.kicad_sym")'
            f'(options "")(descr "JLCPCB library for {lib}"))'
        )
    return f"(sym_lib_table\n  (version 7)\n" + "\n".join(entries) + "\n)\n"


def generate_fp_lib_table():
    local_libs = [
        "24LC256", "CPT-9019A", "DMG2305UX", "DW01A", "FH12-10S",
        "FS8205A", "FTSH-107", "LP5907", "LS027B7DH01", "RN4871",
        "SD6210A", "SN74AHCT244DBR", "SN74HC14", "TP4056", "X50328MSB2GI",
    ]
    entries = []
    for lib in local_libs:
        entries.append(
            f'  (lib (name "local_{lib}")(type "KiCad")'
            f'(uri "${{KIPRJMOD}}/../Libraries/KiCad/{lib}.pretty")'
            f'(options "")(descr "JLCPCB footprint for {lib}"))'
        )
    return f"(fp_lib_table\n  (version 7)\n" + "\n".join(entries) + "\n)\n"


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    global _current_instance_path
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    print("Generating KiCad project files...")

    # Reset counters
    _pwr_counter[0] = 0
    _ref_counters.clear()

    # Pre-generate sheet UUIDs so root and sub-sheets use the same ones
    sheet_uuids = {
        "power": uid(), "mcu": uid(), "display": uid(),
        "ble": uid(), "connectors": uid(), "ui": uid(),
    }

    root_sch, root_uuid = generate_root_sheet(sheet_uuids)

    # Generate sub-sheets, passing the coordinated UUIDs
    sheets = {}
    for name, gen_fn in [
        ("power", generate_power_sheet),
        ("mcu", generate_mcu_sheet),
        ("display", generate_display_sheet),
        ("ble", generate_ble_sheet),
        ("connectors", generate_connectors_sheet),
        ("ui", generate_ui_sheet),
    ]:
        _pwr_counter[0] = 0  # reset per sheet
        try:
            sch, _ = gen_fn(root_uuid, sheet_uuids[name])
            sheets[name] = sch
            print(f"  Generated: {name}.kicad_sch")
        except Exception as e:
            print(f"  ERROR generating {name}: {e}")
            import traceback
            traceback.print_exc()
    _current_instance_path = ""  # reset

    files = {
        f"{PROJECT_NAME}.kicad_sch": root_sch,
        f"{PROJECT_NAME}.kicad_pro": generate_project_file(),
        "sym-lib-table": generate_sym_lib_table(),
        "fp-lib-table": generate_fp_lib_table(),
    }
    files.update({f"{k}.kicad_sch": v for k, v in sheets.items()})

    for filename, content in files.items():
        filepath = PROJECT_DIR / filename
        filepath.write_text(content, encoding="utf-8")
        print(f"  Written: {filepath}")

    print(f"\nProject generated at: {PROJECT_DIR}")
    print(f"Open {PROJECT_DIR / PROJECT_NAME}.kicad_pro in KiCad 10")


if __name__ == "__main__":
    main()
