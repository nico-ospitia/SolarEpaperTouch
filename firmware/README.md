# Firmware

Arduino sketches for the ESP32-C3 SuperMini. They are bring-up tests: run them in order, adding one piece of hardware at a time.

| Sketch | What it shows | Hardware needed |
|---|---|---|
| [`01_epaper_counter`](01_epaper_counter) | A counter that goes up every 3 s. Redraws only the number (partial refresh) and does a full refresh every 20 counts. | U1 + U4 (display) |
| [`02_touch_buttons`](02_touch_buttons) | Same counter, controlled by the touch pads: B1 subtracts 1, B2 pauses, B3 resets. Shows the last button pressed. | + U6–U8 (touch) |
| [`03_three_counters`](03_three_counters) | Three boxes, one per pad. Each touch adds 1 to its box and only that box is redrawn. | + U6–U8 (touch) |

`01_epaper_counter` has been run on the prototype. All three sketches are compiled by the [firmware workflow](../.github/workflows/compile-firmware.yml) on every push.

## Setup (Arduino IDE 2.x)

1. **Board package:** in Boards Manager install **esp32** by Espressif Systems.
2. **Library:** in Library Manager install **GxEPD2** by Jean-Marc Zingg. Accept the extra libraries it asks for (Adafruit GFX Library, Adafruit BusIO).
3. **Board:** Tools > Board > **ESP32C3 Dev Module**.
4. **USB serial:** Tools > **USB CDC On Boot: Enabled**. Without it, `Serial` goes to GPIO20/21 instead of the USB-C port and the Serial Monitor stays empty.
5. **Upload.** If the port doesn't show up, hold **BOOT**, plug in the USB cable, then release BOOT.

> Turn the power switch (SW1) **off** before plugging USB into the ESP32. On most SuperMini boards the 5V pin is tied to USB VBUS, so USB would push 5 V into the battery node.

## Pins used in the code

| Signal | GPIO | Notes |
|---|---|---|
| EPD_SCL (SPI SCK) | 6 | |
| EPD_SDA (SPI MOSI) | 7 | |
| EPD_CS | 10 | |
| EPD_DC | 4 | |
| EPD_RES | 5 | |
| EPD_BUSY | 20 | Input |
| TOUCH1 / TOUCH2 / TOUCH3 | 0 / 1 / 3 | TTP223 outputs; these pins can wake the ESP32-C3 from deep sleep |
| MIC_SCK / MIC_WS / MIC_SD | 8 / 2 / 21 | Reserved for the INMP441 (no sketch yet) |

Full wiring, including power: [docs/wiring.md](../docs/wiring.md).

## Display refresh

The GxEPD2 driver for this panel (`GxEPD2_420_GDEY042T81`, SSD1683) lists about **0.4 s** for a partial refresh and **1.2 s** for a full refresh, plus power-on and power-off time. The Serial Monitor prints the measured time of every refresh.

- **Partial refresh** is fast but leaves a faint trace of the previous image ("ghosting") that builds up.
- **Full refresh** flickers black/white but cleans the screen.

The sketches mix both. If ghosting is still visible, lower `FULL_REFRESH_EVERY`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| Screen stays blank or never refreshes | Check BUSY on GPIO20. Then try another driver class in the `GxEPD2_BW<...>` line: `GxEPD2_420` (UC8176 panels) or `GxEPD2_420_M01`. |
| Nothing in the Serial Monitor | Enable **USB CDC On Boot**. Use a data USB cable, not a charge-only one. |
| A touch pad acts "always pressed" or inverted | That module has jumper A bridged (active-low). Set `TOUCH_ACTIVE_HIGH = false`. |
| Touch pads react badly after power-up | Don't touch the pads while powering up: the TTP223 calibrates at power-on. |

## Planned

- Microphone test: read the INMP441 over I2S and show the sound level.
- Deep sleep with wake-up from the touch pads.
- Application firmware: portfolio tracker and song recognition with synced lyrics (see the [README](../README.md#roadmap)).
