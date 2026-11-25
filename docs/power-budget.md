# Power budget

**These are estimates**, built from datasheets and commonly reported figures. Replace them with measurements as the prototype comes together (see [How to measure](#how-to-measure)).

## What draws current

| Part | State | Current | Source |
|---|---|---|---|
| ESP32-C3 SuperMini | Deep sleep, power LED removed | about 43 µA | Reported for SuperMini boards; to measure |
| ESP32-C3 SuperMini | Awake with Wi-Fi (connect + one HTTPS request) | assumed 100 mA average for 5 s, with peaks of a few hundred mA | Assumption; to measure |
| INMP441 microphone | Running | 1.4 mA | Datasheet |
| INMP441 microphone | Clock stopped | **0.8 mA** | Datasheet (standby mode) |
| TTP223 × 3 | Idle | a few µA each | Datasheet order of magnitude |
| E-paper | Showing an image | about 0 | E-paper keeps its image without power |
| E-paper | Refreshing | short bursts; partial refresh ≈ 0.4 s, full ≈ 1.2 s | GxEPD2 driver timings |

The microphone is the surprise: even with its clock stopped it draws about 20 times more than the ESP32-C3 in deep sleep. With every GPIO already in use, it can't be switched off yet (see [Open questions](#open-questions)).

## Daily use: portfolio mode

Example: the device wakes every 10 minutes (144 times a day), connects to Wi-Fi, fetches prices, redraws and goes back to sleep.

| Item | Calculation | Per day |
|---|---|---|
| Wake-ups | 144 × 5 s × 100 mA | 20 mAh |
| Sleep floor (ESP32-C3 + touch pads) | about 50 µA × 24 h | 1.2 mAh |
| Microphone standby, if always powered | 0.8 mA × 24 h | 19 mAh |

| Scenario | Total per day | 500 mAh cell, no sun | 1000 mAh cell, no sun |
|---|---|---|---|
| Microphone unpowered | ≈ 21 mAh | ≈ 19 days | ≈ 38 days |
| Microphone always powered | ≈ 40 mAh | ≈ 10 days | ≈ 20 days |

Days without sun assume 80 % of the rated capacity is usable.

## Solar input

The panel has to put back what the device uses. The break-even condition is:

> average charging current × hours of useful light per day ≥ daily consumption

For example, a panel that charges at 10 mA for 3 hours a day (30 mAh) covers portfolio mode with the microphone unpowered. Indoors, a small 5 V panel delivers only a fraction of its rated current, so placement near a window matters more than the panel's rating.

## How to measure

1. **Sleep current:** disconnect USB, put a multimeter (µA range) in series with SW1, let the device go to deep sleep and read the current.
2. **Wake-up charge:** use a USB power meter or a current-sense board (such as an INA219) and log a full wake-up; multiply the average current by its duration.
3. **Solar charging:** put the meter (mA range) between U2 BATT IN + and U3 OUT+, leave the device where it will live and log the charging current over a day.

## Open questions

- **Switching off the microphone** needs a free GPIO. Options: drop the e-paper BUSY line (GxEPD2 can use fixed delays instead), give up one touch pad, or add a load switch.
- **Battery level:** there is no GPIO left for a voltage divider to read the battery voltage. The same trade-off applies.
