#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// =====================================================
// PIN DEFINITIONS
// =====================================================

#define I2C_SDA 8
#define I2C_SCL 9

#define JOY_X 1
#define JOY_Y 2
#define JOY_SW 10

#define BTN_FIRE 15
#define BTN_RELOAD 16
#define BTN_RECENTER 17

// =====================================================
// JOYSTICK SETTINGS
// =====================================================

// Based on your observed center values
const int JOY_CENTER_X = 1926;
const int JOY_CENTER_Y = 1960;

// Small movements around center are ignored
const int JOY_DEADZONE = 180;

// =====================================================
// SERIAL SETTINGS
// =====================================================

// Send controller data every 10 ms = 100 Hz
const unsigned long SEND_INTERVAL = 10;

// =====================================================
// MPU6050
// =====================================================

Adafruit_MPU6050 mpu;

// =====================================================
// BUTTON STATE
// =====================================================

// Used to detect a NEW recenter press.
// This prevents one physical press from creating
// hundreds of recenter commands.
bool previousRecenterState = false;

unsigned long lastSendTime = 0;

// =====================================================
// JOYSTICK DEADZONE
// =====================================================

int applyDeadzone(int value, int center)
{
    int delta = value - center;

    if (abs(delta) < JOY_DEADZONE)
    {
        return 0;
    }

    return delta;
}

// =====================================================
// BUTTON READING
// =====================================================

bool readButton(int pin)
{
    // Buttons are wired to GND and use INPUT_PULLUP
    // Therefore:
    // LOW  = pressed
    // HIGH = released

    return digitalRead(pin) == LOW;
}

// =====================================================
// SETUP
// =====================================================

void setup()
{
    Serial.begin(115200);

    delay(500);

    // -------------------------------------------------
    // I2C
    // -------------------------------------------------

    Wire.begin(I2C_SDA, I2C_SCL);

    // -------------------------------------------------
    // MPU6050
    // -------------------------------------------------

    if (!mpu.begin())
    {
        Serial.println("ERROR,MPU6050_NOT_FOUND");

        while (true)
        {
            delay(1000);
        }
    }

    // Accelerometer range
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);

    // Gyroscope range
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);

    // Sensor filtering
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

    // -------------------------------------------------
    // BUTTONS
    // -------------------------------------------------

    pinMode(JOY_SW, INPUT_PULLUP);
    pinMode(BTN_FIRE, INPUT_PULLUP);
    pinMode(BTN_RELOAD, INPUT_PULLUP);
    pinMode(BTN_RECENTER, INPUT_PULLUP);

    Serial.println("READY");
}

// =====================================================
// MAIN LOOP
// =====================================================

void loop()
{
    unsigned long now = millis();

    // =================================================
    // READ MPU6050
    // =================================================

    sensors_event_t accel;
    sensors_event_t gyro;
    sensors_event_t temp;

    mpu.getEvent(&accel, &gyro, &temp);

    // =================================================
    // READ JOYSTICK
    // =================================================

    int joyX = analogRead(JOY_X);
    int joyY = analogRead(JOY_Y);

    int joyDeltaX = applyDeadzone(joyX, JOY_CENTER_X);
    int joyDeltaY = applyDeadzone(joyY, JOY_CENTER_Y);

    // =================================================
    // READ BUTTONS
    // =================================================

    bool scopePressed = readButton(JOY_SW);
    bool firePressed = readButton(BTN_FIRE);
    bool reloadPressed = readButton(BTN_RELOAD);
    bool recenterPressed = readButton(BTN_RECENTER);

    // =================================================
    // RECENTER PRESS DETECTION
    // =================================================

    bool recenterEvent = false;

    /*
     * We only generate a recenter event when GPIO 17
     * changes from RELEASED -> PRESSED.
     *
     * Therefore:
     *
     * Released:
     *     0
     *
     * Press:
     *     0 -> 1
     *     RECENTER EVENT = 1
     *
     * Holding:
     *     1 -> 1 -> 1 -> 1
     *     RECENTER EVENT = 0
     *
     * Release:
     *     1 -> 0
     *     RECENTER EVENT = 0
     *
     * So one physical press = one recenter command.
     */

    if (recenterPressed && !previousRecenterState)
    {
        recenterEvent = true;
    }

    previousRecenterState = recenterPressed;

    // =================================================
    // SEND CONTROLLER DATA
    // =================================================

    if (now - lastSendTime >= SEND_INTERVAL)
    {
        lastSendTime = now;

        /*
         * PACKET FORMAT
         *
         * DATA,GX,GY,GZ,JOY_X,JOY_Y,SCOPE,FIRE,RELOAD,RECENTER
         *
         * Example:
         *
         * DATA,-0.1234,1.2345,0.0123,120,-450,1,0,0,0
         *
         * Meaning:
         *
         * GX        = -0.1234
         * GY        =  1.2345
         * GZ        =  0.0123
         *
         * Joystick X = 120
         * Joystick Y = -450
         *
         * Scope  = 1
         * Fire   = 0
         * Reload = 0
         *
         * Recenter event = 0
         */

        Serial.print("DATA,");

        // -------------------------------------------------
        // GYROSCOPE
        // -------------------------------------------------

        Serial.print(gyro.gyro.x, 4);
        Serial.print(",");

        Serial.print(gyro.gyro.y, 4);
        Serial.print(",");

        Serial.print(gyro.gyro.z, 4);
        Serial.print(",");

        // -------------------------------------------------
        // JOYSTICK
        // -------------------------------------------------

        Serial.print(joyDeltaX);
        Serial.print(",");

        Serial.print(joyDeltaY);
        Serial.print(",");

        // -------------------------------------------------
        // BUTTON STATES
        // -------------------------------------------------

        Serial.print(scopePressed ? 1 : 0);
        Serial.print(",");

        Serial.print(firePressed ? 1 : 0);
        Serial.print(",");

        Serial.print(reloadPressed ? 1 : 0);
        Serial.print(",");

        // -------------------------------------------------
        // RECENTER EVENT
        // -------------------------------------------------

        Serial.println(recenterEvent ? 1 : 0);
    }
}