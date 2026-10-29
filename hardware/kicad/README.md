# DIY Flow Bench V2 — KiCad schematics, rev A

Two KiCad projects, generated from `tools/design.py`:

| Project | Open | Contents |
| --- | --- | --- |
| `flowbench-main/` | `flowbench-main.kicad_pro` | Main board, 6 sheets: Power, Controller, Network and storage, Sensors and ADC, Field inputs, IO and safety. 239 parts, 180 nets. |
| `flowbench-power-module/` | `flowbench-power-module.kicad_pro` | PM1, the plug-in input power module: TPS26631 eFuse with reverse blocking, TPS7A4901 analog 5 V. 33 parts. |

The files are KiCad 7 format and open in KiCad 7, 8 and 9 (8 and 9 offer to upgrade the format when you save). Each project carries its own symbol library (`FlowBench.kicad_sym`, registered in `sym-lib-table`) and, for footprints KiCad lacks, a footprint library (`FlowBench.pretty`, registered in `fp-lib-table`), so nothing else needs installing.

## How the schematic is drawn

Every pin has a short wire and a net label; connections are made by net name, not by drawn wires. Labels that cross sheets are global labels. Unused pins carry a no-connect flag. This keeps the schematic exact and easy to regenerate, but it reads as a netlist, not a hand-drawn diagram. Feel free to tidy any sheet by hand once it's settled, but after that, don't regenerate it.

Notes at the top of each sheet explain the design choices on that sheet. `netlist.csv` in each project lists every net and pin.

## What was checked

- Every file parses with [kiutils](https://github.com/mvnmgrx/kiutils), an independent KiCad file library.
- `tools/verify.py` rebuilds connectivity from the files alone (pin positions, wires, labels, no-connect flags) and matches it net for net against `netlist.csv`. Result: identical, no unconnected pins.
- Every net has at least two connections; every power-input pin has a driver; no net has two power outputs.
- **Not checked:** KiCad itself couldn't be run where these were generated, so run ERC first thing (Inspect → Electrical Rules Checker) and send me anything it reports.

## Review checklist

Symbols converted from KiCad's library keep KiCad's pinouts. These need your eye:

1. **Pololu D24V22F5 / F12:** pinout confirmed from the board (PG, EN, VIN, GND, VOUT down one edge, plus a corner GND level with PG). Its footprint is `FlowBench:Pololu_D24V22Fx` in the project's own footprint library. The corner pad sits 0.4 in from the row, read from Pololu's photo: check it with a caliper before ordering boards.
2. **ABP2:** pinout from Honeywell datasheet 32350268, Table 21 (I2C: 1 GND, 2 VDD, 3 EOC, 4 NC, 5 SDA, 6 SCL). Footprint `FlowBench:Honeywell_ABP2_DIP` from Figure 13: 2.54 mm pitch, rows 11.00 mm apart, 0.73 mm holes. The barbed ports leave the body on the pin 3/4 side; leave room there for the tubing.
3. **WIZ850io:** confirmed from the module (20 × 25 mm, two 1 × 6 headers). One part and one footprint, `FlowBench:WIZ850io`: J1 is pads 1–6, J2 is pads 7–12, rows 17.78 mm (0.7 in) apart, pin 1 nearest the RJ45. Place it with the jack facing the board edge.
4. **DevKit:** header pinout confirmed against Espressif's J1/J3 tables, row spacing measured at 25.4 mm (1.0 in). One part and one footprint, `FlowBench:ESP32-S3-DevKitC-1`: J1 is pads 1–22, J3 is pads 23–44, pin 1 at the antenna end. Let the antenna overhang the board edge or keep copper out from under it. The N32R16V variant fits the same footprint.
5. **Custom symbols** drawn from datasheets: ADS1219 (TSSOP-16), AM26C31 (SOIC-16), TPS7A4901 (MSOP-8 PowerPAD). Worth one look each against the datasheet pin table.
6. **Footprint names** follow KiCad's standard libraries. If KiCad flags one as missing when you update the PCB, it's a name to pick from your library, not a circuit problem. The microSD socket (Hirose DM3AT) and the TLP291-4 footprint are the likeliest.
7. **TPS26631 choices** on the power module: PGTH and PGOOD tied to GND (power-good unused), SHDN left open (internal pull-up), MODE open (latch-off). The library symbol has pin 20 as OUT; TI's pin table lists it as N.C., so tying it to OUT is harmless.
8. **Digimatic inverter footprints** (the NPNs on CLK and DATA) are marked DNP. JP4/JP5 default to the direct path (pads 1–2). Bench check 1 decides.

## Changes from the earlier docs found while drawing this

- **ADS1219 #2 moved to the main I2C bus at 0x41.** At 0x40 behind multiplexer channel 4, it would clash with ADS1219 #1 (also 0x40) whenever that channel was open.
- **74HCT123** instead of 74HC123: at 5 V, a 74HC input needs 3.5 V for a high, more than the ESP32's 3.3 V heartbeat.
- **TPS2663 reverse polarity needs two external FETs** (PM1-Q1 blocking FET, PM1-Q2 BSS138), per TI's application circuit. The part is the TPS26631PWP, HTSSOP-20.
- **Input TVS is SMCJ51CA:** its 51 V stand-off keeps it off if the 48 V supply is plugged in by mistake, and the eFuse overvoltage cut-off disconnects the board.
- **eFuse current monitor** goes to ADS1219 #2 AIN0, so the firmware can read the bench's 24 V current.
- **WIZ850io headers are 1 × 6,** not 2 × 6.

## Board placement (rev A)

`flowbench-main/place_rev_a.py` lays out the main board as a starting point for routing:

- 220 × 160 mm outline, M3 mounting holes in the corners.
- Top edge: 24 V input, stepper power and signals, motor-housing coils, lamp, E-stop. Bottom edge: MAF, current sensors, swirl, Digimatic, BME280, switches, orifice selector. The script turns each connector so its plug faces out.
- DevKit antenna overhangs the left edge; WIZ850io RJ45 faces the right edge; ABP2 ports face the right edge.
- ICs and modules at planned spots; every resistor, capacitor and small part packed next to the part it serves, at least 1 mm apart, for hand soldering.

To run it:
1. In the schematic: Tools → Update PCB from Schematic (F8). This brings in the four mounting holes as well.
2. In the PCB editor: Tools → Scripting Console, then `exec(open(r"<path>/place_rev_a.py").read())`
3. It prints how many parts it placed and lists any it couldn't.

The script also:
- keeps everything at least 3 mm clear of the mounting holes;
- moves part values to the fabrication layer, so only references print on the silkscreen;
- adds a GND plane on the bottom layer, notched under the DevKit antenna, with an antenna keepout on both layers.

`placement-preview.png` is a simulation of the same placement, using approximate part sizes. The real result uses KiCad's actual footprint outlines, so expect small differences. Nothing is routed. Adjust placement by hand, then route (by hand, or with the Freerouting plugin as a first pass).

## Routing setup

The project file defines net classes, so KiCad's router and DRC use the right widths automatically (1 oz copper, about a 10 °C rise):

| Class | Track | Clearance | Via | Nets |
| --- | --- | --- | --- | --- |
| Power24 | 2.5 mm | 0.3 mm | 1.0 / 0.5 mm | +24V_RAW, +24V (up to ~6 A) |
| Stepper24 | 1.2 mm | 0.3 mm | 0.8 / 0.4 mm | Bleed and lift stepper 24 V (3 A peak) |
| Coil24 | 0.8 mm | 0.3 mm | 0.8 / 0.4 mm | Coil supply, coil and lamp returns |
| Supply | 0.8 mm | 0.2 mm | 0.8 / 0.4 mm | +5V, +12V, GND, MAF 12 V |
| Rail | 0.5 mm | 0.2 mm | 0.6 / 0.3 mm | +3V3, +5VA |
| Field24 | 0.4 mm | 0.3 mm | 0.6 / 0.3 mm | 24 V switch, orifice and E-stop wiring |
| Default | 0.25 mm | 0.2 mm | 0.6 / 0.3 mm | All other signals |

Routing tips:
- Keep the bottom layer as an unbroken ground plane: route on top, and use the bottom only for short jumps. Most important under the SPI lines from the DevKit to the WIZ850io (about 13 cm) and the I2C lines.
- Keep the analog area (ADS1219s, MAF and current-sensor inputs) away from the stepper and coil wiring.
- Wide 24 V tracks: draw them first, then everything else.

Schematic UUIDs are stable from this version on, so regenerating no longer breaks the link between the schematic and the PCB.

## Regenerating

```
git clone --depth 1 https://github.com/KiCad/kicad-symbols.git   # KiCad 5 library, used for pinouts
pip install kiutils
cd hardware/kicad/tools
python3 design.py /path/to/kicad-symbols ..
cd .. && python3 tools/verify.py
```

Regenerating rewrites both projects, so any hand edits in the schematic files would be lost. Symbol, sheet and root UUIDs are derived from the design, so the PCB stays linked.
