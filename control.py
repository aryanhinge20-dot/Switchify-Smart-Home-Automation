import RPi.GPIO as GPIO
import time

# ---------------- GPIO SETUP ----------------
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# ---------------- PIN CONFIG ----------------
PINS = {
    "light1": 17,
    "light2": 27,
    "fan": 22
}

# Setup all pins as OUTPUT
for pin in PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.HIGH)  # OFF (for relay modules)

# ---------------- DEVICE CONTROL ----------------

# Light 1
def light1_on():
    GPIO.output(PINS["light1"], GPIO.LOW)

def light1_off():
    GPIO.output(PINS["light1"], GPIO.HIGH)

# Light 2 (3-in-1 light)
def light2_on():
    GPIO.output(PINS["light2"], GPIO.LOW)

def light2_off():
    GPIO.output(PINS["light2"], GPIO.HIGH)

# Fan
def fan_on():
    GPIO.output(PINS["fan"], GPIO.LOW)

def fan_off():
    GPIO.output(PINS["fan"], GPIO.HIGH)

# ---------------- ALL OFF ----------------
def all_off():
    for pin in PINS.values():
        GPIO.output(pin, GPIO.HIGH)

# ---------------- CLEANUP ----------------
def cleanup():
    GPIO.cleanup()
