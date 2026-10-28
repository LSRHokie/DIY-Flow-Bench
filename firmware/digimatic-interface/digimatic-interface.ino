// digimatic-interface.ino - ATtiny1616 Digimatic (SPC) to I2C interface.
//
// Part of DIY Flow Bench V2 (GPLv3). Board: ATtiny1616 with megaTinyCore,
// 10 MHz or faster, programmed over UPDI. Answers on I2C address 0x30.
//
// Frame capture follows KK4HFJ/mitutoyo-arduino (MIT License, Copyright (c) 2025
// Steve Spence): pull REQ low, the indicator clocks out 52 bits, DATA is sampled
// on each CLK falling edge, LSB first. Decoding is in digimatic_frame.h.
//
// Hardware (see docs/V2/pin-map.md):
//   PA4  CLK in   (10 k pull-up to 3.3 V on the board)
//   PA5  DATA in  (10 k pull-up to 3.3 V on the board)
//   PA6  REQ out  drives an NPN; HIGH here pulls the indicator's REQ low
//   PB1  SDA, PB0 SCL  (main I2C bus)
//
// I2C registers (write the register number, then read):
//   0x00  result, 10 bytes:
//         [0] status: bit0 reading valid, bit1 no indicator (timeout), bit2 bad frame
//         [1] sequence number, increments with each good frame
//         [2..5] counts, int32 little-endian (value with the point removed)
//         [6] decimals   [7] unit (0 mm, 1 inch)
//         [8..9] age of the reading in ms, uint16 little-endian (saturates)
//   0x10  last raw frame, 7 bytes, nibbles d1..d13 LSB first (for bring-up checks)
//   0x20  decode error code of the last bad frame (see DigimaticStatus)

#include <Wire.h>
#include "digimatic_frame.h"

#define I2C_ADDRESS   0x30
#define CLK_PIN       PIN_PA4
#define DATA_PIN      PIN_PA5
#define REQ_PIN       PIN_PA6

// Set true if CLK and DATA reach the ATtiny through inverting transistor stages.
const bool INVERT_INPUTS = false;

const uint16_t REQ_MAX_MS       = 120;  // longest REQ pulse (as in KK4HFJ)
const uint16_t FRAME_TIMEOUT_MS = 200;  // no full frame by then: no indicator
const uint16_t READ_INTERVAL_MS = 50;   // about 10 readings per second

volatile uint8_t frameBytes[7];   // filled LSB first; byte stores keep the ISR short on AVR
volatile uint8_t bitCount = 0;

volatile uint8_t regPointer = 0;
volatile uint8_t result[10];
volatile uint8_t rawFrame[7];
volatile uint8_t lastError = 0;

uint8_t  sequence = 0;
uint32_t lastGoodMs = 0;
bool     haveReading = false;

void onClockFalling() {
  uint8_t bit = digitalReadFast(DATA_PIN) ? 1 : 0;
  if (INVERT_INPUTS) bit ^= 1;
  if (bitCount < 52) {
    if (bit) frameBytes[bitCount >> 3] |= (uint8_t)(1u << (bitCount & 7));
    bitCount++;
  }
}

void onI2cReceive(int count) {
  if (count > 0) regPointer = Wire.read();
  while (Wire.available()) Wire.read();
}

void onI2cRequest() {
  if (regPointer == 0x00) {
    uint32_t age = haveReading ? millis() - lastGoodMs : 0xFFFF;
    result[8] = age > 0xFFFF ? 0xFF : (uint8_t)age;
    result[9] = age > 0xFFFF ? 0xFF : (uint8_t)(age >> 8);
    for (uint8_t i = 0; i < 10; i++) Wire.write(result[i]);
  } else if (regPointer == 0x10) {
    for (uint8_t i = 0; i < 7; i++) Wire.write(rawFrame[i]);
  } else if (regPointer == 0x20) {
    Wire.write(lastError);
  } else {
    Wire.write(0xFF);
  }
}

// Returns true and the 52 bits when a full frame arrives in time.
bool captureFrame(uint64_t &bits) {
  noInterrupts();
  for (uint8_t i = 0; i < 7; i++) frameBytes[i] = 0;
  bitCount = 0;
  interrupts();

  attachInterrupt(digitalPinToInterrupt(CLK_PIN), onClockFalling,
                  INVERT_INPUTS ? RISING : FALLING);
  digitalWriteFast(REQ_PIN, HIGH);              // NPN on: REQ low

  uint32_t t0 = millis();
  bool reqOn = true;
  uint8_t n;
  do {
    noInterrupts(); n = bitCount; interrupts();
    // Release REQ once the indicator has started clocking, or after REQ_MAX_MS.
    if (reqOn && (n > 0 || millis() - t0 >= REQ_MAX_MS)) {
      digitalWriteFast(REQ_PIN, LOW);
      reqOn = false;
    }
  } while (n < 52 && millis() - t0 < FRAME_TIMEOUT_MS);

  digitalWriteFast(REQ_PIN, LOW);
  detachInterrupt(digitalPinToInterrupt(CLK_PIN));
  if (n < 52) return false;

  bits = 0;
  for (uint8_t i = 0; i < 7; i++) bits |= (uint64_t)frameBytes[i] << (8 * i);
  return true;
}

void publish(uint8_t status, const DigimaticReading *r) {
  noInterrupts();
  result[0] = status;
  result[1] = sequence;
  if (r) {
    uint32_t c = (uint32_t)r->counts;
    result[2] = c; result[3] = c >> 8; result[4] = c >> 16; result[5] = c >> 24;
    result[6] = r->decimals;
    result[7] = r->inch;
  }
  interrupts();
}

void setup() {
  pinMode(CLK_PIN, INPUT);
  pinMode(DATA_PIN, INPUT);
  pinMode(REQ_PIN, OUTPUT);
  digitalWriteFast(REQ_PIN, LOW);               // REQ released

  publish(0x02, nullptr);                       // no reading yet
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(onI2cReceive);
  Wire.onRequest(onI2cRequest);
}

void loop() {
  uint64_t bits;
  if (!captureFrame(bits)) {
    publish(0x02 | (haveReading ? 0x01 : 0x00), nullptr);  // keep last value, flag timeout
    delay(READ_INTERVAL_MS);
    return;
  }

  noInterrupts();
  for (uint8_t i = 0; i < 7; i++) rawFrame[i] = (uint8_t)(bits >> (8 * i));
  interrupts();

  DigimaticReading r;
  DigimaticStatus s = digimaticDecode(bits, r);
  if (s == DIGI_OK) {
    sequence++;
    lastGoodMs = millis();
    haveReading = true;
    publish(0x01, &r);
  } else {
    lastError = s;
    publish(0x04 | (haveReading ? 0x01 : 0x00), nullptr);
  }
  delay(READ_INTERVAL_MS);
}
