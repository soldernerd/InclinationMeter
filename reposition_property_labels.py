#!/usr/bin/env python3
"""reposition_property_labels.py — Move Reference above and Value below each
component body so the two visible labels stop stacking on top of each
other (and on top of neighbor components' labels).

The old generator placed both labels side-by-side 2.54 mm to the upper-
right of every component. With tightly-packed passives the visible labels
all piled up. Separating them vertically (Ref at Y-7.62, Val at Y+7.62)
gives every instance its own band of text space above/below the body and
keeps neighbor instances' text from colliding.

No wires, junctions, or pins are touched — only the two visible property
positions per instance. Non-visible properties (Footprint, Datasheet, …)
are left where they are; they render nothing.

Safe to run multiple times; idempotent.
"""

from pathlib import Path

from kiutils.schematic import Schematic
from kiutils.items.common import Position
from kiutils.utils import sexpr

ROOT = Path(__file__).parent / "KiCad"

# Offsets from component body to label anchor, in mm
REF_OFFSET = (0.0, -7.62)    # 6 grid units above
VAL_OFFSET = (0.0,  7.62)    # 6 grid units below


def read_sch(p):
    with open(p, encoding="utf-8") as f:
        return Schematic.from_sexpr(sexpr.parse_sexp(f.read()))


def write_sch(s, p):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s.to_sexpr())


def reposition(path: Path) -> None:
    s = read_sch(path)
    touched = 0
    for sy in s.schematicSymbols:
        # Skip power symbols — Reference is hidden (ugly "#PWR001"), and the
        # Value anchor points straight up at the power flag shape, which is
        # the intended KiCad convention. Leave alone.
        if sy.libId.startswith("power:"):
            continue
        bx, by = sy.position.X, sy.position.Y
        for prop in sy.properties:
            if prop.key == "Reference":
                prop.position = Position(X=round(bx + REF_OFFSET[0], 3),
                                         Y=round(by + REF_OFFSET[1], 3),
                                         angle=0)
                touched += 1
            elif prop.key == "Value":
                prop.position = Position(X=round(bx + VAL_OFFSET[0], 3),
                                         Y=round(by + VAL_OFFSET[1], 3),
                                         angle=0)
                touched += 1
    write_sch(s, path)
    print(f"  {path.name}: repositioned {touched} Reference/Value labels")


def main():
    print("Repositioning Reference above / Value below each component body...")
    for sch in sorted(ROOT.glob("*.kicad_sch")):
        if sch.name == "InclinationMeter.kicad_sch":
            continue
        reposition(sch)
    print("Done. Reopen the project to see the result.")


if __name__ == "__main__":
    main()
