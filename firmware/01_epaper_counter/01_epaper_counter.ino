// 01 - E-paper bring-up test
// WeAct Studio 4.2" e-paper (400x300, black/white, SSD1683) + ESP32-C3 SuperMini
//
// Shows a counter that goes up every 3 seconds. Only the counter area is redrawn
// (fast partial refresh); every FULL_REFRESH_EVERY counts the whole screen gets a
// full refresh to clear ghosting.
//
// Libraries: GxEPD2 (ZinggJM) + Adafruit GFX Library.
// Board: "ESP32C3 Dev Module", Tools > "USB CDC On Boot: Enabled".
// Wiring: see docs/wiring.md (only the display is needed for this test).

#include <SPI.h>
#include <GxEPD2_BW.h>
#include <Fonts/FreeMonoBold12pt7b.h>
#include <Fonts/FreeMonoBold24pt7b.h>

// ---- Display pins (same as the final wiring) ----
#define EPD_SCK   6   // display SCL
#define EPD_MOSI  7   // display SDA
#define EPD_CS    10  // display CS
#define EPD_DC    4   // display D/C
#define EPD_RST   5   // display RES
#define EPD_BUSY  20  // display BUSY

// SSD1683 controller, 400x300 (WeAct 4.2"). If the screen stays blank, see the note at the end.
GxEPD2_BW<GxEPD2_420_GDEY042T81, GxEPD2_420_GDEY042T81::HEIGHT> display(
    GxEPD2_420_GDEY042T81(EPD_CS, EPD_DC, EPD_RST, EPD_BUSY));

// Area redrawn on each count (x and width are multiples of 8)
const int CX = 16;
const int CY = 110;
const int CW = 368;
const int CH = 100;

const int FULL_REFRESH_EVERY = 20;  // one full refresh every 20 counts, to clear ghosting

uint32_t counter = 0;

void drawCounterText(uint32_t n) {
  char buf[12];
  snprintf(buf, sizeof(buf), "%lu", (unsigned long)n);

  display.setFont(&FreeMonoBold24pt7b);
  display.setTextColor(GxEPD_BLACK);

  int16_t tbx, tby;
  uint16_t tbw, tbh;
  display.getTextBounds(buf, 0, 0, &tbx, &tby, &tbw, &tbh);
  int16_t x = CX + (CW - tbw) / 2 - tbx;
  int16_t y = CY + (CH - tbh) / 2 - tby;

  display.setCursor(x, y);
  display.print(buf);
}

// Draws the whole screen (full refresh, flickers)
void drawAll(uint32_t n) {
  display.setFullWindow();
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);

    // Frame and title
    display.drawRect(0, 0, display.width(), display.height(), GxEPD_BLACK);
    display.drawRect(2, 2, display.width() - 4, display.height() - 4, GxEPD_BLACK);

    display.setFont(&FreeMonoBold12pt7b);
    display.setTextColor(GxEPD_BLACK);
    display.setCursor(20, 40);
    display.print("Test e-Paper 4.2\"");
    display.setCursor(20, 80);
    display.print("Counter:");

    display.drawFastHLine(10, 240, display.width() - 20, GxEPD_BLACK);
    display.setCursor(20, 275);
    display.print("Every 3 seconds");

    drawCounterText(n);
  } while (display.nextPage());
}

// Redraws only the counter area (partial refresh, fast)
void drawCounterOnly(uint32_t n) {
  display.setPartialWindow(CX, CY, CW, CH);
  display.firstPage();
  do {
    display.fillScreen(GxEPD_WHITE);
    drawCounterText(n);
  } while (display.nextPage());
}

void setup() {
  Serial.begin(115200);
  delay(1500);  // give USB time to enumerate
  Serial.println("Starting e-paper test...");

  SPI.begin(EPD_SCK, -1, EPD_MOSI, EPD_CS);  // SCK, MISO (unused), MOSI, SS
  display.init(115200, true, 2, false);      // debug baud rate, initial reset, reset pulse (ms), no pull-down reset

  display.setRotation(0);  // 400 wide x 300 tall

  drawAll(counter);
  Serial.println("First screen drawn");
}

void loop() {
  delay(3000);
  counter++;

  if (counter % FULL_REFRESH_EVERY == 0) {
    drawAll(counter);
  } else {
    drawCounterOnly(counter);
  }

  Serial.print("Counter: ");
  Serial.println(counter);
}

// If the screen stays blank or never refreshes, try another driver class in the
// "GxEPD2_BW<...>" line above (replace it in both places):
//   GxEPD2_420_GDEY042T81 -> WeAct 4.2" with SSD1683 (most modules)
//   GxEPD2_420            -> older 4.2" panels with UC8176 (GDEW042T2)
//   GxEPD2_420_M01        -> GDEW042M01 panels
