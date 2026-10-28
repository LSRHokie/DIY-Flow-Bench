"""verify.py - independent check of the generated KiCad files.

Parses each .kicad_sch with kiutils (not the generator's own data), rebuilds
connectivity from pin positions, wires, labels and no-connect flags, and compares
it with netlist.csv. Run from hardware/kicad:  python3 tools/verify.py
"""
import csv, glob, sys
from kiutils.schematic import Schematic


def r(v):
    return round(v, 3)


ok = True
for proj in ['flowbench-main', 'flowbench-power-module']:
    expected = {}
    for row in csv.DictReader(open('%s/netlist.csv' % proj)):
        expected.setdefault(row['net'], set()).add((row['ref'], row['pin']))
    got, unconnected = {}, []
    for fn in glob.glob('%s/*.kicad_sch' % proj):
        s = Schematic.from_file(fn)
        pinpos = {}
        for inst in s.schematicSymbols:
            lib = [l for l in s.libSymbols if l.libId == inst.libId][0]
            ref = [p.value for p in inst.properties if p.key == 'Reference'][0]
            for unit in lib.units:
                if unit.unitId in (0, inst.unit):
                    for p in unit.pins:
                        pos = (r(inst.position.X + p.position.X), r(inst.position.Y - p.position.Y))
                        pinpos.setdefault(pos, []).append((ref, p.number))
        parent = {}

        def find(a):
            while parent.get(a, a) != a:
                a = parent[a]
            return a
        for w in s.graphicalItems:
            if getattr(w, 'type', '') == 'wire':
                a = (r(w.points[0].X), r(w.points[0].Y)); b = (r(w.points[1].X), r(w.points[1].Y))
                parent[find(a)] = find(b)
        names = {}
        for lab in list(s.labels) + list(s.globalLabels):
            names.setdefault(find((r(lab.position.X), r(lab.position.Y))), set()).add(lab.text)
        ncs = {(r(n.position.X), r(n.position.Y)) for n in s.noConnects}
        def off(v):
            return abs(v / 1.27 - round(v / 1.27)) > 1e-3
        for pos in pinpos:
            if off(pos[0]) or off(pos[1]):
                print('  pin off the 1.27 mm grid', fn, pos, pinpos[pos]); ok = False
        for w in s.graphicalItems:
            if getattr(w, 'type', '') == 'wire' and any(off(pt.X) or off(pt.Y) for pt in w.points):
                print('  wire end off the 1.27 mm grid', fn, [(pt.X, pt.Y) for pt in w.points]); ok = False
        for pos, pins in pinpos.items():
            k = find(pos)
            if k in names:
                if len(names[k]) != 1:
                    print('  two labels on one wire', fn, names[k]); ok = False
                for pin in pins:
                    got.setdefault(next(iter(names[k])), set()).add(pin)
            elif pos not in ncs:
                unconnected.append((fn, pos, pins))
    match = got == expected
    ok = ok and match and not unconnected
    print('%s: %s, %d nets, %d unconnected pins' % (proj, 'connectivity matches the design' if match else 'MISMATCH',
                                                    len(got), len(unconnected)))
sys.exit(0 if ok else 1)
