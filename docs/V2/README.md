# DIY Flow Bench V2.0

V2.0 is a redesign of the DIY Flow Bench hardware and firmware, forked from [DeeEmm/DIY-Flow-Bench](https://github.com/DeeEmm/DIY-Flow-Bench) V2.0-RC9 and the V2.3 shield.

The goal is **one fixed build**: the only part that varies between benches is the MAF sensor. Component options and alternate footprints from V2.3 are removed, and the bench gains closed-loop vacuum control, automated valve-lift testing and MAF verification against orifice and pitot measurements.

## Files

| File | Contents |
| --- | --- |
| [pin-map.md](pin-map.md) | ESP32-S3 GPIO, I/O expander, I2C address and ADC channel maps |
| [bom.csv](bom.csv) | Current bill of materials |

## Architecture

- **Controller:** ESP32-S3-DevKitC-1-N32R8V (32 MB flash, 8 MB PSRAM), plugged into the main PCB. Web interface over Ethernet (W5500, alone on the SPI bus), with Wi-Fi as fallback. microSD on its own SD host bus (1-bit mode).
- **Pressure:** three Honeywell ABP2 digital sensors (±100 mbar, I2C) for reference, orifice and pitot, through a TCA9548A multiplexer.
- **MAF:** analog (0–5 V, 24-bit ADS1219) and frequency (Schmitt buffer to a hardware counter) inputs on separate pins of one connector; the harness ID tells the firmware which MAF, and which input, is in use. A second ADS1219 reads the harness ID.
- **Environment:** SparkFun BME280 on a short cable at the enclosure air inlet.
- **Power:** 24 V via a panel XT90, 7 A panel breaker and TPS2663 input eFuse (cuts out above about 32 V). Pololu 5 V and 12 V regulators, low-noise TPS7A4901 analog 5 V, LM1117 3.3 V.
- **Vacuum motors:** up to six Ametek Lamb 122165-00 (240 V), each switched at 100% by a 24 V DC-coil DIN-rail contactor in a separate housing. No mains on the PCB. One 60 A, 240 V supply to the housing.
- **Vacuum control:** firmware stages motors one at a time and holds the target test pressure with a closed-loop bleed valve (StepperOnline iCL42-08).
- **Motor monitoring:** a current transformer on each motor confirms it started and flags faults.
- **Valve lift:** a second iCL42-08 on a T8 lead screw opens the valve; a Digimatic indicator (Mitutoyo 575-123 or any Digimatic-output indicator) measures lift, read by an ATtiny1616 interface ([firmware](../../firmware/digimatic-interface), capture method from [KK4HFJ/mitutoyo-arduino](https://github.com/KK4HFJ/mitutoyo-arduino)).
- **Safety:** hardwired E-stop on the coil supply, a hardware heartbeat watchdog that drops all coils if the firmware stops, outputs off at power-up, and firmware interlocks (stepper alarm, over-vacuum, run time, lost connection, motor not drawing current).
- **Assembly:** all parts hand-solderable; finest pitch is the W5500 (LQFP-48, 0.5 mm).

## Status

1. **Prototype (current):** DevKit plus off-the-shelf breakouts on the bench, to prove the separate Ethernet and microSD buses, the Digimatic interface, the iCL42-08 enable polarity, and the Bosch 0280218335 MAF's pinout and current.
2. **Schematic and PCB in KiCad,** after the prototype.
3. **Firmware:** port to the newer ESP32 Arduino core, then motor staging and bleed control, the lift sweep, and the MAF inventory and verification with shareable calibration files.

## Firmware fixes already made on this branch

- Missing `break` after the ±7 kPa XGZP6899A case in the three pressure conversions.
- BME280 start-up no longer freezes the controller when no sensor answers.
- Supply-voltage helpers returned millivolts instead of volts.
- `platformio.ini` `data_dir` path case, which broke builds on Linux.
- `sensors.cpp` included `mafData.h`, but the file is `mafdata.h`, which broke builds on Linux.
- `API.cpp` used the ESP32-only ROM CRC header; it now uses `esp_rom_crc.h`, which works on the ESP32 and the ESP32-S3.

## Building for the V2 controller

The default PlatformIO environment is `esp32s3-n32r8v`: the ESP32-S3-DevKitC-1-N32R8V on the pioarduino platform (ESP32 Arduino core 3.x), with octal flash and PSRAM and the 32 MB partition table `partitions-s3-32MB.csv` (two 6 MB app slots for OTA updates, 8 MB SPIFFS, about 12 MB left free for later). The firmware compiles for this target on core 3.3.12: about 1.24 MB of program and 86 KB of static RAM. The serial console is the DevKit's native USB port.

The old `esp32dev` environment is kept for the original board until the V2 firmware drops it.

## License

Firmware: GPLv3. Hardware: CERN-OHL-W, as for the original project. Derivative designs must credit the original and be published.
