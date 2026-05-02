#!/usr/bin/env python3
"""refresh_lib_symbols.py — Rebuild each sheet's cached (lib_symbols ...)
block by re-fetching every sldrnrd:* symbol fresh from sldrnrd.kicad_sym.

Motivation: the pre-reorg schematic files contained malformed cached
library symbol definitions — the inner unit symbols were named bare
(e.g. 'C_0_1') instead of prefixed with the parent's library name
(e.g. 'Capacitor/C_0603_0_1'). KiCad 10's schematic parser rejects this
with 'Invalid symbol unit name prefix'. KiCad CLI (ERC) happened to be
more permissive and so did not catch it.

This script leaves 'power:*' symbols alone (they come from KiCad's
built-in lib and any cached copy KiCad wrote is valid by construction)
and replaces every 'sldrnrd:*' cached definition with a fresh extract.

Run once after the reorg; safe to re-run.
"""

from pathlib import Path
from kiutils.schematic import Schematic
from kiutils.symbol import Symbol
from kiutils.utils import sexpr

ROOT = Path(__file__).parent / "KiCad"
SLDRNRD_SYM = Path(__file__).parent.parent / "sldrnrd_kicad_lib" / "symbols" / "sldrnrd.kicad_sym"


def read_sch(p):
    with open(p, encoding="utf-8") as f:
        return Schematic.from_sexpr(sexpr.parse_sexp(f.read()))


def write_sch(s, p):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s.to_sexpr())


def extract_sldrnrd_symbol(suffix: str, target_lib_id: str) -> Symbol:
    """Extract the (symbol "<suffix>" ...) block from sldrnrd.kicad_sym and
    rewrite the OUTER name to target_lib_id.

    Inner unit-symbol names must be of the form '<suffix>_<unit>_<style>'
    per KiCad 10's schematic parser. The sldrnrd library is inconsistent —
    most symbols use the full prefix (e.g. 'Capacitor/C_0603_0_1'), but
    some (USB_C, LS027B7DH01, Header_FFC_1.0mm_06, Header_100mil_1x07,
    PEC11R-4215F-S0024, PCAP04) use a short prefix that KiCad 10 rejects.
    We normalize every child unit name in the embedded copy so it matches
    the parent.
    """
    import re
    content = SLDRNRD_SYM.read_text(encoding="utf-8")
    marker = f'(symbol "{suffix}"'
    i = content.find(marker)
    if i < 0:
        raise KeyError(f"{suffix!r} not found in sldrnrd.kicad_sym")
    depth, end = 0, i
    for j in range(i, len(content)):
        c = content[j]
        if c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                end = j + 1
                break
    sym_text = content[i:end]

    # 1) rewrite the outer name to the full target lib_id
    sym_text = sym_text.replace(
        f'(symbol "{suffix}"', f'(symbol "{target_lib_id}"', 1,
    )

    # 2) normalize every inner unit symbol name to '<suffix>_<unit>_<style>'.
    #    The outer was already rewritten to include the 'sldrnrd:' nickname
    #    and does not end in '_<int>_<int>', so the regex won't match it.
    unit_re = re.compile(r'\(symbol "([^"]+?)_(\d+)_(\d+)"')
    def _fix(m):
        _, unit, style = m.group(1), m.group(2), m.group(3)
        return f'(symbol "{suffix}_{unit}_{style}"'
    sym_text = unit_re.sub(_fix, sym_text)

    return Symbol.from_sexpr(sexpr.parse_sexp(sym_text))


def refresh(path: Path) -> None:
    s = read_sch(path)
    used = {sy.libId for sy in s.schematicSymbols}
    new_lib = []
    refreshed = dropped = 0
    for ls in s.libSymbols:
        if ls.libId.startswith("sldrnrd:"):
            suffix = ls.libId.split(":", 1)[1]
            fresh = extract_sldrnrd_symbol(suffix, ls.libId)
            new_lib.append(fresh)
            refreshed += 1
        elif ls.libId.startswith("power:"):
            new_lib.append(ls)  # built-in, always OK
        elif ls.libId in used:
            new_lib.append(ls)  # non-sldrnrd, non-power but actively used
        else:
            dropped += 1  # unused zombie (e.g. local_* leftovers)
    s.libSymbols[:] = new_lib
    write_sch(s, path)
    print(f"  {path.name}: refreshed {refreshed}, dropped {dropped} unused, "
          f"kept {len(new_lib) - refreshed} built-in/referenced")


def main():
    print("Refreshing cached sldrnrd lib_symbols in every sheet...")
    for sch in sorted(ROOT.glob("*.kicad_sch")):
        if sch.name == "InclinationMeter.kicad_sch":
            continue  # root has no lib_symbols
        refresh(sch)
    print("Done. Try opening InclinationMeter.kicad_pro again.")


if __name__ == "__main__":
    main()
