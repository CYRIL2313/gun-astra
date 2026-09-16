#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// ---------------- PIN DEFINITIONS ----------------
#define I2C_SDA 8
#define I2C_SCL 9

#define JOY_X 1
#define JOY_Y 2
#define JOY_SW 10

#define BTN_FIRE 15
#define BTN_RELOAD 16

// --------------------------------------------------

Adafruit_MPU6050 mpu;

// Simple button helper
bool readButton(int pin)
{
    return digitalRead(pin) == LOW;
}

void setup()
{
    Serial.begin(9600);

    // I2C
    Wire.begin(I2C_SDA, I2C_SCL);

    // MPU6050
    if (!mpu.begin())
    {
        Serial.println("MPU6050 NOT FOUND!");
        while (true)
        {
            delay(1000);
        }
    }

    Serial.println("MPU6050 OK");

    // Sensor ranges
    mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
    mpu.setGyroRange(MPU6050_RANGE_500_DEG);
    mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);

    // Joystick
    pinMode(JOY_SW, INPUT_PULLUP);

    // Buttons
    pinMode(BTN_FIRE, INPUT_PULLUP);
    pinMode(BTN_RELOAD, INPUT_PULLUP);

    Serial.println("Controller ready!");
}

void loop()
{
    sensors_event_t accel;
    sensors_event_t gyro;
    sensors_event_t temp;

    mpu.getEvent(&accel, &gyro, &temp);

    int joyX = analogRead(JOY_X);
    int joyY = analogRead(JOY_Y);

    bool scope = readButton(JOY_SW);
    bool fire = readButton(BTN_FIRE);
    bool reload = readButton(BTN_RELOAD);

    Serial.print("Accel [");
    Serial.print("X: ");
    Serial.print(accel.acceleration.x, 2);

    Serial.print(" Y: ");
    Serial.print(accel.acceleration.y, 2);

    Serial.print(" Z: ");
    Serial.print(accel.acceleration.z, 2);

    Serial.print("] ");

    Serial.print("Gyro [");
    Serial.print("X: ");
    Serial.print(gyro.gyro.x, 3);

    Serial.print(" Y: ");
    Serial.print(gyro.gyro.y, 3);

    Serial.print(" Z: ");
    Serial.print(gyro.gyro.z, 3);

    Serial.print("] ");

    Serial.print("Joy [");
    Serial.print("X: ");
    Serial.print(joyX);

    Serial.print(" Y: ");
    Serial.print(joyY);

    Serial.print("] ");

    Serial.print("Btns [");

    Serial.print("Scope: ");
    Serial.print(scope ? "ON" : "OFF");

    Serial.print(" | Fire: ");
    Serial.print(fire ? "ON" : "OFF");

    Serial.print(" | Reload: ");
    Serial.print(reload ? "ON" : "OFF");

    Serial.println("]");

    delay(20);
}