# Digimatic interface (ATtiny1616)

Reads a Digimatic (SPC) indicator, such as the Mitutoyo 575-123 on the valve-lift actuator, and gives the reading to the ESP32 over I2C at address 0x30. The Digimatic clock is too fast to read through the I2C expanders, and no ESP32 pin is free, so a small helper chip does it.

## Credit

The capture method comes from [KK4HFJ/mitutoyo-arduino](https://github.com/KK4HFJ/mitutoyo-arduino) (MIT License, Copyright (c) 2025 Steve Spence): pull REQ low, then sample DATA on each CLK falling edge, 52 bits, LSB first.

Changes from that sketch:

- Runs on an ATtiny1616 and answers on I2C instead of printing to serial.
- REQ is driven through an NPN transistor, so the ATtiny sets its pin high to request a reading. REQ is released as soon as the indicator starts clocking.
- Bits are stored a byte at a time to keep the interrupt short on an AVR.
- The decoder follows the frame layout Mitutoyo publishes (four 0xF header nibbles, sign, six digits most significant first, decimal position, unit). The v1.0.0 sketch decodes a different layout. Frames that don't fit are rejected, never turned into a wrong number.

## Files

| File | Contents |
| --- | --- |
| `digimatic-interface.ino` | ATtiny1616 firmware |
| `digimatic_frame.h` | Frame decoder, usable on any C++ compiler |
| `test/test_decode.cpp` | Host test for the decoder: `g++ -std=c++11 -I.. test_decode.cpp && ./a.out` |

## Building

Arduino IDE or arduino-cli with [megaTinyCore](https://github.com/SpenceKonde/megaTinyCore): board ATtiny1616, clock 10 MHz or faster, millis enabled, programmed over UPDI (a USB-serial adapter and a 4.7 kΩ resistor work as the programmer). The prototype uses the Adafruit ATtiny1616 breakout (5690).

This sketch hasn't been compiled for the ATtiny yet; the decoder passes its host tests.

## I2C registers

Write the register number, then read.

| Register | Length | Contents |
| --- | --- | --- |
| 0x00 | 10 | Status (bit 0 reading valid, bit 1 no indicator, bit 2 bad frame), sequence number, counts (int32 LE, point removed), decimals, unit (0 mm, 1 inch), age in ms (uint16 LE) |
| 0x10 | 7 | Last raw frame, nibbles d1–d13, LSB first |
| 0x20 | 1 | Error code of the last bad frame |

## Bring-up check

With the indicator connected, read register 0x10 and compare the raw nibbles with the display at 0, 0.5 and 1.0 in, and in mm. If the header nibbles aren't 0xF or the digits don't match, look at CLK and DATA on a scope; if they arrive inverted, set `INVERT_INPUTS`.
