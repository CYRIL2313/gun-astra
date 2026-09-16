import serial
import time
from pynput.mouse import Controller

# =====================================================
# SETTINGS
# =====================================================

PORT = "COM21"
BAUD = 115200

# Gyro sensitivity
# We will tune these later.
MOUSE_SENSITIVITY_X = 8.0
MOUSE_SENSITIVITY_Y = 8.0

# Ignore tiny gyro noise
GYRO_DEADZONE = 0.12

# =====================================================
# MOUSE
# =====================================================

mouse = Controller()

# =====================================================
# GYRO PROCESSING
# =====================================================

def process_gyro(value):
    """
    Remove tiny movements caused by sensor noise.
    """

    if abs(value) < GYRO_DEADZONE:
        return 0.0

    return value


# =====================================================
# SERIAL PACKET
# =====================================================

def parse_packet(line):
    """
    Expected:

    DATA,GX,GY,GZ,JOY_X,JOY_Y,SCOPE,FIRE,RELOAD,RECENTER
    """

    parts = line.strip().split(",")

    if len(parts) != 10:
        return None

    if parts[0] != "DATA":
        return None

    try:
        gx = float(parts[1])
        gy = float(parts[2])
        gz = float(parts[3])

        joy_x = int(parts[4])
        joy_y = int(parts[5])

        scope = int(parts[6])
        fire = int(parts[7])
        reload_button = int(parts[8])
        recenter = int(parts[9])

        return (
            gx,
            gy,
            gz,
            joy_x,
            joy_y,
            scope,
            fire,
            reload_button,
            recenter,
        )

    except ValueError:
        return None


# =====================================================
# CONNECT
# =====================================================

print("========================================")
print("        GUN ASTRA GYRO TEST")
print("========================================")
print(f"Connecting to {PORT}...")

try:
    ser = serial.Serial(PORT, BAUD, timeout=1)

except Exception as e:
    print()
    print("ERROR: Could not connect to ESP32.")
    print(e)
    print()
    input("Press Enter to exit...")
    raise SystemExit

print("Connected!")
print()
print("GYRO CONTROL ACTIVE")
print()
print("Move the gun gently.")
print("The Windows mouse cursor should move.")
print()
print("Press Ctrl+C to stop.")
print("----------------------------------------")


# =====================================================
# MAIN LOOP
# =====================================================

try:

    while True:

        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if not line:
            continue

        data = parse_packet(line)

        if data is None:
            continue

        (
            gx,
            gy,
            gz,
            joy_x,
            joy_y,
            scope,
            fire,
            reload_button,
            recenter,
        ) = data

        # ---------------------------------------------
        # Process gyro
        # ---------------------------------------------

        gx = process_gyro(gx)
        gy = process_gyro(gy)

        # ---------------------------------------------
        # Convert gyro to mouse movement
        # ---------------------------------------------

        mouse_x = int(gx * MOUSE_SENSITIVITY_X)
        mouse_y = int(gy * MOUSE_SENSITIVITY_Y)

        # ---------------------------------------------
        # Move Windows cursor
        # ---------------------------------------------

        if mouse_x != 0 or mouse_y != 0:
            mouse.move(mouse_x, mouse_y)


except KeyboardInterrupt:

    print()
    print("Stopping gun controller...")

finally:

    ser.close()

    print("ESP32 disconnected.")
    print("Done.")