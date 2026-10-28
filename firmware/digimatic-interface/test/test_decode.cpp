// Host test for digimatic_frame.h:  g++ -std=c++11 -I.. test_decode.cpp && ./a.out
#include <cstdio>
#include "digimatic_frame.h"

// Build a frame from nibbles d1..d13 (as Mitutoyo lists them).
static uint64_t frame(const uint8_t d[13]) {
  uint64_t b = 0;
  for (int i = 0; i < 13; i++) b |= (uint64_t)(d[i] & 0xF) << (4 * i);
  return b;
}

static int fails = 0;
static void expect(const char *name, const uint8_t d[13], DigimaticStatus st,
                   int32_t counts = 0, uint8_t dec = 0, uint8_t inch = 0) {
  DigimaticReading r{};
  DigimaticStatus got = digimaticDecode(frame(d), r);
  bool ok = got == st && (st != DIGI_OK || (r.counts == counts && r.decimals == dec && r.inch == inch));
  printf("%-28s %s\n", name, ok ? "pass" : "FAIL");
  if (!ok) { fails++; printf("   got status %d counts %ld dec %d inch %d\n", got, (long)r.counts, r.decimals, r.inch); }
}

int main() {
  const uint8_t mm[13]      = {15,15,15,15, 0, 0,1,2,3,4,5, 3, 0};  // +12.345 mm
  const uint8_t inchNeg[13] = {15,15,15,15, 8, 0,0,5,0,0,0, 4, 1};  // -0.5000 in
  const uint8_t full[13]    = {15,15,15,15, 0, 0,1,0,0,0,0, 4, 1};  // +1.0000 in
  const uint8_t zero[13]    = {15,15,15,15, 0, 0,0,0,0,0,0, 4, 1};  // 0.0000 in
  const uint8_t noHdr[13]   = { 5, 4, 3, 2, 1, 0,0,0,0,3,0, 0, 0};  // KK4HFJ example layout
  const uint8_t badDigit[13]= {15,15,15,15, 0, 0,1,10,3,4,5,3, 0};
  const uint8_t badSign[13] = {15,15,15,15, 1, 0,1,2,3,4,5, 3, 0};
  const uint8_t badPoint[13]= {15,15,15,15, 0, 0,1,2,3,4,5, 6, 0};
  const uint8_t badUnit[13] = {15,15,15,15, 0, 0,1,2,3,4,5, 3, 2};
  expect("+12.345 mm", mm, DIGI_OK, 12345, 3, 0);
  expect("-0.5000 in", inchNeg, DIGI_OK, -5000, 4, 1);
  expect("+1.0000 in (full travel)", full, DIGI_OK, 10000, 4, 1);
  expect("0.0000 in", zero, DIGI_OK, 0, 4, 1);
  expect("frame without header", noHdr, DIGI_BAD_HEADER);
  expect("digit above 9", badDigit, DIGI_BAD_DIGIT);
  expect("bad sign", badSign, DIGI_BAD_SIGN);
  expect("bad decimal position", badPoint, DIGI_BAD_POINT);
  expect("bad unit", badUnit, DIGI_BAD_UNIT);
  printf("%s\n", fails ? "SOME TESTS FAILED" : "all tests passed");
  return fails ? 1 : 0;
}
