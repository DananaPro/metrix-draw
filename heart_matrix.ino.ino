
#include "Adafruit_HT1632.h"

#define HT_DATA 2
#define HT_WR   3

#define HT_CS_1 4
#define HT_CS_2 5
#define HT_CS_3 6

#define FRAME_HEADER_1 0xAA
#define FRAME_HEADER_2 0x55

#define DISPLAY_WIDTH  32
#define DISPLAY_HEIGHT 24

#define BYTES_PER_ROW 4
#define FRAME_SIZE 96

Adafruit_HT1632LEDMatrix matrix(
    HT_DATA,
    HT_WR,
    HT_CS_1,
    HT_CS_2,
    HT_CS_3
);

byte frame[FRAME_SIZE];


// ================================================
// SETUP
// ================================================

void setup() {

    Serial.begin(115200);

    if (!matrix.begin(ADA_HT1632_COMMON_8NMOS)) {
        while (true) {}
    }

    matrix.setBrightness(15);
    matrix.setTextWrap(false);

    matrix.clearScreen();
    matrix.writeScreen();
}


// ================================================
// RECEIVE FRAME
// ================================================

bool receiveFrame() {

    static byte state = 0;
    static int frameIndex = 0;

    while (Serial.available() > 0) {

        byte incoming = Serial.read();

        if (state == 0) {

            if (incoming == FRAME_HEADER_1)
                state = 1;

        }

        else if (state == 1) {

            if (incoming == FRAME_HEADER_2) {

                state = 2;
                frameIndex = 0;

            }

            else if (incoming != FRAME_HEADER_1) {

                state = 0;

            }

        }

        else if (state == 2) {

            frame[frameIndex++] = incoming;

            if (frameIndex >= FRAME_SIZE) {

                state = 0;
                frameIndex = 0;

                return true;
            }
        }
    }

    return false;
}


// ================================================
// DISPLAY FRAME
// ================================================

void displayFrame() {

    matrix.clearScreen();

    for (int y = 0; y < DISPLAY_HEIGHT; y++) {

        for (int x = 0; x < DISPLAY_WIDTH; x++) {

            int byteIndex =
                y * BYTES_PER_ROW + x / 8;

            byte pixelByte = frame[byteIndex];

            bool pixel =
                pixelByte & (0x80 >> (x % 8));

            if (pixel)
                matrix.drawPixel(x, y, 1);
        }
    }

    matrix.writeScreen();
}


// ================================================
// MAIN LOOP
// ================================================

void loop() {

    if (receiveFrame())
        displayFrame();
}
