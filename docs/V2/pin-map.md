# DIY Flow Bench V2.0 — ESP32-S3 pin map

Controller: **ESP32-S3-DevKitC-1-N32R8V** (ESP32-S3-WROOM-2-N32R8V module: 32 MB octal flash, 8 MB octal PSRAM, 1.8 V SPI).

All 24 general-purpose GPIO the DevKit exposes are assigned. Slow signals go through two TCA9535 I2C expanders. Analog inputs use ADC1 only, because ADC2 (GPIO11–20) can't be read while Wi-Fi is on.

The WIZ850io Ethernet module (W5500) plugs into the main board and has the SPI bus to itself. The microSD card is on its own bus, the ESP32-S3 SD host in 1-bit mode (3 pins), because the W5500 and an SD card sharing one SPI bus is a known source of failures. The pins came from moving the bleed stepper alarm to expander 2 and running the W5500 without its interrupt line (the driver polls it). Solder jumper JP3 connects the interrupt to expander 2 P06 if polling isn't enough, and JP1 can disconnect DAT0 from GPIO3 if the card ever upsets boot.

## GPIO

| GPIO | Header pin | Function | Dir | Peripheral | Notes |
| --- | --- | --- | --- | --- | --- |
| 0 | J3-14 | BOOT button | in | — | Strapping (boot mode). Not used. |
| 1 | J3-4 | Motor 1 current | in | ADC1 ch0 | CT, 1.65 V bias |
| 2 | J3-5 | Motor 2 current | in | ADC1 ch1 | CT, 1.65 V bias |
| 3 | J1-13 | microSD DAT0 | i/o | SD host (SDMMC), 1-bit | 10 k pull-up, which also keeps this strapping pin high at reset (JTAG over USB, the default) |
| 4 | J1-4 | Motor 3 current | in | ADC1 ch3 | CT, 1.65 V bias |
| 5 | J1-5 | Motor 4 current | in | ADC1 ch4 | CT, 1.65 V bias |
| 6 | J1-6 | Motor 5 current | in | ADC1 ch5 | CT, 1.65 V bias |
| 7 | J1-7 | Motor 6 current | in | ADC1 ch6 | CT, 1.65 V bias |
| 8 | J1-12 | MAF frequency | in | PCNT unit 0 | Schmitt buffer, for frequency-output MAFs |
| 9 | J1-15 | Swirl encoder A | in | PCNT unit 1 | Schmitt buffer, quadrature |
| 10 | J1-16 | Swirl encoder B | in | PCNT unit 1 | Schmitt buffer, quadrature |
| 11 | J1-17 | SPI MOSI | out | SPI2 | W5500 only |
| 12 | J1-18 | SPI SCK | out | SPI2 | W5500 only |
| 13 | J1-19 | SPI MISO | in | SPI2 | W5500 only |
| 14 | J1-20 | Ethernet CS | out | SPI2 | W5500 |
| 15 | J1-8 | I2C SDA | i/o | I2C0, 400 kHz | ADCs, mux, expanders, Digimatic interface |
| 16 | J1-9 | I2C SCL | out | I2C0 | 2.2 k pull-ups to 3.3 V |
| 17 | J1-10 | Bleed stepper step (PUL) | out | RMT | To AM26C31 #1, 200 kHz max |
| 18 | J1-11 | Bleed stepper direction | out | GPIO | To AM26C31 #1, set ≥5 µs before a step |
| 19 | J3-20 | USB D− | — | Native USB | Flashing, console, JTAG |
| 20 | J3-19 | USB D+ | — | Native USB | Flashing, console, JTAG |
| 21 | J3-18 | microSD CMD | i/o | SD host (SDMMC) | 10 k pull-up |
| 35–37 | J3-13…11 | Not available | — | — | Used by the octal flash and PSRAM |
| 38 | J3-10 | Status LED | out | RMT | RGB LED on the DevKit |
| 39 | J3-9 | Lift stepper step (PUL) | out | RMT | To AM26C31 #2 |
| 40 | J3-8 | Lift stepper direction | out | GPIO | To AM26C31 #2 |
| 41 | J3-7 | microSD CLK | out | SD host (SDMMC) | 33 Ω series resistor at the pin. DAT1–DAT3 get 10 k pull-ups and stay unconnected to the ESP32 |
| 42 | J3-6 | Expander interrupt | in | GPIO interrupt | Both TCA9535 INT lines, open drain, wired together |
| 43 | J3-2 | UART0 TX | out | UART0 | DevKit USB-UART port |
| 44 | J3-3 | UART0 RX | in | UART0 | DevKit USB-UART port |
| 45 | J3-15 | Not used | — | — | Strapping pin that sets flash voltage. Left unconnected. |
| 46 | J1-14 | Heartbeat | out | GPIO | To hardware watchdog. Strapping pin; held low at boot |
| 47 | J3-17 | Not used | — | — | Runs at 1.8 V on WROOM-2 modules |
| 48 | J3-16 | Not used | — | — | Runs at 1.8 V on WROOM-2 modules |

## TCA9535 I/O expander 1 (I2C 0x20)

| Pin | Function | Dir | Power-up state |
| --- | --- | --- | --- |
| P00–P05 | Contactor coils 1–6 (TBD62083 inputs 1–6) | out | Off (pull-down) |
| P06 | Motors-armed lamp (TBD62083 input 7) | out | Off (pull-down) |
| P07 | Bleed stepper 24 V power switch | out | Off (pull-down) |
| P10 | Bleed stepper enable (AM26C31 #1) | out | Disabled; polarity set at bring-up |
| P11 | WIZ850io reset | out | Running (pull-up) |
| P12 | E-stop status | in | Opto input |
| P13 | Bleed valve home switch | in | Opto input |
| P14–P16 | Orifice selector bits 0–2 | in | Opto inputs |
| P17 | microSD card detect | in | Pull-up |

## TCA9535 I/O expander 2 (I2C 0x21)

| Pin | Function | Dir | Power-up state |
| --- | --- | --- | --- |
| P00 | Lift stepper 24 V power switch | out | Off (pull-down) |
| P01 | Lift stepper enable (AM26C31 #2) | out | Disabled; polarity set at bring-up |
| P02 | Lift stepper alarm | in | Opto input |
| P03 | Lift actuator home switch | in | Opto input |
| P04 | Lift actuator max-travel switch | in | Opto input |
| P05 | Bleed stepper alarm | in | Opto input; reads active when the drive's alarm transistor turns on |
| P06 | WIZ850io interrupt | in | Only through solder jumper JP3; unused while the W5500 is polled |
| P07 | Input eFuse fault | in | TPS2663 FLT on the power module, open drain, active low; 10 k pull-up |
| P10–P17 | Spare | — | 8 pins free |

## I2C devices (I2C0, GPIO15/16)

| Address | Device | Purpose |
| --- | --- | --- |
| 0x20 | TCA9535 #1 | Coils, bleed stepper, switch inputs |
| 0x21 | TCA9535 #2 | Lift stepper and its limit switches |
| 0x30 | ATtiny1616 Digimatic interface | Reads the lift indicator |
| 0x40 | ADS1219 #1 | MAF, intake air temperature, rail checks |
| 0x41 | ADS1219 #2 | MAF harness ID, input current (eFuse IMON). On the main bus: at 0x40 behind the mux it would clash with #1 |
| 0x70 | TCA9548A | I2C multiplexer |
| 0x28 via mux ch0 | ABP2 | Reference (test) pressure |
| 0x28 via mux ch1 | ABP2 | Orifice differential pressure |
| 0x28 via mux ch2 | ABP2 | Pitot differential pressure |
| 0x77 via mux ch3 | SparkFun BME280 | Temperature, humidity, baro (external cable) |
| mux ch4–7 | Spare | |

## ADS1219 channels

| ADC | Input | Signal | Reference |
| --- | --- | --- | --- |
| #1 | AIN0 | MAF signal 0–5 V, through a 0.4 divider | Internal 2.048 V |
| #1 | AIN1 | MAF intake air temperature | External analog 5 V (ratiometric) |
| #1 | AIN2 | Analog 5 V rail check, 1/4 divider | Internal 2.048 V |
| #1 | AIN3 | 24 V input monitor, 1/16 divider | Internal 2.048 V |
| #2 | AIN1 | MAF harness ID resistor (10 k bias) | External analog 5 V |
| #2 | AIN0 | Input current from the power module (TPS2663 IMON, 10 k: about 1.7 V at 6 A) | Internal 2.048 V |
| #2 | AIN2, AIN3 | Spare (test points) | — |

## MAF harness ID resistors

10 kΩ bias to the analog 5 V, ID resistor from the ID pin to ground, 1%.

| ID resistor | Reading | Assigned to |
| --- | --- | --- |
| 1.0 kΩ | 0.45 V | Bosch 0280218335 |
| 1.5 kΩ | 0.65 V | |
| 2.2 kΩ | 0.90 V | |
| 3.3 kΩ | 1.24 V | |
| 4.7 kΩ | 1.60 V | |
| 6.8 kΩ | 2.02 V | |
| 10 kΩ | 2.50 V | |
| 15 kΩ | 3.00 V | |
| 22 kΩ | 3.44 V | |
| 33 kΩ | 3.84 V | |
| 47 kΩ | 4.12 V | |
| 68 kΩ | 4.36 V | |

No resistor (5 V) reads as unknown; a short (0 V) is a wiring fault.

## Stepper alarm inputs

The iCL42-08 alarm output (ALM+/ALM−) is an isolated, normally open collector: off while the drive is healthy, on when it faults. Each alarm drives an opto input:

- +5 V → 470 Ω → opto LED anode; LED cathode → ALM+; ALM− → ground. About 7 mA through the drive's transistor, inside its 30 mA rating.
- Opto on means alarm. Both alarms are on expander 2: bleed on P05, lift on P02. The expander interrupt (GPIO42) flags a change within a few milliseconds.

A normally open alarm isn't fail-safe: a broken alarm wire, or a drive that has lost power, reads the same as a healthy drive. The firmware only enables the vacuum motors after it has seen the drive answer (it moves to home and the home switch changes state). The drive's tuning software can also set the alarm to normally closed; if that's set later, the firmware's alarm polarity setting flips to match, with no hardware change.

## MAF inputs

The MAF connector (GX12 7-pin) has a separate pin for each signal type, so analog and digital MAFs plug into the same socket. The harness wires the MAF's signal to the matching pin and leaves the other one empty.

| Pin | Signal | Board circuit |
| --- | --- | --- |
| 1 | 12 V supply | Pololu 12 V, through a polyfuse |
| 2 | Ground | |
| 3 | Analog signal, 0–5 V | 1 k series, clamp, 0.4 divider (15 k over 10 k) to ADS1219 #1 AIN0 |
| 4 | Frequency signal, 0–5 V or open collector | 1 k series, 10 k pull-down, solder jumper for a 4.7 k pull-up to 5 V (open-collector MAFs), 74LVC14 (5 V-tolerant inputs, 3.3 V supply) to GPIO8, PCNT |
| 5 | Intake air temperature | Bias resistor from analog 5 V, to ADS1219 #1 AIN1. Value set to suit the MAF's sensor (for example 2.49 k for a 2.5 kΩ NTC) |
| 6 | 5 V reference | Analog 5 V, for MAFs that need a reference |
| 7 | Harness ID | 10 k bias to analog 5 V, to ADS1219 #2 AIN1 |

The pull-down keeps the frequency input quiet when an analog MAF is fitted, so it never counts noise. Each MAF's inventory entry records its signal type (analog or frequency) and transfer function (volts → kg/h, or Hz → kg/h); the firmware reads the harness ID, looks up the entry and reads only that input. The Bosch 0280218335 is analog, 0–5 V, ID 1.0 kΩ.
