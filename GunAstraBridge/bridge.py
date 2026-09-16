import serial
import time
import ctypes
from pynput import mouse, keyboard

# =========================================================
# SETTINGS
# =========================================================

PORT = "COM21"
BAUD = 115200

# Gyro -> mouse sensitivity
MOUSE_SENSITIVITY_X = 30.0
MOUSE_SENSITIVITY_Y = 30.0

GYRO_DEADZONE = 0.12
SMOOTHING = 0.35

# Joystick
JOY_CENTER_X = 1926
JOY_CENTER_Y = 1960

JOY_DEADZONE = 180

# =========================================================
# WINDOWS FOREGROUND WINDOW
# =========================================================

user32 = ctypes.windll.user32

def get_active_window_title():
    hwnd = user32.GetForegroundWindow()

    if hwnd == 0:
        return ""

    length = user32.GetWindowTextLengthW(hwnd)

    if length == 0:
        return ""

    buffer = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buffer, length + 1)

    return buffer.value


def game_is_active():
    title = get_active_window_title().lower()

    return "operation ironhold" in title


# =========================================================
# SERIAL
# =========================================================

print("Connecting to ESP32...")

ser = serial.Serial(
    PORT,
    BAUD,
    timeout=1
)

time.sleep(2)

print("Connected!")
print("Operation Ironhold controller bridge")
print("-------------------------------------")
print("Game title detection: ENABLED")
print()


# =========================================================
# INPUT CONTROLLERS
# =========================================================

mouse_controller = mouse.Controller()
keyboard_controller = keyboard.Controller()


# =========================================================
# STATE
# =========================================================

filtered_x = 0.0
filtered_y = 0.0

fire_pressed = False
scope_pressed = False

w_pressed = False
a_pressed = False
s_pressed = False
d_pressed = False

last_reload = 0
last_recenter = 0


# =========================================================
# HELPERS
# =========================================================

def apply_deadzone(value):
    if abs(value) < GYRO_DEADZONE:
        return 0.0

    return value


def release_all_movement():
    global w_pressed, a_pressed, s_pressed, d_pressed

    if w_pressed:
        keyboard_controller.release('w')
        w_pressed = False

    if a_pressed:
        keyboard_controller.release('a')
        a_pressed = False

    if s_pressed:
        keyboard_controller.release('s')
        s_pressed = False

    if d_pressed:
        keyboard_controller.release('d')
        d_pressed = False


def update_movement(joy_x, joy_y):

    global w_pressed
    global a_pressed
    global s_pressed
    global d_pressed

    # Convert raw joystick values to centered values
    x = joy_x - JOY_CENTER_X
    y = joy_y - JOY_CENTER_Y

    # -----------------------------------------------------
    # X AXIS
    # -----------------------------------------------------

    if x < -JOY_DEADZONE:

        if not a_pressed:
            keyboard_controller.press('a')
            a_pressed = True

        if d_pressed:
            keyboard_controller.release('d')
            d_pressed = False

    elif x > JOY_DEADZONE:

        if not d_pressed:
            keyboard_controller.press('d')
            d_pressed = True

        if a_pressed:
            keyboard_controller.release('a')
            a_pressed = False

    else:

        if a_pressed:
            keyboard_controller.release('a')
            a_pressed = False

        if d_pressed:
            keyboard_controller.release('d')
            d_pressed = False


    # -----------------------------------------------------
    # Y AXIS
    # -----------------------------------------------------

    if y < -JOY_DEADZONE:

        if not w_pressed:
            keyboard_controller.press('w')
            w_pressed = True

        if s_pressed:
            keyboard_controller.release('s')
            s_pressed = False

    elif y > JOY_DEADZONE:

        if not s_pressed:
            keyboard_controller.press('s')
            s_pressed = True

        if w_pressed:
            keyboard_controller.release('w')
            w_pressed = False

    else:

        if w_pressed:
            keyboard_controller.release('w')
            w_pressed = False

        if s_pressed:
            keyboard_controller.release('s')
            s_pressed = False


# =========================================================
# MAIN LOOP
# =========================================================

try:

    print("Bridge running.")
    print("Open Operation Ironhold and click the game once.")
    print()

    while True:

        line = ser.readline().decode(
            errors="ignore"
        ).strip()

        if not line.startswith("DATA,"):
            continue

        parts = line.split(",")

        if len(parts) < 10:
            continue

        # -------------------------------------------------
        # DATA FORMAT
        #
        # DATA,
        # GX,
        # GY,
        # GZ,
        # JOY_X,
        # JOY_Y,
        # SCOPE,
        # FIRE,
        # RELOAD,
        # RECENTER
        # -------------------------------------------------

        gx = float(parts[1])
        gz = float(parts[3])

        joy_x = int(parts[4])
        joy_y = int(parts[5])

        scope = int(parts[6])
        fire = int(parts[7])
        reload_button = int(parts[8])
        recenter = int(parts[9])


        # =================================================
        # ONLY CONTROL COMPUTER WHEN GAME IS ACTIVE
        # =================================================

        if not game_is_active():

            # Release anything we might still be holding
            if fire_pressed:
                mouse_controller.release(mouse.Button.left)
                fire_pressed = False

            release_all_movement()

            filtered_x = 0.0
            filtered_y = 0.0

            continue


        # =================================================
        # GYRO AIM
        # =================================================

        gx = apply_deadzone(gx)
        gz = apply_deadzone(gz)

        filtered_x = (
            filtered_x * (1 - SMOOTHING)
            + gx * SMOOTHING
        )

        filtered_y = (
            filtered_y * (1 - SMOOTHING)
            + gz * SMOOTHING
        )


        # Horizontal
        # We already confirmed X needs inversion.
        mouse_x = int(
            -filtered_x * MOUSE_SENSITIVITY_X
        )

        # Vertical
        mouse_y = int(
            filtered_y * MOUSE_SENSITIVITY_Y
        )

        if mouse_x != 0 or mouse_y != 0:
            mouse_controller.move(
                mouse_x,
                mouse_y
            )


        # =================================================
        # JOYSTICK -> WASD
        # =================================================

        update_movement(
            joy_x,
            joy_y
        )


        # =================================================
        # FIRE -> LEFT MOUSE
        # =================================================

        if fire and not fire_pressed:

            mouse_controller.press(
                mouse.Button.left
            )

            fire_pressed = True

        elif not fire and fire_pressed:

            mouse_controller.release(
                mouse.Button.left
            )

            fire_pressed = False


        # =================================================
        # SCOPE -> RIGHT CLICK
        #
        # Game uses right-click as an ADS toggle.
        # Therefore only send a click when the physical
        # joystick button is newly pressed.
        # =================================================

        if scope and not scope_pressed:

            mouse_controller.click(
                mouse.Button.right
            )

            scope_pressed = True

        elif not scope:

            scope_pressed = False


        # =================================================
        # RELOAD -> R
        #
        # Only send R once per button press.
        # =================================================

        if reload_button and not last_reload:

            keyboard_controller.press('r')
            keyboard_controller.release('r')


        # =================================================
        # RECENTER
        # =================================================
        #
        # Current gyro system is rate-based, so there is
        # no accumulated orientation reference to reset.
        #
        # We keep this event ready for the later improved
        # game-side centering system.
        # =================================================

        if recenter and not last_recenter:

            filtered_x = 0.0
            filtered_y = 0.0

            print(">>> RECENTER")


        last_reload = reload_button
        last_recenter = recenter


except KeyboardInterrupt:

    print("\nStopping...")

finally:

    # Safety cleanup
    try:
        mouse_controller.release(mouse.Button.left)
    except:
        pass

    release_all_movement()

    ser.close()

    print("Bridge closed.")