"""footprints.py - project footprints that KiCad's libraries don't have.

Written to <project>/FlowBench.pretty and registered in the project's fp-lib-table.
Coordinates in mm, KiCad 7 footprint format.
"""


def _pad(num, x, y, shape='circle', size=1.7, drill=1.0):
    return ('  (pad "%s" thru_hole %s (at %g %g) (size %g %g) (drill %g) (layers "*.Cu" "*.Mask"))'
            % (num, shape, x, y, size, size, drill))


def _rect(x0, y0, x1, y1, layer, width):
    return ('  (fp_rect (start %g %g) (end %g %g) (stroke (width %g) (type solid)) (fill none) (layer "%s"))'
            % (x0, y0, x1, y1, width, layer))


def pololu_d24v22fx():
    """Pololu D24V22Fx (0.7 x 0.7 in), plugged into female sockets on the main board.

    From Pololu's labelled top view: PG, EN, VIN, GND, VOUT down the left edge at
    0.1 in pitch (pins 1-5), and a second GND (pin 6) in the top-right corner, level
    with PG and four pitches (0.4 in) to the right. Board outline is approximate
    (fab layer only). Check the pin-6 offset with a caliper before ordering boards.
    """
    p = 2.54
    out = ['(footprint "Pololu_D24V22Fx" (version 20221018) (generator kicadgen) (layer "F.Cu")',
           '  (descr "Pololu D24V22Fx step-down regulator, 5 pins at 0.1 in plus corner GND, on sockets")',
           '  (tags "Pololu regulator D24V22F5 D24V22F12")',
           '  (attr through_hole)',
           '  (fp_text reference "REF**" (at 4.5 -2.6) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
           '  (fp_text value "Pololu_D24V22Fx" (at 8 18) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
           _rect(-1.07, -1.17, 16.71, 16.61, 'F.Fab', 0.1),
           _rect(-1.27, -1.37, 16.91, 16.81, 'F.SilkS', 0.12),
           _rect(-1.57, -1.67, 17.21, 17.11, 'F.CrtYd', 0.05),
           '  (fp_text user "PG" (at 1.9 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify left)))',
           '  (fp_text user "EN" (at 1.9 %g) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify left)))' % p,
           '  (fp_text user "VIN" (at 1.9 %g) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify left)))' % (2 * p),
           '  (fp_text user "GND" (at 1.9 %g) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify left)))' % (3 * p),
           '  (fp_text user "VOUT" (at 1.9 %g) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify left)))' % (4 * p),
           _pad('1', 0, 0, 'rect')]
    for i in range(1, 5):
        out.append(_pad(str(i + 1), 0, i * p))
    out.append(_pad('6', 4 * p, 0))
    out.append(')')
    return '\n'.join(out) + '\n'


def wiz850io():
    """WIZnet WIZ850io (20 x 25 mm), plugged into two 1x6 female sockets.

    J1 (GND, GND, MOSI, SCLK, SCNn, INTn) is pads 1-6 on the left; J2 (GND, 3V3D,
    3V3D, NC, RSTn, MISO) is pads 7-12 on the right, 17.78 mm (0.7 in) across, both
    with pin 1 nearest the RJ45 jack. Top view, jack toward the top (negative y):
    place it with the jack facing the board edge. Module outline is approximate
    (fab layer only); the jack's metal shell overhangs it slightly.
    """
    p, w = 2.54, 17.78
    cx = w / 2
    x0, x1, y0, y1 = cx - 10, cx + 10, -7.0, 18.0
    out = ['(footprint "WIZ850io" (version 20221018) (generator kicadgen) (layer "F.Cu")',
           '  (descr "WIZnet WIZ850io W5500 module, two 1x6 2.54 mm sockets 17.78 mm apart")',
           '  (tags "WIZ850io W5500 Ethernet module")',
           '  (attr through_hole)',
           '  (fp_text reference "REF**" (at %g %g) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))' % (cx, y1 + 1.8),
           '  (fp_text value "WIZ850io" (at %g %g) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))' % (cx, 6.35),
           _rect(x0, y0, x1, y1, 'F.Fab', 0.1),
           _rect(x0 - 0.2, y0 - 0.2, x1 + 0.2, y1 + 0.2, 'F.SilkS', 0.12),
           _rect(x0 - 0.5, y0 - 1.5, x1 + 0.5, y1 + 0.5, 'F.CrtYd', 0.05),
           '  (fp_text user "RJ45 this side" (at %g %g) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))' % (cx, y0 + 1.2),
           '  (fp_text user "J1" (at -1.9 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify right)))',
           '  (fp_text user "J2" (at %g 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12)) (justify left)))' % (w + 1.9)]
    for i in range(6):
        out.append(_pad(str(i + 1), 0, i * p, 'rect' if i == 0 else 'circle'))
    for i in range(6):
        out.append(_pad(str(i + 7), w, i * p, 'rect' if i == 0 else 'circle'))
    out.append(')')
    return '\n'.join(out) + '\n'


ALL = {'Pololu_D24V22Fx': pololu_d24v22fx, 'WIZ850io': wiz850io}
