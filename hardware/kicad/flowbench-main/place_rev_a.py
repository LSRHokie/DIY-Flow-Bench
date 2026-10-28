"""place_rev_a.py - DIY Flow Bench V2 main board, rev A starting placement.

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

W, H = 220.0, 160.0
ANCHORS = {
 "J1": [
  14,
  0,
  0,
  "top"
 ],
 "J16": [
  32,
  0,
  0,
  "top"
 ],
 "J18": [
  50,
  0,
  0,
  "top"
 ],
 "J15": [
  68,
  0,
  0,
  "top"
 ],
 "J17": [
  104,
  0,
  0,
  "top"
 ],
 "J19": [
  140,
  0,
  0,
  "top"
 ],
 "J20": [
  176,
  0,
  0,
  "top"
 ],
 "J21": [
  188,
  0,
  0,
  "top"
 ],
 "J6": [
  14,
  0,
  0,
  "bottom"
 ],
 "J11": [
  44,
  0,
  0,
  "bottom"
 ],
 "J7": [
  78,
  0,
  0,
  "bottom"
 ],
 "J12": [
  100,
  0,
  0,
  "bottom"
 ],
 "J5": [
  118,
  0,
  0,
  "bottom"
 ],
 "J8": [
  136,
  0,
  0,
  "bottom"
 ],
 "J9": [
  150,
  0,
  0,
  "bottom"
 ],
 "J10": [
  168,
  0,
  0,
  "bottom"
 ],
 "J2": [
  10,
  24,
  90,
  None
 ],
 "J3": [
  10,
  46,
  90,
  None
 ],
 "PS1": [
  52,
  22,
  0,
  None
 ],
 "PS2": [
  52,
  44,
  0,
  None
 ],
 "U1": [
  34,
  60,
  0,
  None
 ],
 "U18": [
  82,
  30,
  0,
  None
 ],
 "U19": [
  116,
  30,
  0,
  None
 ],
 "U20": [
  152,
  30,
  0,
  None
 ],
 "U21": [
  188,
  32,
  0,
  None
 ],
 "U2": [
  6,
  98,
  90,
  None
 ],
 "J4": [
  72,
  104,
  0,
  None
 ],
 "U3": [
  205,
  56,
  270,
  None
 ],
 "U13": [
  92,
  62,
  0,
  None
 ],
 "U14": [
  124,
  62,
  0,
  None
 ],
 "J14": [
  146,
  50,
  90,
  None
 ],
 "U15": [
  88,
  86,
  0,
  None
 ],
 "U16": [
  108,
  86,
  0,
  None
 ],
 "U17": [
  128,
  86,
  0,
  None
 ],
 "U4": [
  154,
  74,
  0,
  None
 ],
 "U5": [
  178,
  92,
  0,
  None
 ],
 "U6": [
  178,
  110,
  0,
  None
 ],
 "U7": [
  178,
  128,
  0,
  None
 ],
 "U8": [
  24,
  118,
  0,
  None
 ],
 "U9": [
  52,
  118,
  0,
  None
 ],
 "U11": [
  60,
  136,
  0,
  None
 ],
 "U10": [
  86,
  124,
  0,
  None
 ],
 "U12": [
  110,
  120,
  0,
  None
 ],
 "J13": [
  128,
  134,
  90,
  None
 ],
 "H1": [
  5,
  5,
  0,
  None
 ],
 "H2": [
  215.0,
  5,
  0,
  None
 ],
 "H3": [
  5,
  155.0,
  0,
  None
 ],
 "H4": [
  215.0,
  155.0,
  0,
  None
 ]
}
PASSIVES = [["F1", "J16"], ["Q1", "J16"], ["F2", "J18"], ["Q3", "J18"], ["Q5", "J21"], ["R10", "J21"], ["R9", "J21"], ["D1", "J6"], ["F4", "J6"], ["JP3", "J6"], ["R42", "J6"], ["R43", "J6"], ["R46", "J6"], ["R47", "J6"], ["R48", "J6"], ["R49", "J6"], ["R50", "J6"], ["R51", "J6"], ["C27", "J11"], ["R59", "J11"], ["R60", "J11"], ["R61", "J11"], ["R62", "J11"], ["R63", "J11"], ["R64", "J11"], ["R53", "J7"], ["R54", "J7"], ["R55", "J7"], ["R56", "J7"], ["JP4", "J12"], ["JP5", "J12"], ["Q7", "J12"], ["Q8", "J12"], ["Q9", "J12"], ["R65", "J12"], ["R66", "J12"], ["R67", "J12"], ["R68", "J12"], ["R69", "J12"], ["R70", "J12"], ["R72", "J12"], ["TP19", "J12"], ["TP20", "J12"], ["TP21", "J12"], ["C1", "PS2"], ["C2", "PS2"], ["C3", "PS2"], ["C4", "U1"], ["C5", "U1"], ["F3", "U1"], ["R1", "U1"], ["R2", "U1"], ["R5", "U1"], ["R6", "U1"], ["TP1", "U1"], ["TP2", "U1"], ["TP3", "U1"], ["TP4", "U1"], ["TP5", "U1"], ["TP6", "U1"], ["C38", "U18"], ["C39", "U19"], ["C40", "U21"], ["C41", "U21"], ["Q6", "U21"], ["R105", "U21"], ["R11", "U21"], ["R12", "U21"], ["TP22", "U21"], ["C29", "U2"], ["C30", "U2"], ["C31", "U2"], ["C32", "U2"], ["C33", "U2"], ["C34", "U2"], ["R13", "U2"], ["R14", "U2"], ["R15", "U2"], ["TP10", "U2"], ["TP11", "U2"], ["TP12", "U2"], ["TP7", "U2"], ["TP8", "U2"], ["TP9", "U2"], ["C8", "J4"], ["C9", "J4"], ["JP2", "J4"], ["R19", "J4"], ["R20", "J4"], ["R21", "J4"], ["R22", "J4"], ["R23", "J4"], ["R24", "J4"], ["R25", "J4"], ["R26", "J4"], ["R27", "J4"], ["TP14", "J4"], ["TP15", "J4"], ["TP16", "J4"], ["C6", "U3"], ["C7", "U3"], ["JP1", "U3"], ["R16", "U3"], ["R17", "U3"], ["R18", "U3"], ["TP13", "U3"], ["Q2", "U13"], ["R3", "U13"], ["R4", "U13"], ["R73", "U13"], ["R74", "U13"], ["R75", "U13"], ["R76", "U13"], ["R77", "U13"], ["R78", "U13"], ["R79", "U13"], ["R80", "U13"], ["R81", "U13"], ["R83", "U13"], ["R85", "U13"], ["R86", "U13"], ["R87", "U13"], ["R88", "U13"], ["R89", "U13"], ["C36", "U14"], ["C37", "U14"], ["Q4", "U14"], ["R7", "U14"], ["R8", "U14"], ["R82", "U14"], ["R84", "U14"], ["R90", "U14"], ["R91", "U14"], ["R92", "U14"], ["R93", "U14"], ["R94", "U14"], ["R95", "U14"], ["R96", "U15"], ["R97", "U15"], ["R98", "U15"], ["R99", "U15"], ["R100", "U16"], ["R101", "U16"], ["R102", "U16"], ["R103", "U16"], ["R104", "U17"], ["C10", "U4"], ["R28", "U4"], ["R29", "U4"], ["R30", "U4"], ["R31", "U4"], ["R32", "U4"], ["R33", "U4"], ["R34", "U4"], ["R35", "U4"], ["R36", "U4"], ["C11", "U5"], ["C12", "U6"], ["C13", "U7"], ["C19", "U8"], ["C20", "U8"], ["C22", "U8"], ["C23", "U8"], ["D2", "U8"], ["R37", "U8"], ["R38", "U8"], ["R39", "U8"], ["R40", "U8"], ["R41", "U8"], ["R44", "U8"], ["R45", "U8"], ["C14", "U9"], ["C15", "U9"], ["C16", "U9"], ["C17", "U9"], ["C18", "U9"], ["C21", "U9"], ["C24", "U9"], ["D3", "U9"], ["TP17", "U9"], ["TP18", "U9"], ["C26", "U11"], ["C28", "U11"], ["R57", "U11"], ["R58", "U11"], ["C25", "U10"], ["R52", "U10"], ["C35", "U12"], ["R71", "U12"]]
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
print('Placed %d anchors and %d passives.' % (len(ANCHORS), len(PASSIVES)))
if missing:
    print('Not placed:', ', '.join(missing))
