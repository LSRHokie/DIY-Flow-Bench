"""kicadgen.py - small KiCad 7 schematic writer for DIY Flow Bench V2.

Builds hierarchical KiCad 7 schematics (file version 20230121, opens in KiCad 7, 8
and 9) from a Python description of parts and nets. Every pin gets a short wire and
a net label, so connectivity comes from the net names and the layout only has to be
readable, not routed.

Symbols come from two places:
  * converted from the KiCad 5 symbol library (github.com/KiCad/kicad-symbols),
    which keeps KiCad's own pinouts for parts it already has;
  * drawn here as plain rectangles, from datasheet pinouts, for parts it lacks.

All symbols are written into one project library (FlowBench.kicad_sym) and embedded
in each schematic, so the project opens without any other library installed.
"""
import math, os, re, uuid as uuidlib

GRID = 1.27
MIL = 0.0254


def U():
    return str(uuidlib.uuid4())


def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'


def f(v):
    v = round(v, 4)
    if v == int(v):
        return str(int(v))
    return ('%.4f' % v).rstrip('0').rstrip('.')


def snap(v):
    return round(round(v / GRID) * GRID, 4)


# --------------------------------------------------------------------------- symbols

class Pin:
    def __init__(self, num, name, x, y, angle, length, etype, shape='line', unit=1, hidden=False):
        self.num, self.name, self.x, self.y = str(num), name, x, y
        self.angle, self.length, self.etype, self.shape = angle, length, etype, shape
        self.unit, self.hidden = unit, hidden


class Symbol:
    """A library symbol. Coordinates in mm, library convention (y up)."""

    def __init__(self, name, ref='U', power=False, show_pin_numbers=True, show_pin_names=True,
                 name_offset=0.508, footprint='', datasheet='~', description=''):
        self.name, self.ref, self.power = name, ref, power
        self.show_pin_numbers, self.show_pin_names = show_pin_numbers, show_pin_names
        self.name_offset = name_offset
        self.footprint, self.datasheet, self.description = footprint, datasheet, description
        self.graphics = {}   # unit -> list of s-expr strings (unit 0 = all units)
        self.pins = []
        self.ref_at = (0, 0, 0)
        self.val_at = (0, -2.54, 0)

    @property
    def units(self):
        us = sorted({p.unit for p in self.pins if p.unit != 0})
        return us or [1]

    def unit_pins(self, unit):
        return [p for p in self.pins if p.unit in (unit, 0)]

    def unit_box(self, unit):
        """Body bounding box (graphics only) in library coordinates."""
        xs, ys = [], []
        for u in (0, unit):
            for g in self.graphics.get(u, []):
                for m in re.finditer(r'\((?:xy|start|end|center|mid) (-?[\d.]+) (-?[\d.]+)\)', g):
                    xs.append(float(m.group(1))); ys.append(float(m.group(2)))
                m = re.search(r'\(center (-?[\d.]+) (-?[\d.]+)\) \(radius ([\d.]+)\)', g)
                if m:
                    cx, cy, r = map(float, m.groups())
                    xs += [cx - r, cx + r]; ys += [cy - r, cy + r]
        for p in self.unit_pins(unit):
            ex, ey = pin_inner(p)
            xs.append(ex); ys.append(ey)
        if not xs:
            return (-1.27, -1.27, 1.27, 1.27)
        return (min(xs), min(ys), max(xs), max(ys))

    def sexpr(self, libname=None):
        full = (libname + ':' if libname else '') + self.name
        flags = []
        if self.power:
            flags.append('(power)')
        if not self.show_pin_numbers:
            flags.append('(pin_numbers hide)')
        flags.append('(pin_names (offset %s)%s)' % (f(self.name_offset), '' if self.show_pin_names else ' hide'))
        flags.append('(in_bom %s) (on_board yes)' % ('no' if self.power else 'yes'))
        out = ['(symbol %s %s' % (q(full), ' '.join(flags))]
        props = [('Reference', self.ref, self.ref_at, False), ('Value', self.name, self.val_at, False),
                 ('Footprint', self.footprint, (0, 0, 0), True), ('Datasheet', self.datasheet, (0, 0, 0), True)]
        if self.description:
            props.append(('ki_description', self.description, (0, 0, 0), True))
        for k, v, at, hide in props:
            out.append('  (property %s %s (at %s %s %s) (effects (font (size 1.27 1.27))%s))'
                       % (q(k), q(v), f(at[0]), f(at[1]), f(at[2]), ' hide' if hide else ''))
        units = sorted(set(list(self.graphics.keys()) + [p.unit for p in self.pins]))
        for u in units:
            items = list(self.graphics.get(u, []))
            for p in self.pins:
                if p.unit == u:
                    items.append('(pin %s %s (at %s %s %d) (length %s)%s (name %s (effects (font (size 1.27 1.27)))) '
                                 '(number %s (effects (font (size 1.27 1.27)))))'
                                 % (p.etype, p.shape, f(p.x), f(p.y), p.angle, f(p.length),
                                    ' hide' if p.hidden else '', q(p.name), q(p.num)))
            if items:
                out.append('  (symbol %s' % q('%s_%d_1' % (self.name, u)))
                for it in items:
                    out.append('    ' + it)
                out.append('  )')
        out.append(')')
        return '\n'.join(out)


def pin_inner(p):
    a = math.radians(p.angle)
    return (p.x + p.length * math.cos(a), p.y + p.length * math.sin(a))


def stroke(w=0):
    return '(stroke (width %s) (type default))' % f(w)


def fill(t):
    return '(fill (type %s))' % t


def rect_symbol(name, ref='U', left=(), right=(), top=(), bottom=(), width=None, footprint='',
                datasheet='~', description='', pin_len=2.54):
    """Rectangular symbol. Each side is a list of (number, name, etype) or None for a gap."""
    sym = Symbol(name, ref, footprint=footprint, datasheet=datasheet, description=description)
    rows = max(len(left), len(right), 1)
    cols = max(len(top), len(bottom), 1)
    longest = max([len(p[1]) for p in list(left) + list(right) if p] + [4])
    w = width or snap(max(10.16, 2 * longest * 1.0 + 5.08, (cols + 1) * 2.54))
    w = snap(w / 2) * 2
    h = snap((rows + 1) * 2.54)
    if abs(h / 2 / GRID - round(h / 2 / GRID)) > 1e-6:   # keep the half-height on the 1.27 mm grid
        h += GRID
    x0, x1, y1, y0 = -w / 2, w / 2, h / 2, -h / 2
    sym.graphics[0] = ['(rectangle (start %s %s) (end %s %s) %s %s)'
                       % (f(x0), f(y1), f(x1), f(y0), stroke(0.254), fill('background'))]
    ytop = snap(y1 - 2.54)
    for i, p in enumerate(left):
        if p:
            sym.pins.append(Pin(p[0], p[1], x0 - pin_len, ytop - 2.54 * i, 0, pin_len, p[2] if len(p) > 2 else 'passive'))
    for i, p in enumerate(right):
        if p:
            sym.pins.append(Pin(p[0], p[1], x1 + pin_len, ytop - 2.54 * i, 180, pin_len, p[2] if len(p) > 2 else 'passive'))
    xl = snap(-(len(top) - 1) * 2.54 / 2)
    for i, p in enumerate(top):
        if p:
            sym.pins.append(Pin(p[0], p[1], xl + 2.54 * i, y1 + pin_len, 270, pin_len, p[2] if len(p) > 2 else 'passive'))
    xl = snap(-(len(bottom) - 1) * 2.54 / 2)
    for i, p in enumerate(bottom):
        if p:
            sym.pins.append(Pin(p[0], p[1], xl + 2.54 * i, y0 - pin_len, 90, pin_len, p[2] if len(p) > 2 else 'passive'))
    sym.ref_at = (0, y1 + 1.27, 0)
    sym.val_at = (0, y0 - 1.27, 0)
    return sym


# --------------------------------------------------- KiCad 5 .lib -> KiCad 7 conversion

ETYPE = {'I': 'input', 'O': 'output', 'B': 'bidirectional', 'T': 'tri_state', 'P': 'passive',
         'U': 'unspecified', 'W': 'power_in', 'w': 'power_out', 'C': 'open_collector',
         'E': 'open_emitter', 'N': 'no_connect'}
SHAPE = {'': 'line', 'I': 'inverted', 'C': 'clock', 'CI': 'inverted_clock', 'L': 'input_low',
         'CL': 'clock_low', 'V': 'output_low', 'F': 'edge_clock_high', 'X': 'non_logic'}
ORIENT = {'R': 0, 'U': 90, 'L': 180, 'D': 270}
FILL5 = {'F': 'outline', 'f': 'background', 'N': 'none'}


def v5_name(s):
    """KiCad 5 overbar (~X~) to KiCad 6+ (~{X})."""
    if s == '~':
        return '~'
    parts = s.split('~')
    out = parts[0]
    for i, seg in enumerate(parts[1:]):
        out += ('~{' + seg + '}') if i % 2 == 0 else seg
    return out.replace('~{}', '')


class V5Lib:
    def __init__(self, libdir):
        self.libdir = libdir
        self.defs = {}

    def load(self, libfile):
        text = open(os.path.join(self.libdir, libfile), encoding='utf-8', errors='replace').read()
        for block in re.findall(r'^DEF .*?^ENDDEF', text, re.S | re.M):
            lines = block.split('\n')
            name = lines[0].split()[1]
            self.defs[name] = lines
            for ln in lines:
                if ln.startswith('ALIAS '):
                    for a in ln.split()[1:]:
                        self.defs[a] = lines

    def symbol(self, defname, newname=None, footprint=None, unhide_power=True):
        lines = self.defs[defname]
        d = lines[0].split()
        sym = Symbol(newname or defname, ref=d[2], power=(len(d) > 9 and d[9] == 'P'),
                     show_pin_numbers=(d[5] == 'Y'), show_pin_names=(d[6] == 'Y'),
                     name_offset=int(d[4]) * MIL)
        for ln in lines:
            t = ln.split()
            if not t:
                continue
            if t[0] == 'F0':
                sym.ref_at = (int(t[2]) * MIL, int(t[3]) * MIL, 90 if t[5] == 'V' else 0)
            elif t[0] == 'F1':
                sym.val_at = (int(t[2]) * MIL, int(t[3]) * MIL, 90 if t[5] == 'V' else 0)
            elif t[0] == 'F2':
                sym.footprint = t[1].strip('"')
            elif t[0] == 'F3':
                sym.datasheet = t[1].strip('"') or '~'
        if footprint is not None:
            sym.footprint = footprint
        in_draw = False
        for ln in lines:
            t = ln.split()
            if not t:
                continue
            if t[0] == 'DRAW':
                in_draw = True; continue
            if t[0] == 'ENDDRAW':
                break
            if not in_draw:
                continue
            k = t[0]
            if k == 'X':
                name, num, x, y, length, o = t[1], t[2], int(t[3]), int(t[4]), int(t[5]), t[6]
                unit, conv, et = int(t[9]), int(t[10]), t[11]
                shp = t[12] if len(t) > 12 else ''
                if conv == 2:
                    continue
                hidden = shp.startswith('N')
                shp = shp[1:] if hidden else shp
                if hidden and unhide_power and et in ('W', 'w'):
                    hidden = False   # never rely on hidden power pins: label every pin
                sym.pins.append(Pin(num, v5_name(name), x * MIL, y * MIL, ORIENT[o], length * MIL,
                                    ETYPE[et], SHAPE.get(shp, 'line'), unit, hidden))
                continue
            if k in ('S', 'P', 'C', 'A', 'T'):
                if k == 'S':
                    unit, conv = int(t[5]), int(t[6])
                    g = '(rectangle (start %s %s) (end %s %s) %s %s)' % (
                        f(int(t[1]) * MIL), f(int(t[2]) * MIL), f(int(t[3]) * MIL), f(int(t[4]) * MIL),
                        stroke(int(t[7]) * MIL), fill(FILL5.get(t[8], 'none')))
                elif k == 'P':
                    n, unit, conv, w = int(t[1]), int(t[2]), int(t[3]), int(t[4])
                    pts = ' '.join('(xy %s %s)' % (f(int(t[5 + 2 * i]) * MIL), f(int(t[6 + 2 * i]) * MIL))
                                   for i in range(n))
                    fl = t[5 + 2 * n] if len(t) > 5 + 2 * n else 'N'
                    g = '(polyline (pts %s) %s %s)' % (pts, stroke(w * MIL), fill(FILL5.get(fl, 'none')))
                elif k == 'C':
                    unit, conv = int(t[4]), int(t[5])
                    g = '(circle (center %s %s) (radius %s) %s %s)' % (
                        f(int(t[1]) * MIL), f(int(t[2]) * MIL), f(int(t[3]) * MIL),
                        stroke(int(t[6]) * MIL), fill(FILL5.get(t[7], 'none')))
                elif k == 'A':
                    cx, cy, r = int(t[1]), int(t[2]), int(t[3])
                    unit, conv, w, fl = int(t[6]), int(t[7]), int(t[8]), t[9]
                    xs, ys, xe, ye = int(t[10]), int(t[11]), int(t[12]), int(t[13])
                    vx, vy = (xs - cx) + (xe - cx), (ys - cy) + (ye - cy)
                    norm = math.hypot(vx, vy)
                    if norm < 1e-6:
                        vx, vy = -(ys - cy), (xs - cx); norm = math.hypot(vx, vy)
                    mx, my = cx + r * vx / norm, cy + r * vy / norm
                    g = '(arc (start %s %s) (mid %s %s) (end %s %s) %s %s)' % (
                        f(xs * MIL), f(ys * MIL), f(mx * MIL), f(my * MIL), f(xe * MIL), f(ye * MIL),
                        stroke(w * MIL), fill(FILL5.get(fl, 'none')))
                else:  # T
                    unit, conv = int(t[6]), int(t[7])
                    txt = t[8].strip('"').replace('~', ' ')
                    g = '(text %s (at %s %s %d) (effects (font (size %s %s))))' % (
                        q(txt), f(int(t[2]) * MIL), f(int(t[3]) * MIL), int(t[1]) // 10,
                        f(int(t[4]) * MIL), f(int(t[4]) * MIL))
                if conv == 2:
                    continue
                sym.graphics.setdefault(unit, []).append(g)
        return sym


# --------------------------------------------------------------------------- schematic

class Part:
    def __init__(self, ref, sym, value, nets, footprint=None, fields=None, units=None, dnp=False):
        self.ref, self.sym, self.value = ref, sym, value
        self.nets = {str(k): v for k, v in nets.items()}
        self.footprint = sym.footprint if footprint is None else footprint
        self.fields = fields or {}
        self.units = units or sym.units
        self.dnp = dnp
        missing = [p.num for u in self.units for p in sym.unit_pins(u) if p.num not in self.nets]
        if missing:
            raise ValueError('%s (%s): no net given for pins %s' % (ref, sym.name, sorted(set(missing))))
        extra = set(self.nets) - {p.num for p in sym.pins}
        if extra:
            raise ValueError('%s (%s): unknown pins %s' % (ref, sym.name, sorted(extra)))


class Sheet:
    def __init__(self, name, filename, title, paper='A2', width=None):
        self.name, self.filename, self.title, self.paper = name, filename, title, paper
        self.parts, self.notes = [], []
        self.width = width or {'A4': 270, 'A3': 395, 'A2': 570, 'A1': 820}[paper]
        self.uuid = U()          # the sheet symbol's uuid in the root
        self.file_uuid = U()

    def add(self, part):
        self.parts.append(part)
        return part

    def note(self, text):
        self.notes.append(text)


def label_len(name):
    return len(name) * 1.05 + 3.0


class Project:
    def __init__(self, name, title, libname='FlowBench', company='DIY Flow Bench V2', rev='A', date=''):
        self.name, self.title, self.libname = name, title, libname
        self.company, self.rev, self.date = company, rev, date
        self.sheets, self.symbols = [], {}
        self.root_uuid = U()
        self.counters = {}

    def sym(self, s):
        if s.name in self.symbols and self.symbols[s.name] is not s:
            return self.symbols[s.name]
        self.symbols[s.name] = s
        return s

    def ref(self, prefix):
        n = self.counters.get(prefix, 0) + 1
        self.counters[prefix] = n
        return '%s%d' % (prefix, n)

    # ---- connectivity report
    def netlist(self):
        nets = {}
        for sh in self.sheets:
            for p in sh.parts:
                for u in p.units:
                    for pin in p.sym.unit_pins(u):
                        n = p.nets[pin.num]
                        if n:
                            nets.setdefault(n, set()).add((p.ref, pin.num, pin.name, sh.name))
        return nets

    def check(self, allow_single=()):
        nets = self.netlist()
        problems = []
        for n, members in sorted(nets.items()):
            if len(members) < 2 and n not in allow_single:
                problems.append('net %s has only one connection: %s' % (n, sorted(members)))
        return nets, problems

    # ---- writing
    def write(self, outdir):
        os.makedirs(outdir, exist_ok=True)
        nets = self.netlist()
        net_sheets = {}
        for n, members in nets.items():
            net_sheets[n] = {m[3] for m in members}
        self.global_nets = {n for n, s in net_sheets.items() if len(s) > 1}
        libtxt = ['(kicad_symbol_lib (version 20220914) (generator kicadgen)']
        for s in sorted(self.symbols.values(), key=lambda s: s.name):
            libtxt.append(s.sexpr())
        libtxt.append(')')
        open(os.path.join(outdir, self.libname + '.kicad_sym'), 'w').write('\n'.join(libtxt) + '\n')
        open(os.path.join(outdir, 'sym-lib-table'), 'w').write(
            '(sym_lib_table\n  (lib (name "%s")(type "KiCad")(uri "${KIPRJMOD}/%s.kicad_sym")(options "")'
            '(descr "DIY Flow Bench V2 project symbols"))\n)\n' % (self.libname, self.libname))
        for page, sh in enumerate(self.sheets, start=2):
            self._write_sheet(outdir, sh, page)
        self._write_root(outdir)
        self._write_pro(outdir)

    def _lib_symbols(self, sheet):
        used = {}
        for p in sheet.parts:
            used[p.sym.name] = p.sym
        return '(lib_symbols\n' + '\n'.join(s.sexpr(self.libname) for s in used.values()) + '\n)'

    def _title_block(self, title, comment=''):
        return ('(title_block (title %s) (date %s) (rev %s) (company %s)%s)'
                % (q(title), q(self.date), q(self.rev), q(self.company),
                   (' (comment 1 %s)' % q(comment)) if comment else ''))

    def _write_root(self, outdir):
        out = ['(kicad_sch (version 20230121) (generator kicadgen)', '(uuid %s)' % self.root_uuid,
               '(paper "A4")', self._title_block(self.title), '(lib_symbols)']
        x, y = 25.4, 38.1
        for page, sh in enumerate(self.sheets, start=2):
            out.append('(sheet (at %s %s) (size 50.8 12.7) (fields_autoplaced)\n'
                       '  (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000))\n'
                       '  (uuid %s)\n'
                       '  (property "Sheetname" %s (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
                       '  (property "Sheetfile" %s (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left top)))\n'
                       '  (instances (project %s (path "/%s" (page "%d"))))\n)'
                       % (f(x), f(y), sh.uuid, q(sh.name), f(x), f(y - 0.7), q(sh.filename), f(x), f(y + 13.4),
                          q(self.name), self.root_uuid, page))
            x += 63.5
            if x > 230:
                x, y = 25.4, y + 30.48
        out.append('(text %s (at 25.4 25.4 0) (effects (font (size 2.54 2.54)) (justify left bottom)) (uuid %s))'
                   % (q(self.title), U()))
        out.append('(sheet_instances (path "/" (page "1")))')
        out.append(')')
        open(os.path.join(outdir, self.name + '.kicad_sch'), 'w').write('\n'.join(out) + '\n')

    def _write_pro(self, outdir):
        import json
        pro = {"meta": {"filename": self.name + ".kicad_pro", "version": 1},
               "sheets": [[self.root_uuid, ""]] + [[s.uuid, s.name] for s in self.sheets],
               "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
               "boards": [], "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
               "text_variables": {}}
        open(os.path.join(outdir, self.name + '.kicad_pro'), 'w').write(json.dumps(pro, indent=2) + '\n')

    def _write_sheet(self, outdir, sh, page):
        path = '/%s/%s' % (self.root_uuid, sh.uuid)
        out = ['(kicad_sch (version 20230121) (generator kicadgen)', '(uuid %s)' % sh.file_uuid,
               '(paper %s)' % q(sh.paper), self._title_block(sh.title), self._lib_symbols(sh)]
        items = []
        # layout: pack units in rows
        cursor_x, cursor_y, row_h = 20.32, 30.48, 0
        ny = 20.32
        for text in sh.notes:
            items.append('(text %s (at 20.32 %s 0) (effects (font (size 1.524 1.524)) (justify left bottom)) (uuid %s))'
                         % (q(text), f(ny), U()))
            ny += 3.81
        cursor_y = snap(max(cursor_y, ny + 7.62))
        for part in sh.parts:
            for unit in part.units:
                pins = part.sym.unit_pins(unit)
                bx0, by0, bx1, by1 = part.sym.unit_box(unit)
                # extents in schematic coords (y down) relative to symbol origin
                L, R, T, B = bx0, bx1, -by1, -by0
                for p in pins:
                    n = part.nets[p.num]
                    ext = 2.54 + (label_len(n) if n else 1.27)
                    if p.angle == 0:
                        L = min(L, p.x - ext)
                    elif p.angle == 180:
                        R = max(R, p.x + ext)
                    elif p.angle == 270:      # pin at top, points down into body
                        T = min(T, -p.y - ext)
                    else:
                        B = max(B, -p.y + ext)
                T -= 5.08
                w, h = R - L, B - T
                if cursor_x + w > sh.width and cursor_x > 20.32:
                    cursor_x, cursor_y, row_h = 20.32, cursor_y + row_h + 7.62, 0
                ox, oy = snap(cursor_x - L), snap(cursor_y - T)
                cursor_x += w + 10.16
                row_h = max(row_h, h)
                items.append(self._symbol_instance(part, unit, ox, oy, path, L, T))
                seen = {}
                for p in pins:
                    px, py = ox + p.x, oy - p.y
                    key = (round(px, 3), round(py, 3))
                    n = part.nets[p.num]
                    if key in seen:
                        if seen[key] != n:
                            raise ValueError('%s: stacked pins at one point on different nets' % part.ref)
                        continue
                    seen[key] = n
                    if n is None:
                        items.append('(no_connect (at %s %s) (uuid %s))' % (f(px), f(py), U()))
                        continue
                    dx, dy, ang = {0: (-2.54, 0, 180), 180: (2.54, 0, 0), 90: (0, 2.54, 270),
                                   270: (0, -2.54, 90)}[p.angle]
                    ex, ey = px + dx, py + dy
                    items.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid %s))'
                                 % (f(px), f(py), f(ex), f(ey), U()))
                    items.append(self._label(n, ex, ey, ang))
        out += items
        out.append(')')
        open(os.path.join(outdir, sh.filename), 'w').write('\n'.join(out) + '\n')

    def _label(self, net, x, y, ang):
        just = {0: 'left', 180: 'right', 90: 'left', 270: 'right'}[ang]
        if net in self.global_nets:
            return ('(global_label %s (shape passive) (at %s %s %d) (fields_autoplaced) '
                    '(effects (font (size 1.27 1.27)) (justify %s)) (uuid %s) '
                    '(property "Intersheetrefs" "${INTERSHEET_REFS}" (at %s %s %d) '
                    '(effects (font (size 1.27 1.27)) (justify %s) hide)))'
                    % (q(net), f(x), f(y), ang, just, U(), f(x), f(y), ang, just))
        return ('(label %s (at %s %s %d) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify %s bottom)) (uuid %s))'
                % (q(net), f(x), f(y), ang, just, U()))

    def _symbol_instance(self, part, unit, ox, oy, path, L, T):
        sym = part.sym
        fx, fy = ox + L, oy + T + 2.54
        props = [('Reference', part.ref, fx, fy, False),
                 ('Value', part.value, fx + len(part.ref) * 1.1 + 2.54, fy, False),
                 ('Footprint', part.footprint, ox, oy, True),
                 ('Datasheet', part.fields.get('Datasheet', sym.datasheet), ox, oy, True)]
        for k, v in part.fields.items():
            if k != 'Datasheet':
                props.append((k, v, ox, oy, True))
        lines = ['(symbol (lib_id %s) (at %s %s 0) (unit %d)' % (q(self.libname + ':' + sym.name), f(ox), f(oy), unit),
                 '  (in_bom %s) (on_board yes) (dnp %s)' % ('no' if sym.power else 'yes', 'yes' if part.dnp else 'no'),
                 '  (uuid %s)' % U()]
        for k, v, x, y, hide in props:
            lines.append('  (property %s %s (at %s %s 0) (effects (font (size 1.27 1.27)) (justify left)%s))'
                         % (q(k), q(v), f(x), f(y), ' hide' if hide else ''))
        for p in sym.unit_pins(unit):
            lines.append('  (pin %s (uuid %s))' % (q(p.num), U()))
        lines.append('  (instances (project %s (path %s (reference %s) (unit %d))))'
                     % (q(self.name), q(path), q(part.ref), unit))
        lines.append(')')
        return '\n'.join(lines)
