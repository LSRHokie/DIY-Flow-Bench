# Bench checks before PCB rev A

Short tests that settle the last circuit questions while the schematic is drawn. PCB rev A is the prototype; these replace the full breadboard build. Steps and pass criteria are in the Bench Checks doc.

| Sketch | Board | Check |
| --- | --- | --- |
| `../digimatic-interface` | ATtiny1616 (megaTinyCore, UPDI) | 1. Digimatic indicator signal levels and decoding |
| `eth_sd_check` | ESP32-S3-DevKitC-1-N32R8V | 2. WIZ850io polled on SPI and microSD on the SD host bus, at the same time |
| `stepper_check` | ESP32-S3-DevKitC-1-N32R8V | 3. iCL42-08 enable level and alarm input |

ESP32-S3 settings: ESP32S3 Dev Module, Flash Mode OPI 80 MHz, Flash Size 32 MB, PSRAM OPI, USB CDC On Boot enabled. Both ESP32 sketches compile on Arduino core 3.3.12.

`eth_sd_check` uses `ETH.begin(ETH_PHY_W5500, 1, CS, -1, RST, SPI)`: an interrupt pin of -1 makes the core poll the W5500 (every 10 ms by default, set with `ETH.setPollPeriod()`).
