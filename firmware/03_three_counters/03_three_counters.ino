// 03 - Three counters
// WeAct Studio 4.2" e-paper (400x300, black/white) + 3x TTP223 + ESP32-C3 SuperMini
//
// - Three boxes, each with a number.
// - Each touch adds 1 to its own box:
//     B1 (GPIO0) -> box 1,  B2 (GPIO1) -> box 2,  B3 (GPIO3) -> box 3
// - Only the box that changed is redrawn (partial refresh), so the others don't build up ghosting.
// - Every FULL_REFRESH_EVERY partial refreshes the whole screen gets a full refresh.
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
const uint8_t BTN_PINS[3] = {0, 1, 3};

// TTP223 modules ship active-high (jumper A open): HIGH while touched.
// If a module has jumper A bridged (LOW while touched), set this to false.
const bool TOUCH_ACTIVE_HIGH = true;

// ---- Settings ----
const int      FULL_REFRESH_EVERY = 15;   // full refresh every N partial refreshes
const uint32_t DEBOUNCE_MS        = 150;  // ignore bounces of the same button closer than this

GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT> display(
    GxEPD2_420_GDEY042T81(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

// ---- Box geometry (x and width are multiples of 8 for partial refresh) ----
const int16_t BOX_Y = 72;
const int16_t BOX_W = 120;
const int16_t BOX_H = 150;
const int16_t BOX_X[3] = {16, 144, 272};

// ---- State ----
uint32_t counters[3] = {0, 0, 0};
int partialsSinceFull = 0;

// ---- Buttons via interrupts ----
// Each touch adds 1 to "pending", so no touch is lost while the screen is refreshing.
portMUX_TYPE btnMux = portMUX_INITIALIZER_UNLOCKED;
volatile uint16_t pending[3]   = {0, 0, 0};
volatile uint32_t lastIsrMs[3] = {0, 0, 0};

void IRAM_ATTR registerTap(int i) {
  uint32_t now = millis();
  portENTER_CRITICAL_ISR(&btnMux);
  if (now - lastIsrMs[i] > DEBOUNCE_MS) {
    lastIsrMs[i] = now;
    pending[i]++;
  }
  portEXIT_CRITICAL_ISR(&btnMux);
}
void IRAM_ATTR onBtn1() { registerTap(0); }
void IRAM_ATTR onBtn2() { registerTap(1); }
void IRAM_ATTR onBtn3() { registerTap(2); }

uint16_t takePending(int i) {
  portENTER_CRITICAL(&btnMux);
  uint16_t n = pending[i];
  pending[i] = 0;
  portEXIT_CRITICAL(&btnMux);
  return n;
}

// ---- Drawing ----
void printCentered(const char* text, int16_t boxX, int16_t boxY, int16_t boxW, int16_t boxH) {
  int16_t tbx, tby;
  uint16_t tbw, tbh;
  display.getTextBounds(text, 0, 0, &tbx, &tby, &tbw, &tbh);
  display.setCursor(boxX + (boxW - tbw) / 2 - tbx, boxY + (boxH - tbh) / 2 - tby);
  display.print(text);
}

// Draws one whole box: frame, label and number
void drawBox(int i) {
  int16_t x = BOX_X[i];

  display.fillRect(x, BOX_Y, BOX_W, BOX_H, GxEPD_WHITE);
  display.drawRect(x, BOX_Y, BOX_W, BOX_H, GxEPD_BLACK);
  display.drawRect(x + 1, BOX_Y + 1, BOX_W - 2, BOX_H - 2, GxEPD_BLACK);

  // "B1", "B2", "B3" label at the top, with a line under it
  char label[4];
  snprintf(label, sizeof(label), "B%d", i + 1);
  display.setFont(&FreeMonoBold12pt7b);
  printCentered(label, x, BOX_Y + 4, BOX_W, 30);
  display.drawFastHLine(x + 8, BOX_Y + 38, BOX_W - 16, GxEPD_BLACK);

  // Number: large font up to 3 digits, smaller after that
  char num[12];
  snprintf(num, sizeof(num), "%lu", (unsigned long)counters[i]);
  display.setFont(strlen(num) <= 3 ? &FreeMonoBold24pt7b : &FreeMonoBold12pt7b);
  printCentered(num, x, BOX_Y + 40, BOX_W, BOX_H - 44);
}

void drawWholeScreen() {
  display.fillScreen(GxEPD_WHITE);
  display.setTextColor(GxEPD_BLACK);

  // Outer frame
  display.drawRect(0, 0, display.width(), display.height(), GxEPD_BLACK);
  display.drawRect(2, 2, display.width() - 4, display.height() - 4, GxEPD_BLACK);

  // Title
  display.setFont(&FreeMonoBold12pt7b);
  printCentered("Three counters", 0, 12, display.width(), 30);
  display.drawFastHLine(10, 52, display.width() - 20, GxEPD_BLACK);

  for (int i = 0; i < 3; i++) drawBox(i);

  // Legend
  display.setFont(&FreeMonoBold9pt7b);
  printCentered("Tap a button to add 1", 0, 240, display.width(), 40);
}

// Full refresh of the whole screen (flickers, leaves everything clean)
void fullRefresh() {
  uint32_t t0 = millis();
  display.setFullWindow();
  display.firstPage();
  do {
    drawWholeScreen();
  } while (display.nextPage());
  partialsSinceFull = 0;
  Serial.printf("FULL refresh: %lu ms\n", (unsigned long)(millis() - t0));
}

// Partial refresh of a single box (fast)
void refreshBox(int i) {
  uint32_t t0 = millis();
  display.setPartialWindow(BOX_X[i], BOX_Y, BOX_W, BOX_H);
  display.firstPage();
  do {
    display.setTextColor(GxEPD_BLACK);
    drawBox(i);
  } while (display.nextPage());
  partialsSinceFull++;
  Serial.printf("Box %d -> %lu (partial: %lu ms)\n", i + 1,
                (unsigned long)counters[i], (unsigned long)(millis() - t0));
}

void setup() {
  Serial.begin(115200);
  delay(1500);  // give USB time to enumerate
  Serial.println("Starting three counters...");

  // Buttons. Don't touch the pads while powering up: the TTP223 calibrates at power-on.
  uint8_t mode = TOUCH_ACTIVE_HIGH ? INPUT_PULLDOWN : INPUT_PULLUP;
  int edge     = TOUCH_ACTIVE_HIGH ? RISING : FALLING;
  for (int i = 0; i < 3; i++) pinMode(BTN_PINS[i], mode);
  attachInterrupt(digitalPinToInterrupt(BTN_PINS[0]), onBtn1, edge);
  attachInterrupt(digitalPinToInterrupt(BTN_PINS[1]), onBtn2, edge);
  attachInterrupt(digitalPinToInterrupt(BTN_PINS[2]), onBtn3, edge);

  // Display
  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);
  display.init(115200, true, 2, false);  // 115200 prints the library's timings to the Serial Monitor
  display.setRotation(0);

  fullRefresh();
}

void loop() {
  bool changed[3] = {false, false, false};

  for (int i = 0; i < 3; i++) {
    uint16_t taps = takePending(i);
    if (taps > 0) {
      counters[i] += taps;  // several touches during one refresh all count
      changed[i] = true;
    }
  }

  if (!changed[0] && !changed[1] && !changed[2]) return;

  if (partialsSinceFull >= FULL_REFRESH_EVERY) {
    fullRefresh();  // draws all three boxes, already updated
  } else {
    for (int i = 0; i < 3; i++) {
      if (changed[i]) refreshBox(i);
    }
  }
}

// If the screen does not respond, try another driver class in the "GxEPD2_BW<...>" line
// (both places): GxEPD2_420_GDEY042T81 (SSD1683, most WeAct modules), GxEPD2_420 (UC8176)
// or GxEPD2_420_M01.
