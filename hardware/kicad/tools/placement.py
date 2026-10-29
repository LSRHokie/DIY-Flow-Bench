"""placement.py - writes place_rev_a.py, a KiCad scripting-console script that lays out
the main board for rev A: outline, mounting holes, edge connectors, ICs and modules
at planned spots, and every passive packed next to the part it serves.

Board: 180 x 125 mm, origin at the top-left corner, y down (KiCad convention).
  Top edge:    24 V input, stepper power and signals, coils
  Right edge:  lamp, E-stop; WIZ850io RJ45 and ABP2 ports face it
  Bottom edge: MAF, current sensors, swirl, Digimatic, BME280, bleed home switch
  Left edge:   orifice selector, lift switches; DevKit antenna overhangs it
"""
import json
import re

W, H = 180.0, 125.0
POWER_NETS = {'GND', '+3V3', '+5V', '+12V', '+24V', '+24V_RAW', '+5VA', '+24V_FIELD', 'SDA', 'SCL'}
DEVKIT_PIN1 = (6, 88)          # DevKit rotated 90: antenna band at the left edge, y about 61 to 90

# value (or Function field) -> (x, y, rotation, edge). For edge connectors the script pushes
# the part against that edge with its plug facing out; x (top/bottom) or y (left/right) is
# where the connector starts along the edge, and the other coordinate is ignored.
PLAN = [
    # top edge: 24 V and actuators
    ('24V IN', 13, 0, 0, 'top'),
    ('Bleed stepper 24 V (GX12-2)', 27, 0, 0, 'top'),
    ('Lift stepper 24 V (GX12-2)', 41, 0, 0, 'top'),
    ('Bleed stepper signals (GX16-8)', 55, 0, 0, 'top'),
    ('Lift stepper signals (GX16-8)', 90, 0, 0, 'top'),
    ('Motor housing coils (GX16-8)', 125, 0, 0, 'top'),
    # right edge: lamp and E-stop above the RJ45 and pressure ports
    ('Motors-armed lamp', 0, 13, 90, 'right'),
    ('E-stop (2 NC contacts)', 0, 26, 90, 'right'),
    # left edge: switch inputs above the DevKit antenna
    ('Orifice selector (GX12-5)', 0, 13, 90, 'left'),
    ('Lift switches (GX12-4)', 0, 37, 90, 'left'),
    # bottom edge: sensors
    ('MAF (GX12-7)', 13, 0, 0, 'bottom'),
    ('Motor current sensors (GX16-8)', 45, 0, 0, 'bottom'),
    ('Swirl encoder (GX12-5)', 80, 0, 0, 'bottom'),
    ('Digimatic indicator (GX12-4)', 104, 0, 0, 'bottom'),
    ('BME280 (GX12-4)', 124, 0, 0, 'bottom'),
    ('Bleed home switch (GX12-3)', 144, 0, 0, 'bottom'),
    # power block (top left); PM1 plugs in above its sockets
    ('PM1 power socket', 13, 17, 90, None),
    ('PM1 signal socket', 13, 31, 90, None),
    ('D24V22F5 (5 V 2.5 A)', 48, 15, 0, None),
    ('D24V22F12 (12 V 2.2 A)', 70, 15, 0, None),
    ('LM1117-3.3', 32, 42, 0, None),
    # stepper drivers, coil driver, watchdog (under the top connectors)
    ('AM26C31 (bleed stepper)', 99, 26, 0, None),
    ('AM26C31 (lift stepper)', 116, 26, 0, None),
    ('TBD62083AFWG', 136, 27, 0, None),
    ('74HCT123', 157, 26, 0, None),
    # controller and storage
    ('ESP32-S3-DevKitC-1-N32R8V', DEVKIT_PIN1[0], DEVKIT_PIN1[1], 90, None),
    ('microSD push-push', 70, 85, 0, None),
    ('WIZ850io', 167, 46, 270, None),
    # expanders and optocouplers
    ('TCA9535PWR #1 (0x20)', 80, 48, 0, None),
    ('TCA9535PWR #2 (0x21)', 102, 48, 0, None),
    ('TLP291-4#1', 76, 68, 0, None),
    ('TLP291-4#2', 94, 68, 0, None),
    ('TLP291-4#3', 112, 68, 0, None),
    # I2C mux and pressure sensors (ports toward the right edge)
    ('TCA9548APWR', 132, 70, 0, None),
    ('Reference pressure', 150, 70, 0, None),
    ('Orifice pressure', 150, 84, 0, None),
    ('Pitot pressure', 150, 98, 0, None),
    # analog and field interfaces (above the bottom connectors)
    ('ADS1219 #1 (0x40)', 18, 100, 0, None),
    ('ADS1219 #2 (0x41)', 36, 100, 0, None),
    ('MCP6002', 53, 102, 0, None),
    ('74LVC14 (5 V-tolerant inputs)', 92, 99, 0, None),
    ('ATtiny1616-SN', 113, 99, 0, None),
    ('UPDI', 129, 103, 90, None),
    # test-point areas, grouped by purpose and voltage
    ('+24V_RAW', 116, 43, 0, None), ('+24V', 122.35, 43, 0, None), ('BLEED_24V_F', 128.7, 43, 0, None),
    ('LIFT_24V_F', 135.05, 43, 0, None), ('COIL_24V_ESTOP', 141.4, 43, 0, None), ('+24V_FIELD', 147.75, 43, 0, None),
    ('GND#1', 147.75, 49.35, 0, None),
    ('+12V', 15, 56, 0, None), ('+5V', 20.08, 56, 0, None), ('+5VA', 25.16, 56, 0, None), ('+3V3', 30.24, 56, 0, None),
    ('GND#2', 35.32, 56, 0, None),
    ('Controller test header', 41, 57, 90, None),
    ('Analog test header', 58, 104, 90, None),
    ('Digimatic test header', 106, 111, 90, None),
    ('Expander 2 spare', 76, 111, 90, None),
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
    unplaced = [p.ref for _, p in parts if not re.match(r'^(R|C|D|Q|F|JP|TP|LED)\d', p.ref) and p.ref not in anchors]
    unplanned_tp = [p.ref for _, p in parts if p.ref.startswith('TP') and p.ref not in anchors]
    if unplanned_tp:
        raise KeyError('test points without a planned spot: %s' % unplanned_tp)
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

It draws the 180 x 125 mm outline (only if the board has none), puts the edge
connectors against the edges with their plugs facing out, places ICs and modules at
planned spots, and packs every resistor, capacitor and small part next to the part
it connects to, at least 1 mm apart. Nothing is routed. Run it once on a fresh board;
re-running moves everything back to these spots.
"""
import pcbnew

W, H = %(W)s, %(H)s
ANCHORS = %(anchors)s
PASSIVES = %(passives)s
ANTENNA = (%(ant_y0)s, %(ant_y1)s, 5.0)   # y from, y to, x to: DevKit antenna band at the left edge
GAP = 1.0        # mm between part outlines, for hand soldering
MARGIN = 2.0     # mm from the board edge
HOLE_KEEP = 3.0  # extra mm kept clear around mounting holes (screw heads, standoffs)

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
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        px, py = pad_centre(fp)
        if {'top': cy > py, 'bottom': cy < py, 'left': cx > px, 'right': cx < px}[edge]:
            fp.SetOrientationDegrees(rot + 180)
        b = bbox(fp)
        if edge in ('top', 'bottom'):
            dx, dy = x - b[0], (0.5 - b[1]) if edge == 'top' else (H - 0.5 - b[3])
        else:
            dx, dy = (0.5 - b[0]) if edge == 'left' else (W - 0.5 - b[2]), y - b[1]
        shift(fp, dx, dy)
    b = bbox(fp)
    if ref.startswith('H'):
        b = [b[0] - HOLE_KEEP, b[1] - HOLE_KEEP, b[2] + HOLE_KEEP, b[3] + HOLE_KEEP]
    placed.append(b)

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

# part values to the fabrication layer: they stay visible in KiCad but don't print.
# LEDs, test points and test headers keep theirs on the silkscreen: it's their label.
for fp in B.GetFootprints():
    if fp.GetReference().startswith(('LED', 'TP')) or 'test header' in fp.GetValue():
        continue
    try:
        fp.Value().SetLayer(pcbnew.F_Fab)
    except Exception:
        pass

# ground plane on the bottom layer, with a notch under the DevKit antenna, plus an
# antenna keepout on both layers so no track or pour goes under it
def poly_zone(name, layer, pts, net=None, rule_area=False):
    z = pcbnew.ZONE(B)
    z.SetLayer(layer)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(mm(x), mm(y))
    z.SetZoneName(name)
    if rule_area:
        z.SetIsRuleArea(True)
        z.SetDoNotAllowCopperPour(True)
        z.SetDoNotAllowTracks(True)
        z.SetDoNotAllowVias(True)
    elif net is not None:
        z.SetNet(net)
    B.Add(z)
    return z

zones_note = ''
try:
    for z in list(B.Zones()):
        if z.GetZoneName() in ('GND plane', 'Antenna keepout'):
            B.Remove(z)
    ay0, ay1, ax1 = ANTENNA
    gnd = B.FindNet('GND')
    poly_zone('GND plane', pcbnew.B_Cu, [(0, 0), (W, 0), (W, H), (0, H), (0, ay1), (ax1, ay1), (ax1, ay0), (0, ay0)], gnd)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        poly_zone('Antenna keepout', layer, [(0, ay0), (ax1, ay0), (ax1, ay1), (0, ay1)], rule_area=True)
    pcbnew.ZONE_FILLER(B).Fill(B.Zones())
    zones_note = ' Ground plane added on B.Cu and filled.'
except Exception as e:
    zones_note = ' Ground plane not added (%%s): add a GND zone on B.Cu by hand.' %% e

pcbnew.Refresh()
print('Placed %%d anchors and %%d passives.%%s' %% (len(ANCHORS), len(PASSIVES), zones_note))
if missing:
    print('Not placed:', ', '.join(missing))
'''


def write(project, path):
    anchors, passives = build(project)
    with open(path, 'w') as fh:
        fh.write(SCRIPT % {'W': W, 'H': H, 'ant_y0': DEVKIT_PIN1[1] - 28.2, 'ant_y1': DEVKIT_PIN1[1] + 2.8, 'anchors': json.dumps(anchors, indent=1).replace('null', 'None'),
                           'passives': json.dumps(passives)})
    return anchors, passives
