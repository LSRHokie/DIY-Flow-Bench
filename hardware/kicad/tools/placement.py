"""placement.py - writes place_rev_a.py, a KiCad scripting-console script that lays out
the main board for rev A: outline, mounting holes, edge connectors, ICs and modules
at planned spots, and every passive packed next to the part it serves.

Board: 220 x 160 mm, origin at the top-left corner, y down (KiCad convention).
  Top edge:    24 V input, stepper power and signals, coils, lamp, E-stop
  Bottom edge: MAF, current sensors, swirl, Digimatic, BME280, switches, orifice
  Left edge:   DevKit antenna overhangs it
  Right edge:  WIZ850io RJ45 faces it; ABP2 ports face it
"""
import json
import re

W, H = 220.0, 160.0
POWER_NETS = {'GND', '+3V3', '+5V', '+12V', '+24V', '+24V_RAW', '+5VA', '+24V_FIELD', 'SDA', 'SCL'}

# value (or Function field) -> (x, y, rotation, edge). For edge connectors x is the left
# end of the connector and y is ignored: the script pushes it against the edge.
PLAN = [
    # top edge
    ('24V IN', 14, 0, 0, 'top'),
    ('Bleed stepper 24 V (GX12-2)', 32, 0, 0, 'top'),
    ('Lift stepper 24 V (GX12-2)', 50, 0, 0, 'top'),
    ('Bleed stepper signals (GX16-8)', 68, 0, 0, 'top'),
    ('Lift stepper signals (GX16-8)', 104, 0, 0, 'top'),
    ('Motor housing coils (GX16-8)', 140, 0, 0, 'top'),
    ('Motors-armed lamp', 176, 0, 0, 'top'),
    ('E-stop (2 NC contacts)', 188, 0, 0, 'top'),
    # bottom edge
    ('MAF (GX12-7)', 14, 0, 0, 'bottom'),
    ('Motor current sensors (GX16-8)', 44, 0, 0, 'bottom'),
    ('Swirl encoder (GX12-5)', 78, 0, 0, 'bottom'),
    ('Digimatic indicator (GX12-4)', 100, 0, 0, 'bottom'),
    ('BME280 (GX12-4)', 118, 0, 0, 'bottom'),
    ('Bleed home switch (GX12-3)', 136, 0, 0, 'bottom'),
    ('Lift switches (GX12-4)', 150, 0, 0, 'bottom'),
    ('Orifice selector (GX12-5)', 168, 0, 0, 'bottom'),
    # power block (top left); PM1 plugs in above its sockets
    ('PM1 power socket', 10, 24, 90, None),
    ('PM1 signal socket', 10, 46, 90, None),
    ('D24V22F5 (5 V 2.5 A)', 52, 22, 0, None),
    ('D24V22F12 (12 V 2.2 A)', 52, 44, 0, None),
    ('LM1117-3.3', 34, 60, 0, None),
    # stepper drivers, coil driver and watchdog (under the top connectors)
    ('AM26C31 (bleed stepper)', 82, 30, 0, None),
    ('AM26C31 (lift stepper)', 116, 30, 0, None),
    ('TBD62083AFWG', 152, 30, 0, None),
    ('74HCT123', 188, 32, 0, None),
    # controller: pin 1 at the left, antenna overhanging the left edge
    ('ESP32-S3-DevKitC-1-N32R8V', 6, 98, 90, None),
    ('microSD push-push', 72, 104, 0, None),
    # Ethernet: RJ45 toward the right edge
    ('WIZ850io', 205, 56, 270, None),
    # expanders and optocouplers (middle)
    ('TCA9535PWR #1 (0x20)', 92, 62, 0, None),
    ('TCA9535PWR #2 (0x21)', 124, 62, 0, None),
    ('Expander 2 spare', 146, 50, 90, None),
    ('TLP291-4#1', 88, 86, 0, None),
    ('TLP291-4#2', 108, 86, 0, None),
    ('TLP291-4#3', 128, 86, 0, None),
    # I2C mux and pressure sensors (ports toward the right edge)
    ('TCA9548APWR', 154, 74, 0, None),
    ('Reference pressure', 178, 92, 0, None),
    ('Orifice pressure', 178, 110, 0, None),
    ('Pitot pressure', 178, 128, 0, None),
    # analog and field interfaces (above the bottom connectors)
    ('ADS1219 #1 (0x40)', 24, 118, 0, None),
    ('ADS1219 #2 (0x41)', 52, 118, 0, None),
    ('MCP6002', 60, 136, 0, None),
    ('74LVC14 (5 V-tolerant inputs)', 86, 124, 0, None),
    ('ATtiny1616-SN', 110, 120, 0, None),
    ('UPDI', 128, 134, 90, None),
    # mounting holes
    ('M3 mounting hole#1', 5, 5, 0, None),
    ('M3 mounting hole#2', W - 5, 5, 0, None),
    ('M3 mounting hole#3', 5, H - 5, 0, None),
    ('M3 mounting hole#4', W - 5, H - 5, 0, None),
]


def build(project):
    """Return (anchors, passives) for the main-board project."""
    parts = [(sh, p) for sh in project.sheets for p in sh.parts if p.footprint]
    keyed, counts = {}, {}
    for sh, p in parts:
        k = p.fields.get('Function') if p.sym.name == 'ABP2_I2C' else p.value
        if k in counts or any(k == q[0].split('#')[0] for q in PLAN if '#' in q[0]):
            counts[k] = counts.get(k, 0) + 1
            k = '%s#%d' % (k, counts[k])
        keyed[k] = p
    anchors = {}
    for key, x, y, rot, edge in PLAN:
        if key not in keyed:
            raise KeyError('placement plan names a part that does not exist: %s' % key)
        anchors[keyed[key].ref] = [x, y, rot, edge]
    anchor_parts = {p.ref: p for _, p in parts if p.ref in anchors}
    unplaced = [p.ref for _, p in parts if not re.match(r'^(R|C|D|Q|F|JP|TP)\d', p.ref) and p.ref not in anchors]
    if unplaced:
        raise KeyError('no placement planned for %s' % unplaced)

    def nets(p):
        return {n for n in p.nets.values() if n and n not in POWER_NETS}

    passives = []
    order = [p for _, p in parts]
    for i, (sh, p) in enumerate(parts):
        if p.ref in anchors:
            continue
        mine = nets(p)
        best, score = None, 0
        sheet_of = {q.ref: shq.name for shq, q in parts}
        for a in anchor_parts.values():
            s = len(mine & nets(a))
            if s and sheet_of[a.ref] == sh.name:
                s += 0.5                      # ties go to a part on the same schematic sheet
            if s > score:
                best, score = a, s
        if best is None:      # follows a part through another passive, or decoupling: nearest anchor before it
            for q in reversed(order[:i]):
                if q.ref in anchors:
                    best = q
                    break
        if best is None:
            best = next(q for q in order[i:] if q.ref in anchors)
        passives.append([p.ref, best.ref])
    # a passive that shares no signal net with any anchor (for example the gate resistors
    # in a transistor stage) follows another passive it connects to that does.
    by_ref = {p.ref: p for p in order}
    direct = {r: a for r, a in passives if nets(by_ref[r]) & nets(anchor_parts[a])}
    for item in passives:
        if item[0] in direct:
            continue
        for r2, a2 in direct.items():
            if nets(by_ref[item[0]]) & nets(by_ref[r2]):
                item[1] = a2
                break
    passives.sort(key=lambda r: (list(anchors).index(r[1]), r[0]))
    return anchors, passives


SCRIPT = r'''"""place_rev_a.py - DIY Flow Bench V2 main board, rev A starting placement.

Run in KiCad's PCB editor after Update PCB from Schematic:
    Tools -> Scripting Console, then
    exec(open(r"<path to this file>").read())

It draws the 220 x 160 mm outline (only if the board has none), puts the edge
connectors against the edges with their plugs facing out, places ICs and modules at
planned spots, and packs every resistor, capacitor and small part next to the part
it connects to, at least 1 mm apart. Nothing is routed. Run it once on a fresh board;
re-running moves everything back to these spots.
"""
import pcbnew

W, H = %(W)s, %(H)s
ANCHORS = %(anchors)s
PASSIVES = %(passives)s
GAP = 1.0        # mm between part outlines
MARGIN = 2.0     # mm from the board edge

B = pcbnew.GetBoard()
mm, tomm = pcbnew.FromMM, pcbnew.ToMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


def bbox(fp):
    for args in ((False, False), (False,), ()):
        try:
            b = fp.GetBoundingBox(*args)
            break
        except TypeError:
            continue
    return [tomm(b.GetLeft()), tomm(b.GetTop()), tomm(b.GetRight()), tomm(b.GetBottom())]


def move(fp, x, y):
    fp.SetPosition(V(x, y))


def shift(fp, dx, dy):
    p = fp.GetPosition()
    move(fp, tomm(p.x) + dx, tomm(p.y) + dy)


def pad_centre(fp):
    ps = list(fp.Pads())
    return (sum(tomm(p.GetPosition().x) for p in ps) / len(ps), sum(tomm(p.GetPosition().y) for p in ps) / len(ps))


placed = []


def free(r, ignore_edges=False):
    x0, y0, x1, y1 = r
    if not ignore_edges and (x0 < MARGIN or y0 < MARGIN or x1 > W - MARGIN or y1 > H - MARGIN):
        return False
    for a in placed:
        if not (x1 + GAP <= a[0] or x0 >= a[2] + GAP or y1 + GAP <= a[1] or y0 >= a[3] + GAP):
            return False
    return True


missing = []
# outline
if not any(d.GetLayer() == pcbnew.Edge_Cuts for d in B.GetDrawings()):
    r = pcbnew.PCB_SHAPE(B)
    r.SetShape(pcbnew.SHAPE_T_RECT)
    r.SetStart(V(0, 0))
    r.SetEnd(V(W, H))
    r.SetLayer(pcbnew.Edge_Cuts)
    try:
        r.SetWidth(mm(0.1))
    except Exception:
        pass
    B.Add(r)

# anchors: modules, ICs, connectors, holes
for ref, (x, y, rot, edge) in ANCHORS.items():
    fp = B.FindFootprintByReference(ref)
    if fp is None:
        missing.append(ref)
        continue
    fp.SetOrientationDegrees(rot)
    move(fp, x, y)
    if edge:
        # the connector body (plug side) must face the edge: compare body centre with pad centre
        b = bbox(fp)
        cy = (b[1] + b[3]) / 2
        px, py = pad_centre(fp)
        if (edge == 'top' and cy > py) or (edge == 'bottom' and cy < py):
            fp.SetOrientationDegrees(rot + 180)
        b = bbox(fp)
        dx = x - b[0]
        dy = (0.5 - b[1]) if edge == 'top' else (H - 0.5 - b[3])
        shift(fp, dx, dy)
    placed.append(bbox(fp))

# passives: nearest free spot around their anchor, spiralling outward
for ref, anchor in PASSIVES:
    fp = B.FindFootprintByReference(ref)
    a = B.FindFootprintByReference(anchor)
    if fp is None or a is None:
        missing.append(ref)
        continue
    fp.SetOrientationDegrees(0)
    ab = bbox(a)
    move(fp, 0, 0)
    pb = bbox(fp)
    w, h = pb[2] - pb[0], pb[3] - pb[1]
    ox, oy = -pb[0], -pb[1]             # footprint origin offset inside its own box
    done = False
    d = GAP
    while not done and d < 60:
        x0, y0, x1, y1 = ab[0] - d - w, ab[1] - d - h, ab[2] + d, ab[3] + d
        cands = []
        step = 1.27
        x = x0
        while x <= x1:                  # below, then above
            cands += [(x, y1), (x, y0)]
            x += step
        y = y0
        while y <= y1:                  # right, then left
            cands += [(x1, y), (x0, y)]
            y += step
        cands.sort(key=lambda c: abs(c[0] + w / 2 - (ab[0] + ab[2]) / 2) + abs(c[1] + h / 2 - (ab[1] + ab[3]) / 2))
        for cx, cy in cands:
            r = [cx, cy, cx + w, cy + h]
            if free(r):
                move(fp, cx + ox, cy + oy)
                placed.append(bbox(fp))
                done = True
                break
        d += 1.27
    if not done:
        missing.append(ref + ' (no room)')

pcbnew.Refresh()
print('Placed %%d anchors and %%d passives.' %% (len(ANCHORS), len(PASSIVES)))
if missing:
    print('Not placed:', ', '.join(missing))
'''


def write(project, path):
    anchors, passives = build(project)
    with open(path, 'w') as fh:
        fh.write(SCRIPT % {'W': W, 'H': H, 'anchors': json.dumps(anchors, indent=1).replace('null', 'None'),
                           'passives': json.dumps(passives)})
    return anchors, passives
