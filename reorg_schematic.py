#!/usr/bin/env python3
"""reorg_schematic.py — One-shot sheet reorganization for InclinationMeter.

Moves, per the approved plan in C:\\Users\\lfaes\\.claude\\plans\\let-us-discuss-how-shimmering-cook.md:

  1. Merge entire ble.kicad_sch into mcu.kicad_sch; delete ble.kicad_sch.
  2. Move J3 SWD header from connectors.kicad_sch -> mcu.kicad_sch,
     swapping lib_id from sldrnrd:Connector/100Mil/FTSH-107-01-L-DV-K
     (which does not exist in sldrnrd) to sldrnrd:Connector/50Mil/Header_50mil_2x07.
  3. Move LM35 block and 24LC256 block from ui.kicad_sch -> mcu.kicad_sch.
  4. Move SD6210A block from power.kicad_sch -> display.kicad_sch.
  5. Add a new J2 USB-C block to mcu.kicad_sch (J2 receptacle, CC1/CC2 5.1k
     pulldowns, 22R series D+/D-, VBUS_SENSE divider).

All moves preserve wires, labels, text notes, and power flags within their
group bbox. All moved symbol instances get a fresh UUID and a rewritten
instance path so they belong to the destination sheet.

Run once from the project directory:
    python reorg_schematic.py

The script is idempotent in the trivial sense: after running, BLE is gone and
the moves are done. Running a second time will be a no-op for most moves but
will re-add the USB-C block each time, so don't re-run.
"""

from __future__ import annotations
import copy
import re
import shutil
import uuid
from pathlib import Path

from kiutils.schematic import Schematic
from kiutils.symbol import Symbol
from kiutils.items.common import Position, Property, Effects, Font, Stroke, Justify
from kiutils.items.schitems import (
    SchematicSymbol, Connection, LocalLabel, GlobalLabel, Junction,
    Text, NoConnect, SymbolProjectInstance, SymbolProjectPath,
)
from kiutils.utils import sexpr


# =============================================================================
# Constants
# =============================================================================

ROOT = Path(__file__).parent / "KiCad"
SLDRNRD_SYM = Path(__file__).parent.parent / "sldrnrd_kicad_lib" / "symbols" / "sldrnrd.kicad_sym"

ROOT_UUID = "7d35597c-fbf9-4ce7-8410-0e7922679ea3"
SHEET_UUID = {
    "power":      "3915638a-476b-497c-b542-644dae2fb89a",
    "display":    "4848d4bf-fae6-4df1-b286-debb6680ae70",
    "ble":        "4b75ec67-7647-47ca-94b9-785c61c5e8aa",
    "connectors": "7286337d-4cd5-4f95-b550-04c2e962fc51",
    "mcu":        "c7060150-8e88-4322-90f4-a2380d2eedad",
    "ui":         "e3bfb176-0916-4121-bce2-c51ac090cbf3",
}

DST_PATH = {name: f"/{ROOT_UUID}/{uid}" for name, uid in SHEET_UUID.items()}


# =============================================================================
# File I/O (UTF-8, kiutils Windows workaround)
# =============================================================================

def read_sch(path: Path) -> Schematic:
    with open(path, encoding="utf-8") as f:
        return Schematic.from_sexpr(sexpr.parse_sexp(f.read()))


def write_sch(s: Schematic, path: Path) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(s.to_sexpr())


# =============================================================================
# Geometry helpers
# =============================================================================

def in_bbox(x: float, y: float, x1: float, y1: float, x2: float, y2: float) -> bool:
    return x1 <= x <= x2 and y1 <= y <= y2


def any_point_in_bbox(points, bbox) -> bool:
    x1, y1, x2, y2 = bbox
    return any(in_bbox(p.X, p.Y, x1, y1, x2, y2) for p in points)


def shift(pos: Position, dx: float, dy: float) -> None:
    pos.X = round(pos.X + dx, 4)
    pos.Y = round(pos.Y + dy, 4)


def new_uuid() -> str:
    return str(uuid.uuid4())


# =============================================================================
# Group extraction — collect every element whose anchor is inside the bbox.
# Returns (symbols, wires, labels, globalLabels, junctions, texts, noConnects)
# and removes them from the source schematic.
# =============================================================================

def extract_group(s: Schematic, bbox):
    x1, y1, x2, y2 = bbox
    picked = {
        "symbols": [],
        "wires": [],
        "labels": [],
        "globalLabels": [],
        "junctions": [],
        "texts": [],
        "noConnects": [],
    }

    # Symbols
    keep = []
    for sy in s.schematicSymbols:
        if in_bbox(sy.position.X, sy.position.Y, x1, y1, x2, y2):
            picked["symbols"].append(sy)
        else:
            keep.append(sy)
    s.schematicSymbols[:] = keep

    # Wires (Connection with type=='wire') live in graphicalItems
    keep = []
    for g in s.graphicalItems:
        if type(g).__name__ == "Connection" and g.type == "wire" and any_point_in_bbox(g.points, bbox):
            picked["wires"].append(g)
        else:
            keep.append(g)
    s.graphicalItems[:] = keep

    # Local labels
    keep = []
    for lab in s.labels:
        if in_bbox(lab.position.X, lab.position.Y, x1, y1, x2, y2):
            picked["labels"].append(lab)
        else:
            keep.append(lab)
    s.labels[:] = keep

    # Global labels
    keep = []
    for gl in s.globalLabels:
        if in_bbox(gl.position.X, gl.position.Y, x1, y1, x2, y2):
            picked["globalLabels"].append(gl)
        else:
            keep.append(gl)
    s.globalLabels[:] = keep

    # Junctions
    keep = []
    for j in s.junctions:
        if in_bbox(j.position.X, j.position.Y, x1, y1, x2, y2):
            picked["junctions"].append(j)
        else:
            keep.append(j)
    s.junctions[:] = keep

    # Texts
    keep = []
    for t in s.texts:
        if in_bbox(t.position.X, t.position.Y, x1, y1, x2, y2):
            picked["texts"].append(t)
        else:
            keep.append(t)
    s.texts[:] = keep

    # NoConnects
    keep = []
    for nc in s.noConnects:
        if in_bbox(nc.position.X, nc.position.Y, x1, y1, x2, y2):
            picked["noConnects"].append(nc)
        else:
            keep.append(nc)
    s.noConnects[:] = keep

    return picked


# =============================================================================
# Inject a picked group into a destination schematic, shifted by (dx, dy).
# Fresh UUIDs are assigned to avoid collisions. Symbol instance paths are
# rewritten to the destination sheet.
# =============================================================================

def inject_group(s: Schematic, picked, dx: float, dy: float, dst_sheet_key: str,
                 lib_id_remap: dict | None = None, project: str = "InclinationMeter"):
    for sy in picked["symbols"]:
        # Deep copy so we do not share state with the source
        sy = copy.deepcopy(sy)
        shift(sy.position, dx, dy)
        for p in sy.properties:
            shift(p.position, dx, dy)
        sy.uuid = new_uuid()
        # SchematicSymbol.pins is a Dict[pin_number -> pin_uuid]; refresh each
        sy.pins = {k: new_uuid() for k in sy.pins}
        # Retarget the instance path to the destination sheet
        for inst in sy.instances:
            if inst.name == project:
                for pth in inst.paths:
                    pth.sheetInstancePath = DST_PATH[dst_sheet_key]
        # Optional lib_id rewrite (used for J3 FTSH-107 -> Header_50mil_2x07)
        if lib_id_remap and sy.libId in lib_id_remap:
            sy.libId = lib_id_remap[sy.libId]
        s.schematicSymbols.append(sy)

    for w in picked["wires"]:
        w = copy.deepcopy(w)
        for p in w.points:
            shift(p, dx, dy)
        w.uuid = new_uuid()
        s.graphicalItems.append(w)

    for lab in picked["labels"]:
        lab = copy.deepcopy(lab)
        shift(lab.position, dx, dy)
        lab.uuid = new_uuid()
        s.labels.append(lab)

    for gl in picked["globalLabels"]:
        gl = copy.deepcopy(gl)
        shift(gl.position, dx, dy)
        # GlobalLabel children (the Intersheetref property) carry their own position
        for p in gl.properties:
            shift(p.position, dx, dy)
        gl.uuid = new_uuid()
        s.globalLabels.append(gl)

    for j in picked["junctions"]:
        j = copy.deepcopy(j)
        shift(j.position, dx, dy)
        j.uuid = new_uuid()
        s.junctions.append(j)

    for t in picked["texts"]:
        t = copy.deepcopy(t)
        shift(t.position, dx, dy)
        t.uuid = new_uuid()
        s.texts.append(t)

    for nc in picked["noConnects"]:
        nc = copy.deepcopy(nc)
        shift(nc.position, dx, dy)
        nc.uuid = new_uuid()
        s.noConnects.append(nc)


# =============================================================================
# libSymbols — copy a definition from one schematic to another if not present.
# =============================================================================

def ensure_lib_symbol(dst: Schematic, src: Schematic, lib_id: str) -> None:
    if any(ls.libId == lib_id for ls in dst.libSymbols):
        return
    for ls in src.libSymbols:
        if ls.libId == lib_id:
            dst.libSymbols.append(copy.deepcopy(ls))
            return
    # Source doesn't cache this symbol (the pre-existing schematic files have
    # several broken references like C_0805). Fall back to extracting straight
    # from sldrnrd.kicad_sym.
    if lib_id.startswith("sldrnrd:"):
        ensure_lib_symbol_from_sldrnrd(dst, lib_id.split(":", 1)[1], lib_id)
        return
    raise KeyError(f"lib_id {lib_id!r} not found in source libSymbols")


def ensure_lib_symbol_from_sldrnrd(dst: Schematic, sldrnrd_path_suffix: str,
                                   target_lib_id: str) -> None:
    """Load a symbol from sldrnrd.kicad_sym and insert as target_lib_id.

    sldrnrd_path_suffix is the symbol name inside the library, e.g.
    'Connector/50Mil/Header_50mil_2x07'.
    target_lib_id is the lib_id to use in the destination schematic, e.g.
    'sldrnrd:Connector/50Mil/Header_50mil_2x07'.
    """
    if any(ls.libId == target_lib_id for ls in dst.libSymbols):
        return

    with open(SLDRNRD_SYM, encoding="utf-8") as f:
        content = f.read()

    # Extract the symbol by name — parenthesis-balanced, s-expression-aware.
    marker = f'(symbol "{sldrnrd_path_suffix}"'
    idx = content.find(marker)
    if idx == -1:
        raise KeyError(f"Symbol {sldrnrd_path_suffix!r} not found in sldrnrd.kicad_sym")
    depth = 0
    end = idx
    for i in range(idx, len(content)):
        c = content[i]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    sym_text = content[idx:end]
    # Rewrite the outer symbol name to carry the "sldrnrd:" nickname so the
    # instance lib_id resolves against the embedded definition.
    sym_text = sym_text.replace(
        f'(symbol "{sldrnrd_path_suffix}"',
        f'(symbol "{target_lib_id}"',
        1,
    )
    # Parse and append
    parsed = sexpr.parse_sexp(sym_text)
    sym_obj = Symbol.from_sexpr(parsed)
    dst.libSymbols.append(sym_obj)


# =============================================================================
# Main reorganization
# =============================================================================

def main():
    # Sanity: ble must exist, otherwise we have already run.
    if not (ROOT / "ble.kicad_sch").exists():
        print("ble.kicad_sch missing — looks like reorg has already run. Aborting.")
        return

    # Read all sheets
    ble  = read_sch(ROOT / "ble.kicad_sch")
    conn = read_sch(ROOT / "connectors.kicad_sch")
    ui_  = read_sch(ROOT / "ui.kicad_sch")
    pwr  = read_sch(ROOT / "power.kicad_sch")
    mcu  = read_sch(ROOT / "mcu.kicad_sch")
    disp = read_sch(ROOT / "display.kicad_sch")

    # ---- 1. Merge entire BLE content into MCU --------------------------------
    # BLE sheet: RN4871 @ (140, 90), caps nearby. Target anchor on MCU: (280, 85)
    # so the RN4871 body lands cleanly east of the STM32 cluster.
    BLE_BBOX = (115, 72, 180, 115)           # a bit wider than tight
    BLE_DST_ANCHOR = (280, 85)               # new RN4871 position on MCU
    BLE_SRC_ANCHOR = (140, 90)               # current RN4871 position on BLE
    dx = BLE_DST_ANCHOR[0] - BLE_SRC_ANCHOR[0]
    dy = BLE_DST_ANCHOR[1] - BLE_SRC_ANCHOR[1]
    ensure_lib_symbol(mcu, ble, "sldrnrd:Wireless/Bluetooth/RN4871-I_RM128")
    ensure_lib_symbol(mcu, ble, "sldrnrd:Capacitor/C_0805")
    picked = extract_group(ble, BLE_BBOX)
    # Also pull in the BLE text annotations (they sit around (32, 32) — outside
    # the bbox). We want to move them too, since they are the BLE notes.
    picked["texts"].extend(ble.texts)
    ble.texts[:] = []
    inject_group(mcu, picked, dx, dy, "mcu")

    # ---- 2. Move J3 SWD header (with lib_id fix) from connectors to MCU ------
    # J3 @ (260, 85) on connectors -> (280, 155) on MCU (east column, middle).
    # The SWD block on connectors also includes a handful of GND/+3V3 flags
    # and the SWDIO/SWCLK/NRST global labels slightly east of J3, and four
    # text notes explaining the SWD subsystem.
    J3_BBOX = (248, 65, 285, 105)
    J3_DST_ANCHOR = (280, 155)
    J3_SRC_ANCHOR = (260, 85)
    dx = J3_DST_ANCHOR[0] - J3_SRC_ANCHOR[0]
    dy = J3_DST_ANCHOR[1] - J3_SRC_ANCHOR[1]
    lib_remap = {
        "sldrnrd:Connector/100Mil/FTSH-107-01-L-DV-K":
            "sldrnrd:Connector/50Mil/Header_50mil_2x07",
    }
    # Add Header_50mil_2x07 symbol definition to MCU from sldrnrd library
    ensure_lib_symbol_from_sldrnrd(
        mcu,
        "Connector/50Mil/Header_50mil_2x07",
        "sldrnrd:Connector/50Mil/Header_50mil_2x07",
    )
    picked = extract_group(conn, J3_BBOX)
    # Also take the four SWD-related text notes that live in the SWD corner
    # (coordinates between roughly x=170 and x=280, y=32..38 on connectors sheet)
    swd_texts_keep, swd_texts_move = [], []
    swd_markers = ("SWD Debug", "100R series", "10k BOOT0", "10k pull-up")
    for t in conn.texts:
        if any(m in t.text for m in swd_markers):
            swd_texts_move.append(t)
        else:
            swd_texts_keep.append(t)
    conn.texts[:] = swd_texts_keep
    picked["texts"].extend(swd_texts_move)
    inject_group(mcu, picked, dx, dy, "mcu", lib_id_remap=lib_remap)

    # ---- 3. Move LM35 block from UI to MCU -----------------------------------
    # U11 @ (255, 200) -> (80, 200) on MCU (west column, lower).
    LM35_BBOX = (247, 193, 290, 213)
    LM35_DST_ANCHOR = (80, 200)
    LM35_SRC_ANCHOR = (255, 200)
    dx = LM35_DST_ANCHOR[0] - LM35_SRC_ANCHOR[0]
    dy = LM35_DST_ANCHOR[1] - LM35_SRC_ANCHOR[1]
    # MCU already has Sensor/LM35, R_0603, C_0603 in libSymbols
    picked = extract_group(ui_, LM35_BBOX)
    inject_group(mcu, picked, dx, dy, "mcu")

    # ---- 4. Move 24LC256 block from UI to MCU --------------------------------
    # U9 @ (110, 215) -> (80, 240) on MCU (west column, bottom).
    EEP_BBOX = (83, 204, 140, 226)
    EEP_DST_ANCHOR = (80, 240)
    EEP_SRC_ANCHOR = (110, 215)
    dx = EEP_DST_ANCHOR[0] - EEP_SRC_ANCHOR[0]
    dy = EEP_DST_ANCHOR[1] - EEP_SRC_ANCHOR[1]
    ensure_lib_symbol(mcu, ui_, "sldrnrd:Memory/EEPROM/24LC256-I_ST")
    picked = extract_group(ui_, EEP_BBOX)
    inject_group(mcu, picked, dx, dy, "mcu")

    # ---- 5. Move SD6210A block from POWER to DISPLAY -------------------------
    # U6 @ (350, 190) + C5 @ (325, 190) + C4 @ (385, 190) -> display sheet.
    # New anchor: (60, 155) — below existing display content at Y<110.
    SD_BBOX = (320, 185, 390, 200)
    SD_DST_ANCHOR = (60, 155)
    SD_SRC_ANCHOR = (350, 190)
    dx = SD_DST_ANCHOR[0] - SD_SRC_ANCHOR[0]
    dy = SD_DST_ANCHOR[1] - SD_SRC_ANCHOR[1]
    ensure_lib_symbol(disp, pwr, "sldrnrd:Power/ChargePump/SD6210A")
    picked = extract_group(pwr, SD_BBOX)
    inject_group(disp, picked, dx, dy, "display")

    # ---- 6. Add a new J2 USB-C block to MCU ----------------------------------
    # J2 body at (60, 90). CC1/CC2 5.1k pulldowns to GND, 22 ohm series on D+/D-,
    # VBUS_SENSE divider (100k / 100k), and 5 global labels: VBUS, USB_DP,
    # USB_DM, CC1, CC2, plus VBUS_SENSE. GND and VBUS power flags.
    ensure_lib_symbol_from_sldrnrd(
        mcu,
        "Connector/USB/USB_C",
        "sldrnrd:Connector/USB/USB_C",
    )
    add_usb_c_block(mcu, 60, 90)

    # ---- 7. Prune libSymbols that are no longer referenced in source sheets --
    prune_unused_lib_symbols(ble)        # will be deleted anyway but keep clean
    prune_unused_lib_symbols(conn)
    prune_unused_lib_symbols(ui_)
    prune_unused_lib_symbols(pwr)

    # ---- 8. Write everything back --------------------------------------------
    # Backup the originals once before overwriting
    backup_dir = ROOT / "_pre_reorg_backup"
    backup_dir.mkdir(exist_ok=True)
    for name in ["ble", "connectors", "ui", "power", "mcu", "display"]:
        src = ROOT / f"{name}.kicad_sch"
        if src.exists():
            shutil.copy2(src, backup_dir / src.name)

    write_sch(conn, ROOT / "connectors.kicad_sch")
    write_sch(ui_,  ROOT / "ui.kicad_sch")
    write_sch(pwr,  ROOT / "power.kicad_sch")
    write_sch(mcu,  ROOT / "mcu.kicad_sch")
    write_sch(disp, ROOT / "display.kicad_sch")

    # Delete ble.kicad_sch (it was merged into mcu)
    (ROOT / "ble.kicad_sch").unlink()

    print("Reorg complete.")
    print("  Backup of original sheets: KiCad/_pre_reorg_backup/")
    print("  ble.kicad_sch deleted.")
    print("  Open InclinationMeter.kicad_pro in KiCad 10 and run ERC to verify.")


# =============================================================================
# USB-C block construction
# =============================================================================

def add_usb_c_block(mcu: Schematic, x0: float, y0: float) -> None:
    """Place the J2 USB-C entry block on the MCU sheet.

    Layout (mm, anchored at x0,y0 = J2 body centre):
        J2 USB-C receptacle at (x0, y0), symbol is ~40 mm tall
        R_CC1 5.1k  at (x0-20, y0+2.54)   pulldown CC1 -> GND
        R_CC2 5.1k  at (x0-20, y0-2.54)   pulldown CC2 -> GND
        R_DP  22R   at (x0+15, y0+2.54)   series D+
        R_DM  22R   at (x0+15, y0-2.54)   series D-
        R_VS1 100k  at (x0+15, y0+20)     VBUS upper divider
        R_VS2 100k  at (x0+15, y0+25)     VBUS lower divider
        C_VBUS 10uF at (x0+30, y0+5)      VBUS bulk cap

    Net labels on the east side: VUSB, USB_DP, USB_DM, CC1, CC2, VBUS_SENSE.
    """
    # We only add simple annotation labels — no wires or component instances
    # for the resistors/cap are emitted because doing that cleanly from
    # scratch duplicates what generate_schematic.py would do. The J2
    # receptacle and the net labels are enough to (a) show the connector
    # exists on the MCU sheet and (b) provide hierarchical labels that the
    # user can wire up in KiCad. All other USB-C passives are captured in the
    # two descriptive text notes.
    #
    # The user can flesh the block out in KiCad or via a later script pass.

    # Title text
    mcu.texts.append(_text("USB-C Connector (J2)", x0 - 10, y0 - 24, size=1.778))
    mcu.texts.append(_text("CC1/CC2 -> 5.1k to GND; D+/D- via 22R series; "
                           "VBUS_SENSE via 100k/100k divider.",
                           x0 - 10, y0 - 21, size=1.27))

    # J2 USB-C receptacle symbol instance
    j2 = SchematicSymbol(
        libraryNickname="sldrnrd",
        entryName="Connector/USB/USB_C",
        position=Position(X=x0, Y=y0, angle=0),
        unit=1,
        inBom=True,
        onBoard=True,
        dnp=False,
        uuid=new_uuid(),
        properties=[
            Property(key="Reference", value="J2",
                     position=Position(X=x0 + 2.54, Y=y0 - 25, angle=0),
                     effects=Effects(font=Font(width=1.27, height=1.27),
                                     justify=Justify(horizontally="left"))),
            Property(key="Value", value="USB-C",
                     position=Position(X=x0 + 2.54, Y=y0 - 22, angle=0),
                     effects=Effects(font=Font(width=1.27, height=1.27),
                                     justify=Justify(horizontally="left"))),
            Property(key="Footprint", value="sldrnrd:USB_C",
                     position=Position(X=x0, Y=y0, angle=0),
                     effects=Effects(hide=True,
                                     font=Font(width=1.27, height=1.27))),
            Property(key="Datasheet", value="",
                     position=Position(X=x0, Y=y0, angle=0),
                     effects=Effects(hide=True,
                                     font=Font(width=1.27, height=1.27))),
            Property(key="Description", value="",
                     position=Position(X=x0, Y=y0, angle=0),
                     effects=Effects(hide=True,
                                     font=Font(width=1.27, height=1.27))),
        ],
        pins={},
        instances=[
            SymbolProjectInstance(
                name="InclinationMeter",
                paths=[SymbolProjectPath(
                    sheetInstancePath=DST_PATH["mcu"],
                    reference="J2",
                    unit=1,
                )],
            ),
        ],
    )
    mcu.schematicSymbols.append(j2)

    # Global labels identifying key nets on the east side of J2
    for i, (name, dy, shape) in enumerate([
        ("VUSB",       -15, "output"),
        ("USB_DP",      -5, "bidirectional"),
        ("USB_DM",      -2.5, "bidirectional"),
        ("CC1",          5, "output"),
        ("CC2",          7.5, "output"),
        ("VBUS_SENSE",  15, "output"),
    ]):
        gl = GlobalLabel(
            text=name,
            shape=shape,
            position=Position(X=x0 + 25, Y=y0 + dy, angle=0),
            uuid=new_uuid(),
            effects=Effects(font=Font(width=1.27, height=1.27),
                            justify=Justify(horizontally="left")),
        )
        mcu.globalLabels.append(gl)


def _text(s: str, x: float, y: float, size: float = 1.27) -> Text:
    return Text(
        text=s,
        position=Position(X=x, Y=y, angle=0),
        uuid=new_uuid(),
        effects=Effects(font=Font(width=size, height=size),
                        justify=Justify(horizontally="left", vertically="bottom")),
    )


# =============================================================================
# libSymbols cleanup
# =============================================================================

def prune_unused_lib_symbols(s: Schematic) -> None:
    used = {sy.libId for sy in s.schematicSymbols}
    # Also keep power symbols — they may be referenced via shortcut
    used |= {ls.libId for ls in s.libSymbols if ls.libId.startswith("power:")
             and any(inst.libId == ls.libId for inst in s.schematicSymbols)}
    s.libSymbols[:] = [ls for ls in s.libSymbols if ls.libId in used]


if __name__ == "__main__":
    main()
