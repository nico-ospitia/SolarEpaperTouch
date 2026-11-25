# Tools

Scripts that generate the drawings in this repository. Edit the scripts, then regenerate; don't edit the output files by hand.

## Requirements

```bash
pip install pillow playwright
playwright install chromium
```

The scripts measure text with Liberation Sans/Mono (Linux) or Arial/Courier New (macOS, Windows).

## Schematic

```bash
cd tools/schematic
python3 generate_schematic.py ../../hardware/schematic/SolarEpaperTouch_schematic_revA.svg
python3 render_schematic.py ../../hardware/schematic/SolarEpaperTouch_schematic_revA.svg \
    ../../hardware/schematic/SolarEpaperTouch_schematic_revA.pdf ../../docs/images/schematic.png 1.3334
```

`generate_schematic.py` prints any labels that overlap. Bump the revision letter in the title block and the file names when the circuit changes.

## UI concepts

```bash
cd tools/ui_mockups
python3 make_ui_mockups.py ../../docs/images
```

Writes the native 400 × 300 screens to `docs/images/ui/` and the combined `docs/images/ui-concepts.png`.
