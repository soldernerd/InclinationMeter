#!/usr/bin/env python3
"""fix_property_visibility.py — Re-hide property fields that kiutils lost
when it round-tripped the schematic files.

Problem: KiCad 10 encodes "hide this property on the schematic" as a
property-level `(hide yes)` s-expression, but the version of kiutils we
use only recognizes the `hide` keyword when it appears inside `(effects ...)`
— it silently drops the property-level form. So every time a script read
and re-wrote a sheet, the hide flags on Footprint, Datasheet, Manufacturer,
MPN, LCSC, etc. were lost, leaving them visible and overlapping.

Fix: walk every schematic symbol instance and every libSymbol, and force
`effects.hide = True` on every property whose key is NOT in the visible
whitelist (Reference, Value). kiutils serialises `effects.hide=True` as
`(effects (font ...) hide)`, which KiCad 10 accepts.

Safe to run multiple times.
"""

from pathlib import Path
from kiutils.schematic import Schematic
from kiutils.items.common import Effects, Font
from kiutils.utils import sexpr

ROOT = Path(__file__).parent / "KiCad"
VISIBLE_DEFAULT = {"Reference", "Value"}
# On power symbols (GND, +3V3, VBAT, ...) only Value should show; the auto-
# generated #PWRxxx Reference is noise.
VISIBLE_POWER = {"Value"}


def read_sch(p):
    with open(p, encoding="utf-8") as f:
        return Schematic.from_sexpr(sexpr.parse_sexp(f.read()))


def write_sch(s, p):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s.to_sexpr())


def force_hide(prop) -> bool:
    """Set hide=True on a property; return True if this actually changed it."""
    if prop.effects is None:
        prop.effects = Effects(hide=True, font=Font(width=1.27, height=1.27))
        return True
    if not prop.effects.hide:
        prop.effects.hide = True
        return True
    return False


def ensure_hidden(prop, visible_keys):
    if prop.key in visible_keys:
        return False
    return force_hide(prop)


def kill_show_name(prop) -> bool:
    """Turn off showName so KiCad renders 'R6' instead of 'Reference: R6'.

    kiutils has a parsing bug where any 'show_name' token (including
    the KiCad 10 'show_name no' form) is read as showName=True. We clear
    it explicitly — kiutils omits the token entirely on write, and KiCad
    defaults to not displaying the property name in that case.
    """
    if getattr(prop, "showName", False):
        prop.showName = False
        return True
    return False


def fix(path: Path) -> None:
    s = read_sch(path)
    changed = 0

    # Component and power-symbol instances
    for sy in s.schematicSymbols:
        visible = VISIBLE_POWER if sy.libId.startswith("power:") else VISIBLE_DEFAULT
        for prop in sy.properties:
            if ensure_hidden(prop, visible):
                changed += 1
            if kill_show_name(prop):
                changed += 1

    # libSymbols (so future kiutils round-trips don't silently un-hide again)
    for ls in s.libSymbols:
        visible = VISIBLE_POWER if ls.libId.startswith("power:") else VISIBLE_DEFAULT
        for prop in ls.properties:
            if ensure_hidden(prop, visible):
                changed += 1
            if kill_show_name(prop):
                changed += 1

    # Global labels: hide the auto-generated Intersheetrefs / Intersheetref
    # helper properties so the literal "${INTERSHEET_REFS}" doesn't render.
    for gl in s.globalLabels:
        for prop in getattr(gl, "properties", None) or []:
            if prop.key in ("Intersheetrefs", "Intersheetref"):
                if force_hide(prop):
                    changed += 1
            if kill_show_name(prop):
                changed += 1

    if changed:
        write_sch(s, path)
    print(f"  {path.name}: hid {changed} property field(s)")


def main():
    print("Hiding non-essential property fields on every instance...")
    for sch in sorted(ROOT.glob("*.kicad_sch")):
        if sch.name == "InclinationMeter.kicad_sch":
            continue  # root has no component instances
        fix(sch)
    print("Done. Reopen InclinationMeter.kicad_pro in KiCad.")


if __name__ == "__main__":
    main()
