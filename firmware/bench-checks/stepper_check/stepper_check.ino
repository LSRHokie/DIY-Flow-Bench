// stepper_check.ino - DIY Flow Bench V2 bench check 3 (GPLv3).
// Finds the iCL42-08 enable level and confirms the alarm input, using the
// DevKit and an AM26C31 line driver. Serial commands at 115200:
//   f / r     run 1 revolution forward / reverse (1600 steps, slow)
//   e         toggle the enable output (note which level frees the shaft)
//   a         print the alarm input
//
// Wiring for this check (the PCB uses the expanders for enable and alarm):
//   GPIO17 -> AM26C31 in A -> PUL+/PUL-     GPIO18 -> in B -> DIR+/DIR-
//   GPIO5  -> in C -> ENA+/ENA-             AM26C31 enable pins high, 5 V supply
//   Alarm: +5 V -> 470 ohm -> opto LED anode, cathode -> ALM+, ALM- -> GND;
//          opto output to GPIO6 with a 10 k pull-up to 3.3 V (low = alarm)
//   iCL42-08 at 24 V, DIP SW6 off (closed loop), 1600 pulses per revolution.

#define PIN_STEP  17
#define PIN_DIR   18
#define PIN_ENA   5
#define PIN_ALARM 6

const uint32_t STEPS_PER_REV = 1600;
const uint32_t STEP_HALF_US  = 300;      // about 1.04 rev/s

bool enaLevel = false;

void move(bool forward) {
  digitalWrite(PIN_DIR, forward ? HIGH : LOW);
  delayMicroseconds(10);                  // DIR at least 5 us before PUL
  for (uint32_t i = 0; i < STEPS_PER_REV; i++) {
    digitalWrite(PIN_STEP, HIGH); delayMicroseconds(STEP_HALF_US);
    digitalWrite(PIN_STEP, LOW);  delayMicroseconds(STEP_HALF_US);
    if (digitalRead(PIN_ALARM) == LOW) { Serial.printf("ALARM after %lu steps\n", i); return; }
  }
  Serial.println("move done");
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_STEP, OUTPUT); pinMode(PIN_DIR, OUTPUT); pinMode(PIN_ENA, OUTPUT);
  pinMode(PIN_ALARM, INPUT);
  digitalWrite(PIN_ENA, enaLevel ? HIGH : LOW);
  delay(1500);
  Serial.println("\nBench check 3: f/r move, e toggle enable, a alarm");
  Serial.printf("ENA output starts %s\n", enaLevel ? "HIGH" : "LOW");
}

void loop() {
  static bool lastAlarm = false;
  bool alarm = digitalRead(PIN_ALARM) == LOW;
  if (alarm != lastAlarm) { Serial.printf("alarm %s\n", alarm ? "ON" : "off"); lastAlarm = alarm; }

  if (!Serial.available()) return;
  char c = Serial.read();
  if (c == 'f') move(true);
  else if (c == 'r') move(false);
  else if (c == 'e') {
    enaLevel = !enaLevel;
    digitalWrite(PIN_ENA, enaLevel ? HIGH : LOW);
    Serial.printf("ENA output now %s: try turning the shaft by hand\n", enaLevel ? "HIGH" : "LOW");
  } else if (c == 'a') Serial.printf("alarm input %s\n", alarm ? "ON" : "off");
}
