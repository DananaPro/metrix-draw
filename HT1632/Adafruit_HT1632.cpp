
#include "Adafruit_HT1632.h"

#include <stdlib.h>
#include <string.h>
#include <new>


// ==================================================
// CONSTRUCTORS
// ==================================================

Adafruit_HT1632LEDMatrix::Adafruit_HT1632LEDMatrix(
    uint8_t data,
    uint8_t wr,
    uint8_t cs1
)
    : Adafruit_GFX(32, 8),
      matrices(NULL),
      matrixNum(0) {

    matrices = (Adafruit_HT1632 *)malloc(
        sizeof(Adafruit_HT1632)
    );

    if (matrices) {

        new (&matrices[0]) Adafruit_HT1632(
            data, wr, cs1
        );

        matrixNum = 1;
    }
}


Adafruit_HT1632LEDMatrix::Adafruit_HT1632LEDMatrix(
    uint8_t data,
    uint8_t wr,
    uint8_t cs1,
    uint8_t cs2,
    uint8_t cs3
)
    : Adafruit_GFX(32, 24),
      matrices(NULL),
      matrixNum(0) {

    matrices = (Adafruit_HT1632 *)malloc(
        3 * sizeof(Adafruit_HT1632)
    );

    if (matrices) {

        new (&matrices[0]) Adafruit_HT1632(
            data, wr, cs1
        );

        new (&matrices[1]) Adafruit_HT1632(
            data, wr, cs2
        );

        new (&matrices[2]) Adafruit_HT1632(
            data, wr, cs3
        );

        matrixNum = 3;
    }
}


// ==================================================
// PIXEL MAPPING
// ==================================================

void Adafruit_HT1632LEDMatrix::setPixel(
    uint8_t x,
    uint8_t y
) {
    drawPixel(x, y, 1);
}


void Adafruit_HT1632LEDMatrix::clrPixel(
    uint8_t x,
    uint8_t y
) {
    drawPixel(x, y, 0);
}


void Adafruit_HT1632LEDMatrix::drawPixel(
    int16_t x,
    int16_t y,
    uint16_t color
) {

    if (x < 0 || x >= 32 || y < 0 || y >= 24)
        return;

    if (!matrices || matrixNum != 3)
        return;

    uint8_t panel = y / 8;
    uint8_t localY = y % 8;

    // Original horizontal mirror correction
    uint8_t localX = 31 - x;

    uint16_t index = (localX * 8) + localY;

    if (color)
        matrices[panel].setPixel(index);
    else
        matrices[panel].clrPixel(index);
}


// ==================================================
// INITIALIZATION
// ==================================================

boolean Adafruit_HT1632LEDMatrix::begin(uint8_t type) {

    if (!matrices)
        return false;

    for (uint8_t i = 0; i < matrixNum; i++)
        matrices[i].begin(type);

    return true;
}


// ==================================================
// DISPLAY CONTROL
// ==================================================

void Adafruit_HT1632LEDMatrix::clearScreen() {

    for (uint8_t i = 0; i < matrixNum; i++)
        matrices[i].clearBuffer();
}


void Adafruit_HT1632LEDMatrix::fillScreen() {

    for (uint8_t i = 0; i < matrixNum; i++)
        matrices[i].fillScreen();
}


void Adafruit_HT1632LEDMatrix::setBrightness(
    uint8_t brightness
) {

    for (uint8_t i = 0; i < matrixNum; i++)
        matrices[i].setBrightness(brightness);
}


void Adafruit_HT1632LEDMatrix::blink(boolean b) {

    for (uint8_t i = 0; i < matrixNum; i++)
        matrices[i].blink(b);
}


void Adafruit_HT1632LEDMatrix::writeScreen() {

    for (uint8_t i = 0; i < matrixNum; i++)
        matrices[i].writeScreen();
}


// ==================================================
// LOW LEVEL CONSTRUCTOR
// ==================================================

Adafruit_HT1632::Adafruit_HT1632(
    int8_t data,
    int8_t wr,
    int8_t cs,
    int8_t rd
) {

    _data = data;
    _wr = wr;
    _cs = cs;
    _rd = rd;

    memset(ledmatrix, 0, sizeof(ledmatrix));
}


// ==================================================
// INITIALIZATION
// ==================================================

void Adafruit_HT1632::begin(uint8_t type) {

    pinMode(_cs, OUTPUT);
    digitalWrite(_cs, HIGH);

    pinMode(_wr, OUTPUT);
    digitalWrite(_wr, HIGH);

    pinMode(_data, OUTPUT);

    if (_rd >= 0) {
        pinMode(_rd, OUTPUT);
        digitalWrite(_rd, HIGH);
    }

#ifdef __AVR__

    csport = portOutputRegister(digitalPinToPort(_cs));
    csmask = digitalPinToBitMask(_cs);

    wrport = portOutputRegister(digitalPinToPort(_wr));
    wrmask = digitalPinToBitMask(_wr);

    dataport = portOutputRegister(digitalPinToPort(_data));
    datadir = portModeRegister(digitalPinToPort(_data));
    datamask = digitalPinToBitMask(_data);

#endif

    sendcommand(ADA_HT1632_SYS_EN);
    sendcommand(ADA_HT1632_LED_ON);
    sendcommand(ADA_HT1632_BLINK_OFF);
    sendcommand(ADA_HT1632_MASTER_MODE);
    sendcommand(ADA_HT1632_INT_RC);
    sendcommand(type);

    sendcommand(ADA_HT1632_PWM_CONTROL | 0xF);
}


// ==================================================
// BRIGHTNESS AND BLINK
// ==================================================

void Adafruit_HT1632::setBrightness(uint8_t pwm) {

    if (pwm > 15)
        pwm = 15;

    sendcommand(ADA_HT1632_PWM_CONTROL | pwm);
}


void Adafruit_HT1632::blink(boolean state) {

    sendcommand(
        state
        ? ADA_HT1632_BLINK_ON
        : ADA_HT1632_BLINK_OFF
    );
}


// ==================================================
// PIXEL MEMORY
// ==================================================

void Adafruit_HT1632::setPixel(uint16_t i) {

    if (i >= 256)
        return;

    ledmatrix[i / 8] |= (1 << (i & 7));
}


void Adafruit_HT1632::clrPixel(uint16_t i) {

    if (i >= 256)
        return;

    ledmatrix[i / 8] &= ~(1 << (i & 7));
}


void Adafruit_HT1632::clearBuffer() {

    memset(ledmatrix, 0, sizeof(ledmatrix));
}


void Adafruit_HT1632::fillScreen() {

    memset(ledmatrix, 0xFF, sizeof(ledmatrix));

    writeScreen();
}


// ==================================================
// DEBUG
// ==================================================

void Adafruit_HT1632::dumpScreen() {

    Serial.println(F("---------------------------------------"));

    for (uint16_t i = 0; i < sizeof(ledmatrix); i++) {

        Serial.print("0x");
        Serial.print(ledmatrix[i], HEX);
        Serial.print(" ");

        if (i % 3 == 2)
            Serial.println();
    }

    Serial.println(F("\n---------------------------------------"));
}


// ==================================================
// WRITE DISPLAY RAM
// ==================================================

void Adafruit_HT1632::writeScreen() {

#ifdef __AVR__

    *csport &= ~csmask;
    *datadir |= datamask;

#else

    digitalWrite(_cs, LOW);

#endif

    writedata(ADA_HT1632_WRITE, 3);
    writedata(0, 7);

    for (uint16_t i = 0; i < sizeof(ledmatrix); i += 2) {

        writedata(
            ((uint16_t)ledmatrix[i] << 8)
            | ledmatrix[i + 1],
            16
        );
    }

#ifdef __AVR__

    *csport |= csmask;
    *datadir &= ~datamask;

#else

    digitalWrite(_cs, HIGH);

#endif
}


void Adafruit_HT1632::clearScreen() {

    clearBuffer();
    writeScreen();
}


// ==================================================
// SERIAL BIT-BANGING
// ==================================================

void Adafruit_HT1632::writedata(
    uint16_t d,
    uint8_t bits
) {

#ifdef __AVR__

    for (
        uint16_t bit = 1 << (bits - 1);
        bit;
        bit >>= 1
    ) {

        *wrport &= ~wrmask;

        if (d & bit)
            *dataport |= datamask;
        else
            *dataport &= ~datamask;

        *wrport |= wrmask;
    }

#else

    pinMode(_data, OUTPUT);

    for (
        uint16_t bit = 1 << (bits - 1);
        bit;
        bit >>= 1
    ) {

        digitalWrite(_wr, LOW);

        digitalWrite(
            _data,
            (d & bit) ? HIGH : LOW
        );

        digitalWrite(_wr, HIGH);
    }

    pinMode(_data, INPUT);

#endif
}


// ==================================================
// WRITE RAM
// ==================================================

void Adafruit_HT1632::writeRAM(
    uint8_t addr,
    uint8_t data
) {

    uint16_t d = ADA_HT1632_WRITE;

    d <<= 7;
    d |= addr & 0x7F;

    d <<= 4;
    d |= data & 0xF;

#ifdef __AVR__

    *csport &= ~csmask;

    writedata(d, 14);

    *csport |= csmask;

#else

    digitalWrite(_cs, LOW);
    writedata(d, 14);
    digitalWrite(_cs, HIGH);

#endif
}


// ==================================================
// COMMANDS
// ==================================================

void Adafruit_HT1632::sendcommand(uint8_t cmd) {

#ifdef __AVR__

    *csport &= ~csmask;
    *datadir |= datamask;

    writedata(
        (((uint16_t)ADA_HT1632_COMMAND << 8) | cmd) << 1,
        12
    );

    *datadir &= ~datamask;
    *csport |= csmask;

#else

    digitalWrite(_cs, LOW);

    writedata(
        (((uint16_t)ADA_HT1632_COMMAND << 8) | cmd) << 1,
        12
    );

    digitalWrite(_cs, HIGH);

#endif
}
