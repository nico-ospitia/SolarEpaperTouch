# Schematic

| File | Use |
|---|---|
| [`SolarEpaperTouch_schematic_revA.pdf`](SolarEpaperTouch_schematic_revA.pdf) | One A3 sheet, for printing |
| [`SolarEpaperTouch_schematic_revA.svg`](SolarEpaperTouch_schematic_revA.svg) | Vector version |

The sheet has five blocks (power, microcontroller, display, touch buttons, microphone), a pin table for the ESP32-C3 and the build notes. Signals between blocks are joined by net labels: two labels with the same name are the same wire. The same connections are listed as tables in [docs/wiring.md](../../docs/wiring.md).

## Revision A (2026-11-25)

First issue. Decisions worth knowing:

- **Microphone pins:** SD on IO21, SCK on IO8, WS on IO2. The microphone's SD output floats or is pulled to GND while idle, so it is kept off IO8, which is a boot (strapping) pin.
- **R1 (10 kΩ) from IO2 to 3.3 V:** IO2 has to be high at boot and has no internal pull-up by default.
- **Charger wiring:** the CN3065 output goes to OUT+ / OUT− of the TP4056 module, not to its IN+ / IN− input.
- **No external diode on the solar panel:** the CN3065 already blocks reverse current in the dark and the module has SS14 diodes.

## Regenerating

The drawing is produced by a script, so edits go in [`tools/schematic`](../../tools/schematic) and the files here are regenerated from it.
