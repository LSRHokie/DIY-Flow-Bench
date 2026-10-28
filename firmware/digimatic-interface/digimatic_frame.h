// digimatic_frame.h - decode a Mitutoyo Digimatic (SPC) 52-bit frame.
//
// Part of DIY Flow Bench V2 (GPLv3). The capture method used with this decoder
// (sample DATA on each CLK falling edge, 52 bits LSB-first, REQ to start) comes
// from KK4HFJ/mitutoyo-arduino, MIT License, Copyright (c) 2025 Steve Spence.
//
// Frame layout, as Mitutoyo publishes it: 13 nibbles d1..d13, each sent LSB first.
//   d1-d4   0xF header
//   d5      sign: 0 = positive, 8 = negative
//   d6-d11  six BCD digits, d6 most significant
//   d12     decimal point position: number of digits after the point (0-5)
//   d13     unit: 0 = mm, 1 = inch
// Note: the decode in KK4HFJ/mitutoyo-arduino v1.0.0 uses a different layout
// (8 digits first, no header). This file follows Mitutoyo's layout and rejects
// any frame whose header or digits don't fit it, so a wrong layout can't produce
// a plausible-looking number. Check against the indicator's display at bring-up.
#pragma once
#include <stdint.h>

enum DigimaticStatus : uint8_t {
  DIGI_OK          = 0,
  DIGI_BAD_HEADER  = 1,  // d1-d4 not all 0xF
  DIGI_BAD_SIGN    = 2,  // d5 not 0 or 8
  DIGI_BAD_DIGIT   = 3,  // a value digit above 9
  DIGI_BAD_POINT   = 4,  // decimal position above 5
  DIGI_BAD_UNIT    = 5,  // unit not 0 or 1
};

struct DigimaticReading {
  int32_t counts;     // signed value with the decimal point removed (12.345 -> 12345)
  uint8_t decimals;   // digits after the point
  uint8_t inch;       // 1 = inch, 0 = mm
};

// Nibble i (0-based, d1 = 0) of a frame captured LSB-first into a 64-bit word.
static inline uint8_t digimaticNibble(uint64_t bits, uint8_t i) {
  return (uint8_t)((bits >> (4u * i)) & 0xFu);
}

static inline DigimaticStatus digimaticDecode(uint64_t bits, DigimaticReading &out) {
  for (uint8_t i = 0; i < 4; i++)
    if (digimaticNibble(bits, i) != 0xF) return DIGI_BAD_HEADER;

  uint8_t sign = digimaticNibble(bits, 4);
  if (sign != 0 && sign != 8) return DIGI_BAD_SIGN;

  int32_t value = 0;
  for (uint8_t i = 5; i <= 10; i++) {          // d6 (MSD) .. d11 (LSD)
    uint8_t d = digimaticNibble(bits, i);
    if (d > 9) return DIGI_BAD_DIGIT;
    value = value * 10 + d;
  }

  uint8_t point = digimaticNibble(bits, 11);
  if (point > 5) return DIGI_BAD_POINT;
  uint8_t unit = digimaticNibble(bits, 12);
  if (unit > 1) return DIGI_BAD_UNIT;

  out.counts = (sign == 8) ? -value : value;
  out.decimals = point;
  out.inch = unit;
  return DIGI_OK;
}
