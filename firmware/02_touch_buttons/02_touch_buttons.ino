// 02 - E-paper + three TTP223 touch buttons
// WeAct Studio 4.2" e-paper (400x300, black/white) + 3x TTP223 + ESP32-C3 SuperMini
//
// - The counter goes up by itself every 3 seconds.
// - B1 (GPIO0): subtract 1
// - B2 (GPIO1): pause / resume
// - B3 (GPIO3): reset to 0 (and do a full refresh to clean the screen)
// The screen shows the state and the last button pressed, so you can check each pad.
//
// Libraries: GxEPD2 (ZinggJM) + Adafruit GFX Library.
// Board: "ESP32C3 Dev Module", Tools > "USB CDC On Boot: Enabled".
// Wiring: see docs/wiring.md.

#include <SPI.h>
#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold9pt7b.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <Fonts/FreeMonoBold24pt7b.h>

// ---- Display pins ----
#define EPD_SCK   6   // SCL
#define EPD_MOSI  7   // SDA
#define EPD_CS    10  // CS
#define EPD_DC    4   // D/C
#define EPD_RST   5   // RES
#define EPD_BUSY  20  // BUSY

// ---- TTP223 pins (module I/O pin) ----
#define BTN1 0
#define BTN2 1
#define BTN3 3

// TTP223 modules ship active-high (jumper A open): HIGH while touched.
// If a module has jumper A bridged (LOW while touched), set this to false.
const bool TOUCH_ACTIVE_HIGH = true;

// ---- Settings ----
const uint32_t COUNT_INTERVAL_MS  = 3000;  // how often the counter goes up
const int      FULL_REFRESH_EVERY = 10;    // full refresh every N updates (clears ghosting)
const uint32_t DEBOUNCE_MS        = 250;   // ignore repeated touches closer than this

GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT> display(
    GxEPD2_420_GDEY042T81(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

// ---- State ----
uint32_t counter          = 0;
bool     paused           = false;
int      lastButton       = 0;  // 0 = none yet
uint32_t lastTick         = 0;
int      updatesSinceFull = 0;

// ---- Buttons via interrupts: a touch is caught even while the screen is refreshing ----
portMUX_TYPE btnMux = portMUX_INITIALIZER_UNLOCKED;
volatile bool     btnFlag[3]   = {false, false, false};
volatile uint32_t btnLastMs[3] = {0, 0, 0};

void IRAM_ATTR markButton(int i) {
  uint32_t now = millis();
  portENTER_CRITICAL_ISR(&btnMux);
  if (now - btnLastMs[i] > DEBOUNCE_MS) {
    btnLastMs[i] = now;
    btnFlag[i] = true;
  }
  portEXIT_CRITICAL_ISR(&btnMux);
}
void IRAM_ATTR onBtn1() { markButton(0); }
void IRAM_ATTR onBtn2() { markButton(1); }
void IRAM_ATTR onBtn3() { markButton(2); }

bool takeFlag(int i) {
  portENTER_CRITICAL(&btnMux);
  bool f = btnFlag[i];
  btnFlag[i] = false;
  portEXIT_CRITICAL(&btnMux);
  return f;
}

// ---- Drawing ----
void printCentered(const char* text, int16_t boxX, int16_t boxY, int16_t boxW, int16_t boxH) {
  int16_t tbx, tby;
  uint16_t tbw, tbh;
  display.getTextBounds(text, 0, 0, &tbx, &tby, &tbw, &tbh);
  display.setCursor(boxX + (boxW - tbw) / 2 - tbx, boxY + (boxH - tbh) / 2 - tby);
  display.print(text);
}

void drawContent() {
  display.fillScreen(GxEPD_WHITE);
  display.setTextColor(GxEPD_BLACK);

  // Frame
  display.drawRect(0, 0, display.width(), display.height(), GxEPD_BLACK);
  display.drawRect(2, 2, display.width() - 4, display.height() - 4, GxEPD_BLACK);

  // Title
  display.setFont(&FreeMonoBold12pt7b);
  display.setCursor(14, 34);
  display.print("e-Paper + touch test");
  display.drawFastHLine(10, 48, display.width() - 20, GxEPD_BLACK);

  // Counter
  display.setCursor(14, 80);
  display.print("Counter:");

  char buf[12];
  snprintf(buf, sizeof(buf), "%lu", (unsigned long)counter);
  display.setFont(&FreeMonoBold24pt7b);
  printCentered(buf, 10, 90, display.width() - 20, 90);

  display.setFont(&FreeMonoBold12pt7b);
  display.drawFastHLine(10, 190, display.width() - 20, GxEPD_BLACK);

  // State
  display.setCursor(14, 220);
  display.print(paused ? "State: Paused" : "State: Running");

  display.setCursor(14, 250);
  display.print("Last button: ");
  if (lastButton == 0) {
    display.print("-");
  } else {
    display.print("B");
    display.print(lastButton);
  }

  // Legend
  display.setFont(&FreeMonoBold9pt7b);
  display.setCursor(14, 282);
  display.print("B1: -1   B2: pause   B3: reset");
}

// Full refresh: flickers and takes longer, but leaves the screen clean.
// Partial refresh: fast, but slowly builds up ghosting.
void updateScreen(bool forceFull) {
  bool full = forceFull || (updatesSinceFull >= FULL_REFRESH_EVERY);

  if (full) {
    display.setFullWindow();
    updatesSinceFull = 0;
  } else {
    display.setPartialWindow(0, 0, display.width(), display.height());
    updatesSinceFull++;
  }

  uint32_t t0 = millis();
  display.firstPage();
  do {
    drawContent();
  } while (display.nextPage());

  Serial.printf("%s refresh: %lu ms | counter=%lu | %s | last button=%d\n",
                full ? "FULL" : "PARTIAL",
                (unsigned long)(millis() - t0),
                (unsigned long)counter,
                paused ? "paused" : "running",
                lastButton);
}

void setup() {
  Serial.begin(115200);
  delay(1500);  // give USB time to enumerate
  Serial.println("Starting e-paper + touch test...");

  // Buttons. Don't touch the pads while powering up: the TTP223 calibrates at power-on.
  uint8_t mode = TOUCH_ACTIVE_HIGH ? INPUT_PULLDOWN : INPUT_PULLUP;
  int edge     = TOUCH_ACTIVE_HIGH ? RISING : FALLING;
  pinMode(BTN1, mode);
  pinMode(BTN2, mode);
  pinMode(BTN3, mode);
  attachInterrupt(digitalPinToInterrupt(BTN1), onBtn1, edge);
  attachInterrupt(digitalPinToInterrupt(BTN2), onBtn2, edge);
  attachInterrupt(digitalPinToInterrupt(BTN3), onBtn3, edge);

  // Display
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  display.init(115200, true, 2, false);  // 115200 prints the library's refresh timings to the Serial Monitor
  display.setRotation(0);

  updateScreen(true);
  lastTick = millis();
}

void loop() {
  bool changed   = false;
  bool forceFull = false;

  if (takeFlag(0)) {  // B1: subtract
    if (counter > 0) counter--;
    lastButton = 1;
    changed = true;
  }
  if (takeFlag(1)) {  // B2: pause / resume
    paused = !paused;
    lastButton = 2;
    lastTick = millis();  // on resume, wait a full interval
    changed = true;
  }
  if (takeFlag(2)) {  // B3: reset
    counter = 0;
    lastButton = 3;
    lastTick = millis();
    changed = true;
    forceFull = true;  // good moment to clean the screen
  }

  if (!paused && (millis() - lastTick >= COUNT_INTERVAL_MS)) {
    lastTick = millis();
    counter++;
    changed = true;
  }

  if (changed) {
    updateScreen(forceFull);
  }
}

// If the screen does not respond, try another driver class in the "GxEPD2_BW<...>" line
// (both places): GxEPD2_420_GDEY042T81 (SSD1683, most WeAct modules), GxEPD2_420 (UC8176)
// or GxEPD2_420_M01.
