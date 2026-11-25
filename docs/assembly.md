# Assembly and bring-up

Build and test one block at a time, so a problem always points to the last thing you added. Connections for every step are in [wiring.md](wiring.md).

## 1. Display (USB power only)

1. Wire U4 to U1: VCC, GND, SDA, SCL, CS, D/C, RES, BUSY.
2. Power U1 from USB. No battery yet.
3. Upload [`01_epaper_counter`](../firmware/01_epaper_counter). The counter should go up every 3 seconds.

If the screen stays blank, see the troubleshooting table in [firmware/README.md](../firmware/README.md#troubleshooting).

## 2. Touch buttons

1. Add U6, U7 and U8: VCC to 3V3, GND to GND, I/O to IO0, IO1 and IO3.
2. Leave the A and B jumpers on each module open.
3. Upload [`02_touch_buttons`](../firmware/02_touch_buttons). Touch each pad and check that the screen shows the right "Last button".
4. Upload [`03_three_counters`](../firmware/03_three_counters) to check that every pad counts on its own.

Keep your fingers off the pads while the board powers up: the TTP223 calibrates at power-on.

## 3. Power chain (without the ESP32)

1. Wire PV1 → U2 SOLAR ±, U2 BATT IN ± → U3 OUT ±, BT1 → U3 B ±.
2. Check battery polarity before connecting BT1.
3. With a multimeter:
   - U3 OUT+ to OUT− should read the battery voltage (3.0–4.2 V).
   - With light on the panel, U2's charge LED should turn on.

## 4. Power the ESP32 from the battery

1. Wire SW1 between U3 OUT+ and U1 5V, and U3 OUT− to U1 GND.
2. Unplug USB, turn SW1 on: the board should boot and the display should update.
3. From now on, **turn SW1 off before plugging in USB.**

## 5. Microphone

1. Wire U5: VDD to 3V3, GND and L/R to GND, SCK to IO8, WS to IO2, SD to IO21.
2. Add R1 (10 kΩ) from IO2 to 3V3.
3. Test sketch: to be added.

## 6. Low-power preparation

1. Remove the red power LED from U1 (it stays on all the time and dominates deep-sleep current).
2. Measure the sleep current as described in [power-budget.md](power-budget.md#how-to-measure).

## 7. Enclosure

To be added: see [hardware/enclosure](../hardware/enclosure).
