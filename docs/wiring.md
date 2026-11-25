# Wiring

Every part is a ready-made module, joined point-to-point on perfboard. Pin names follow the silkscreen on each board. The drawing is in [hardware/schematic](../hardware/schematic).

## Power

| From | To | Notes |
|---|---|---|
| PV1 + | U2 SOLAR + | No external diode needed |
| PV1 − | U2 SOLAR − | |
| U2 BATT IN + | U3 OUT+ | Net VBAT |
| U2 BATT IN − | U3 OUT− | Net GND |
| BT1 + | U3 B+ | |
| BT1 − | U3 B− | **B− is not ground.** Nothing else connects here. |
| U3 OUT+ | SW1, then U1 5V | Net VSYS after the switch |
| U3 OUT− | U1 GND and every module's GND | System ground |
| U1 3V3 | U4 VCC, U5 VDD, U6–U8 VCC, R1 | Net +3V3, from the ESP32 board's regulator |

Left unconnected: U2 SYS OUT ±, U3 IN+ / IN− and U3's USB-C port.

The solar charger (U2) charges the battery *through* the protection board (U3), so the cell is protected while charging too. The switch only cuts the load: the battery keeps charging with SW1 off.

## ESP32-C3 SuperMini (U1)

Seen from the top with the USB-C connector up, the left header is IO5, IO6, IO7, IO8, IO9, IO10, IO20, IO21 and the right header is 5V, GND, 3V3, IO4, IO3, IO2, IO1, IO0 (top to bottom).

| Pin | Net | Goes to | Notes |
|---|---|---|---|
| IO0 | TOUCH1 | U6 I/O | Can wake from deep sleep |
| IO1 | TOUCH2 | U7 I/O | Can wake from deep sleep |
| IO2 | MIC_WS | U5 WS, R1 | Strapping pin: must be high at boot |
| IO3 | TOUCH3 | U8 I/O | Can wake from deep sleep |
| IO4 | EPD_DC | U4 D/C | |
| IO5 | EPD_RES | U4 RES | |
| IO6 | EPD_SCL | U4 SCL | SPI clock |
| IO7 | EPD_SDA | U4 SDA | SPI data (MOSI) |
| IO8 | MIC_SCK | U5 SCK | Strapping pin; on-board LED |
| IO9 | — | — | BOOT button: leave unconnected |
| IO10 | EPD_CS | U4 CS | |
| IO20 | EPD_BUSY | U4 BUSY | Input |
| IO21 | MIC_SD | U5 SD | Input |
| 5V | VSYS | SW1 | Battery voltage, 3.0–4.2 V |
| 3V3 | +3V3 | U4–U8, R1 | Regulator output |
| GND | GND | everything | |

## Per module

**E-paper (U4):** VCC → 3V3, GND → GND, SDA → IO7, SCL → IO6, CS → IO10, D/C → IO4, RES → IO5, BUSY → IO20. SDA and SCL are SPI lines here, not I²C.

**Touch buttons (U6, U7, U8):** VCC → 3V3, GND → GND, I/O → IO0, IO1 and IO3. Leave the A and B jumpers open (active-high, momentary).

**Microphone (U5):** VDD → 3V3, GND → GND, L/R → GND (left channel), SCK → IO8, WS → IO2, SD → IO21. R1 (10 kΩ) goes from IO2 to 3V3.

## Rules

- **Turn SW1 off before plugging USB into the ESP32.** On most SuperMini boards the 5V pin is tied to USB VBUS, so with SW1 on, USB would push 5 V into the battery node.
- **Never use U3's USB-C port** while the solar charger is connected.
- **Boot pins:** IO2 and IO8 only carry signals that the ESP32 drives (WS and SCK). Don't connect a module *output* to them, and leave IO9 alone.
- **Touch calibration:** the TTP223 calibrates when it powers up. Keep fingers off the pads while switching on.

## Perfboard tips

- Solder female headers and plug the modules in, so a dead module can be swapped.
- Keep the power path short and use thicker wire for it (battery → U3 → SW1 → 5V): Wi-Fi bursts draw a few hundred mA.
- Keep copper, the battery and wires away from the end of the ESP32-C3 board with the antenna (the end opposite the USB-C connector).
- Check battery polarity twice before connecting BT1. Reversing it can destroy the protection board.
