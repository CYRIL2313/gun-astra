import serial
import time
from pynput import mouse

# =========================
# SETTINGS
# =========================

PORT = "COM21"
BAUD = 115200

MOUSE_SENSITIVITY_X = 20.0
MOUSE_SENSITIVITY_Y = 20.0

GYRO_DEADZONE = 0.12
SMOOTHING = 0.35

# =========================
# SERIAL
# =========================

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

print("Gyro mouse test started")
print("GX -> Horizontal")
print("GZ -> Vertical")
print("Move the gun!")

# =========================
# MOUSE
# =========================

mouse_controller = mouse.Controller()

filtered_x = 0.0
filtered_y = 0.0


def apply_deadzone(value):
    if abs(value) < GYRO_DEADZONE:
        return 0.0
    return value


# =========================
# MAIN LOOP
# =========================

while True:

    try:
        line = ser.readline().decode(errors="ignore").strip()

        if not line.startswith("DATA,"):
            continue

        parts = line.split(",")

        if len(parts) < 10:
            continue

        # DATA,GX,GY,GZ,JOY_X,JOY_Y,SCOPE,FIRE,RELOAD,RECENTER
        gx = float(parts[1])
        gz = float(parts[3])

        # Deadzone
        gx = apply_deadzone(gx)
        gz = apply_deadzone(gz)

        # Smoothing
        filtered_x = (
            filtered_x * (1 - SMOOTHING)
            + gx * SMOOTHING
        )

        filtered_y = (
            filtered_y * (1 - SMOOTHING)
            + gz * SMOOTHING
        )

        # Horizontal:
        # Right movement previously moved cursor LEFT,
        # so invert GX.
        mouse_x = int(-filtered_x * MOUSE_SENSITIVITY_X)

        # Vertical:
        # Now using GZ instead of GY.
        mouse_y = int(filtered_y * MOUSE_SENSITIVITY_Y)

        if mouse_x != 0 or mouse_y != 0:
            mouse_controller.move(mouse_x, mouse_y)

    except KeyboardInterrupt:
        print("\nStopped.")
        break

    except Exception as e:
        print("Error:", e)