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
2. **ABP2 pinout and footprint:** from Honeywell's I2C table (1 VDD, 2 SCL, 3 EOC, 4 SDA, 5 GND, 6 NC). KiCad has no ABP2 footprint; one has to be drawn from the datasheet.
3. **WIZ850io:** two 1 × 6 sockets (J1: GND, GND, MOSI, SCLK, SCNn, INTn; J2: GND, 3V3D, 3V3D, NC, RSTn, MISO). Take their spacing from WIZnet's mechanical drawing.
4. **DevKit sockets:** the pin-by-pin map follows `docs/V2/pin-map.md`. Take the row spacing from Espressif's drawing.
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

## Regenerating

```
git clone --depth 1 https://github.com/KiCad/kicad-symbols.git   # KiCad 5 library, used for pinouts
pip install kiutils
cd hardware/kicad/tools
python3 design.py /path/to/kicad-symbols ..
cd .. && python3 tools/verify.py
```

Regenerating replaces both projects (new UUIDs), so any hand edits in the schematic files would be lost.
