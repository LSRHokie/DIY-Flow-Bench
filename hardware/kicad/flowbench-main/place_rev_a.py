"""place_rev_a.py - DIY Flow Bench V2 main board, rev A starting placement.

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

W, H = 180.0, 125.0
ANCHORS = {
 "J1": [
  13,
  0,
  0,
  "top"
 ],
 "J20": [
  27,
  0,
  0,
  "top"
 ],
 "J22": [
  41,
  0,
  0,
  "top"
 ],
 "J19": [
  55,
  0,
  0,
  "top"
 ],
 "J21": [
  90,
  0,
  0,
  "top"
 ],
 "J23": [
  125,
  0,
  0,
  "top"
 ],
 "J24": [
  0,
  13,
  90,
  "right"
 ],
 "J25": [
  0,
  26,
  90,
  "right"
 ],
 "J12": [
  0,
  13,
  90,
  "left"
 ],
 "J11": [
  0,
  37,
  90,
  "left"
 ],
 "J8": [
  13,
  0,
  0,
  "bottom"
 ],
 "J13": [
  45,
  0,
  0,
  "bottom"
 ],
 "J9": [
  80,
  0,
  0,
  "bottom"
 ],
 "J14": [
  104,
  0,
  0,
  "bottom"
 ],
 "J6": [
  124,
  0,
  0,
  "bottom"
 ],
 "J10": [
  144,
  0,
  0,
  "bottom"
 ],
 "J2": [
  13,
  17,
  90,
  None
 ],
 "J3": [
  13,
  31,
  90,
  None
 ],
 "PS1": [
  48,
  15,
  0,
  None
 ],
 "PS2": [
  70,
  15,
  0,
  None
 ],
 "U1": [
  32,
  42,
  0,
  None
 ],
 "U18": [
  99,
  26,
  0,
  None
 ],
 "U19": [
  116,
  26,
  0,
  None
 ],
 "U20": [
  136,
  27,
  0,
  None
 ],
 "U21": [
  157,
  26,
  0,
  None
 ],
 "U2": [
  6,
  88,
  90,
  None
 ],
 "J5": [
  70,
  85,
  0,
  None
 ],
 "U3": [
  167,
  46,
  270,
  None
 ],
 "U13": [
  80,
  48,
  0,
  None
 ],
 "U14": [
  102,
  48,
  0,
  None
 ],
 "U15": [
  76,
  68,
  0,
  None
 ],
 "U16": [
  94,
  68,
  0,
  None
 ],
 "U17": [
  112,
  68,
  0,
  None
 ],
 "U4": [
  132,
  70,
  0,
  None
 ],
 "U5": [
  150,
  70,
  0,
  None
 ],
 "U6": [
  150,
  84,
  0,
  None
 ],
 "U7": [
  150,
  98,
  0,
  None
 ],
 "U8": [
  18,
  100,
  0,
  None
 ],
 "U9": [
  36,
  100,
  0,
  None
 ],
 "U11": [
  53,
  102,
  0,
  None
 ],
 "U10": [
  90,
  100,
  0,
  None
 ],
 "U12": [
  112,
  101,
  0,
  None
 ],
 "J15": [
  129,
  103,
  90,
  None
 ],
 "TP1": [
  116,
  43,
  0,
  None
 ],
 "TP2": [
  122.35,
  43,
  0,
  None
 ],
 "TP3": [
  128.7,
  43,
  0,
  None
 ],
 "TP4": [
  135.05,
  43,
  0,
  None
 ],
 "TP5": [
  141.4,
  43,
  0,
  None
 ],
 "TP6": [
  147.75,
  43,
  0,
  None
 ],
 "TP7": [
  147.75,
  49.35,
  0,
  None
 ],
 "TP8": [
  15,
  56,
  0,
  None
 ],
 "TP9": [
  20.08,
  56,
  0,
  None
 ],
 "TP10": [
  25.16,
  56,
  0,
  None
 ],
 "TP11": [
  30.24,
  56,
  0,
  None
 ],
 "TP12": [
  35.32,
  56,
  0,
  None
 ],
 "J4": [
  41,
  57,
  90,
  None
 ],
 "J7": [
  58,
  104,
  90,
  None
 ],
 "J16": [
  106,
  113.5,
  90,
  None
 ],
 "PROTO1": [
  97.5,
  76,
  0,
  None
 ],
 "J17": [
  124.8,
  77,
  0,
  None
 ],
 "J18": [
  127.34,
  77,
  0,
  None
 ],
 "H1": [
  5,
  5,
  0,
  None
 ],
 "H2": [
  175.0,
  5,
  0,
  None
 ],
 "H3": [
  5,
  120.0,
  0,
  None
 ],
 "H4": [
  175.0,
  120.0,
  0,
  None
 ]
}
PASSIVES = [["Q5", "J25"], ["R10", "J25"], ["R111", "J25"], ["R9", "J25"], ["R115", "J12"], ["R116", "J12"], ["R117", "J12"], ["R113", "J11"], ["R114", "J11"], ["D1", "J8"], ["F4", "J8"], ["JP3", "J8"], ["R57", "J8"], ["R58", "J8"], ["R61", "J8"], ["R62", "J8"], ["R63", "J8"], ["R64", "J8"], ["R65", "J8"], ["R66", "J8"], ["C27", "J13"], ["R74", "J13"], ["R75", "J13"], ["R76", "J13"], ["R77", "J13"], ["R78", "J13"], ["R79", "J13"], ["R68", "J9"], ["R69", "J9"], ["R70", "J9"], ["R71", "J9"], ["JP4", "J14"], ["JP5", "J14"], ["Q7", "J14"], ["Q8", "J14"], ["Q9", "J14"], ["R80", "J14"], ["R81", "J14"], ["R82", "J14"], ["R83", "J14"], ["R84", "J14"], ["R85", "J14"], ["R87", "J14"], ["R112", "J10"], ["LED5", "J3"], ["R17", "J3"], ["C1", "PS2"], ["C2", "PS2"], ["C3", "PS2"], ["C4", "U1"], ["C5", "U1"], ["F3", "U1"], ["LED1", "U1"], ["LED2", "U1"], ["LED3", "U1"], ["LED4", "U1"], ["R1", "U1"], ["R13", "U1"], ["R14", "U1"], ["R15", "U1"], ["R16", "U1"], ["R2", "U1"], ["R5", "U1"], ["R6", "U1"], ["C38", "U18"], ["C39", "U19"], ["LED18", "U20"], ["LED19", "U20"], ["LED20", "U20"], ["LED21", "U20"], ["LED22", "U20"], ["LED23", "U20"], ["LED24", "U20"], ["R122", "U20"], ["R123", "U20"], ["R124", "U20"], ["R125", "U20"], ["R126", "U20"], ["R127", "U20"], ["R128", "U20"], ["C40", "U21"], ["C41", "U21"], ["LED17", "U21"], ["R120", "U21"], ["R121", "U21"], ["C29", "U2"], ["C30", "U2"], ["C31", "U2"], ["C32", "U2"], ["C33", "U2"], ["C34", "U2"], ["R20", "U2"], ["R21", "U2"], ["R22", "U2"], ["C8", "J5"], ["C9", "J5"], ["JP2", "J5"], ["R26", "J5"], ["R27", "J5"], ["R28", "J5"], ["R29", "J5"], ["R30", "J5"], ["R31", "J5"], ["R32", "J5"], ["R33", "J5"], ["R34", "J5"], ["C6", "U3"], ["C7", "U3"], ["JP1", "U3"], ["R23", "U3"], ["R24", "U3"], ["R25", "U3"], ["Q2", "U13"], ["R100", "U13"], ["R101", "U13"], ["R102", "U13"], ["R103", "U13"], ["R104", "U13"], ["R3", "U13"], ["R4", "U13"], ["R88", "U13"], ["R89", "U13"], ["R90", "U13"], ["R91", "U13"], ["R92", "U13"], ["R93", "U13"], ["R94", "U13"], ["R95", "U13"], ["R96", "U13"], ["R98", "U13"], ["C36", "U14"], ["C37", "U14"], ["Q4", "U14"], ["R105", "U14"], ["R106", "U14"], ["R107", "U14"], ["R108", "U14"], ["R109", "U14"], ["R110", "U14"], ["R7", "U14"], ["R8", "U14"], ["R97", "U14"], ["R99", "U14"], ["LED10", "U15"], ["LED11", "U15"], ["LED8", "U15"], ["LED9", "U15"], ["LED12", "U16"], ["LED13", "U16"], ["LED14", "U16"], ["LED15", "U16"], ["R118", "U16"], ["LED16", "U17"], ["R119", "U17"], ["C10", "U4"], ["R35", "U4"], ["R36", "U4"], ["R37", "U4"], ["R38", "U4"], ["R39", "U4"], ["R40", "U4"], ["R41", "U4"], ["R42", "U4"], ["R43", "U4"], ["R44", "U4"], ["R45", "U4"], ["R46", "U4"], ["R47", "U4"], ["R48", "U4"], ["R49", "U4"], ["R50", "U4"], ["R51", "U4"], ["C11", "U5"], ["C12", "U6"], ["C13", "U7"], ["C19", "U8"], ["C20", "U8"], ["C22", "U8"], ["C23", "U8"], ["D2", "U8"], ["R52", "U8"], ["R53", "U8"], ["R54", "U8"], ["R55", "U8"], ["R56", "U8"], ["R59", "U8"], ["R60", "U8"], ["C14", "U9"], ["C15", "U9"], ["C16", "U9"], ["C17", "U9"], ["C18", "U9"], ["C21", "U9"], ["C24", "U9"], ["D3", "U9"], ["C26", "U11"], ["C28", "U11"], ["R72", "U11"], ["R73", "U11"], ["C25", "U10"], ["R67", "U10"], ["C35", "U12"], ["R86", "U12"], ["F1", "TP3"], ["LED6", "TP3"], ["Q1", "TP3"], ["R18", "TP3"], ["F2", "TP4"], ["LED7", "TP4"], ["Q3", "TP4"], ["R19", "TP4"], ["Q6", "J4"], ["R11", "J4"], ["R12", "J4"]]
ANTENNA = (59.8, 90.8, 5.0)   # y from, y to, x to: DevKit antenna band at the left edge
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
    zones_note = ' Ground plane not added (%s): add a GND zone on B.Cu by hand.' % e

pcbnew.Refresh()
print('Placed %d anchors and %d passives.%s' % (len(ANCHORS), len(PASSIVES), zones_note))
if missing:
    print('Not placed:', ', '.join(missing))
