// eth_sd_check.ino - DIY Flow Bench V2 bench check 2 (GPLv3).
// Proves the WIZ850io (W5500, polled, alone on SPI) and the microSD card (SD host,
// 1-bit mode, its own pins) work together on the ESP32-S3-DevKitC-1-N32R8V.
//
// Board: ESP32S3 Dev Module, Flash OPI 32 MB, PSRAM OPI, USB CDC on boot enabled.
// Wiring (docs/V2/pin-map.md):
//   WIZ850io  MOSI GPIO11, SCLK GPIO12, MISO GPIO13, SCNn GPIO14, RSTn GPIO4
//             (expander 1 P11 on the PCB; a spare GPIO here), INTn not connected, 3.3 V, GND
//   microSD   CLK GPIO41 (33 ohm series), CMD GPIO21, DAT0 GPIO3, 10 k pull-ups on
//             CMD and DAT0-DAT3, 3.3 V, GND
//
// Open http://<ip>/ to see the counters. Reload it repeatedly (or run a ping) while
// the SD test loops: both counters should keep rising with zero errors.

#include <ETH.h>
#include <SPI.h>
#include <SD_MMC.h>
#include <WebServer.h>

#define ETH_CS    14
#define ETH_RST   4
#define ETH_IRQ   -1     // polled: no interrupt line
#define SPI_MOSI  11
#define SPI_SCK   12
#define SPI_MISO  13
#define SD_CLK    41
#define SD_CMD    21
#define SD_D0     3

WebServer server(80);
volatile bool ethUp = false;
uint32_t sdPasses = 0, sdErrors = 0, pageHits = 0;
uint32_t lastWriteKBps = 0, lastReadKBps = 0;

void onEvent(arduino_event_id_t event) {
  switch (event) {
    case ARDUINO_EVENT_ETH_GOT_IP:
      Serial.printf("ETH got IP %s, link %u Mbps %s duplex\n", ETH.localIP().toString().c_str(),
                    ETH.linkSpeed(), ETH.fullDuplex() ? "full" : "half");
      ethUp = true; break;
    case ARDUINO_EVENT_ETH_DISCONNECTED: Serial.println("ETH link down"); ethUp = false; break;
    default: break;
  }
}

void handleRoot() {
  pageHits++;
  String s = "<h1>Bench check 2</h1><pre>";
  s += "Uptime s:      " + String(millis() / 1000) + "\n";
  s += "Page hits:     " + String(pageHits) + "\n";
  s += "SD passes:     " + String(sdPasses) + "\n";
  s += "SD errors:     " + String(sdErrors) + "\n";
  s += "SD write KB/s: " + String(lastWriteKBps) + "\n";
  s += "SD read KB/s:  " + String(lastReadKBps) + "\n</pre>";
  s += "<script>setTimeout(()=>location.reload(),1000)</script>";
  server.send(200, "text/html", s);
}

// Write 256 KB of a known pattern, read it back and compare.
bool sdPass() {
  const size_t CHUNK = 4096, TOTAL = 256 * 1024;
  static uint8_t buf[CHUNK], chk[CHUNK];
  File f = SD_MMC.open("/check.bin", FILE_WRITE);
  if (!f) return false;
  uint32_t t0 = millis();
  for (size_t off = 0; off < TOTAL; off += CHUNK) {
    for (size_t i = 0; i < CHUNK; i++) buf[i] = (uint8_t)((off + i) * 31 + sdPasses);
    if (f.write(buf, CHUNK) != CHUNK) { f.close(); return false; }
    server.handleClient();                       // keep Ethernet busy during the test
  }
  f.close();
  uint32_t t1 = millis();
  f = SD_MMC.open("/check.bin", FILE_READ);
  if (!f) return false;
  for (size_t off = 0; off < TOTAL; off += CHUNK) {
    if (f.read(chk, CHUNK) != CHUNK) { f.close(); return false; }
    for (size_t i = 0; i < CHUNK; i++)
      if (chk[i] != (uint8_t)((off + i) * 31 + sdPasses)) { f.close(); return false; }
    server.handleClient();
  }
  f.close();
  uint32_t t2 = millis();
  lastWriteKBps = (TOTAL / 1024) * 1000 / max<uint32_t>(1, t1 - t0);
  lastReadKBps  = (TOTAL / 1024) * 1000 / max<uint32_t>(1, t2 - t1);
  return true;
}

void setup() {
  Serial.begin(115200);
  delay(1500);
  Serial.println("\nBench check 2: Ethernet (polled W5500) and microSD (SD host, 1-bit)");

  Network.onEvent(onEvent);
  SPI.begin(SPI_SCK, SPI_MISO, SPI_MOSI);
  if (!ETH.begin(ETH_PHY_W5500, 1, ETH_CS, ETH_IRQ, ETH_RST, SPI))
    Serial.println("FAIL: ETH.begin");

  if (!SD_MMC.setPins(SD_CLK, SD_CMD, SD_D0)) Serial.println("FAIL: SD_MMC.setPins");
  if (!SD_MMC.begin("/sdcard", true)) {          // true = 1-bit mode
    Serial.println("FAIL: SD_MMC.begin (card, wiring or pull-ups)");
  } else {
    Serial.printf("SD card %llu MB\n", SD_MMC.cardSize() / (1024 * 1024));
  }

  server.on("/", handleRoot);
  server.begin();
}

void loop() {
  server.handleClient();
  static uint32_t last = 0;
  if (millis() - last >= 2000) {
    last = millis();
    if (SD_MMC.cardType() != CARD_NONE) {
      if (sdPass()) sdPasses++; else sdErrors++;
    }
    Serial.printf("eth %s  sd passes %lu errors %lu  write %lu KB/s read %lu KB/s  hits %lu\n",
                  ethUp ? "up" : "down", sdPasses, sdErrors, lastWriteKBps, lastReadKBps, pageHits);
  }
}
