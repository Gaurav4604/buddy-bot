import Jetson.GPIO as GPIO
import time
import tkinter as tk

# Pin Definitions
# Left Side Motors
ENA_LEFT = 32  # PWM for Left Side Motors
IN1_LEFT = 12  # Left Motor 1 Forward
IN2_LEFT = 11  # Left Motor 1 Backward
IN3_LEFT = 22  # Left Motor 2 Forward
IN4_LEFT = 21  # Left Motor 2 Backward

# Right Side Motors
ENA_RIGHT = 33  # PWM for Right Side Motors
IN1_RIGHT = 15  # Right Motor 1 Forward
IN2_RIGHT = 16  # Right Motor 1 Backward
IN3_RIGHT = 24  # Right Motor 2 Forward
IN4_RIGHT = 23  # Right Motor 2 Backward

# GPIO setup
GPIO.setmode(GPIO.BOARD)
pins = [
    ENA_LEFT,
    ENA_RIGHT,
    IN1_LEFT,
    IN2_LEFT,
    IN3_LEFT,
    IN4_LEFT,
    IN1_RIGHT,
    IN2_RIGHT,
    IN3_RIGHT,
    IN4_RIGHT,
]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)

# Initialize hardware PWM on ENA pins at 1kHz frequency
pwm_left = GPIO.PWM(ENA_LEFT, 1000)
pwm_left.start(0)
pwm_right = GPIO.PWM(ENA_RIGHT, 1000)
pwm_right.start(0)


# Movement Functions
def move_forward(speed):
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def move_backward(speed):
    GPIO.output(IN1_LEFT, GPIO.LOW)
    GPIO.output(IN2_LEFT, GPIO.HIGH)
    GPIO.output(IN3_LEFT, GPIO.LOW)
    GPIO.output(IN4_LEFT, GPIO.HIGH)
    GPIO.output(IN1_RIGHT, GPIO.LOW)
    GPIO.output(IN2_RIGHT, GPIO.HIGH)
    GPIO.output(IN3_RIGHT, GPIO.LOW)
    GPIO.output(IN4_RIGHT, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def turn_left(speed):
    GPIO.output(IN1_LEFT, GPIO.LOW)
    GPIO.output(IN2_LEFT, GPIO.HIGH)
    GPIO.output(IN3_LEFT, GPIO.LOW)
    GPIO.output(IN4_LEFT, GPIO.HIGH)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def turn_right(speed):
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.LOW)
    GPIO.output(IN2_RIGHT, GPIO.HIGH)
    GPIO.output(IN3_RIGHT, GPIO.LOW)
    GPIO.output(IN4_RIGHT, GPIO.HIGH)
    pwm_left.ChangeDutyCycle(speed)
    pwm_right.ChangeDutyCycle(speed)


def move_forward_left():
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(100)
    pwm_right.ChangeDutyCycle(80)


def move_forward_right():
    GPIO.output(IN1_LEFT, GPIO.HIGH)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.HIGH)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.HIGH)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.HIGH)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(80)
    pwm_right.ChangeDutyCycle(100)


def stop_motors():
    GPIO.output(IN1_LEFT, GPIO.LOW)
    GPIO.output(IN2_LEFT, GPIO.LOW)
    GPIO.output(IN3_LEFT, GPIO.LOW)
    GPIO.output(IN4_LEFT, GPIO.LOW)
    GPIO.output(IN1_RIGHT, GPIO.LOW)
    GPIO.output(IN2_RIGHT, GPIO.LOW)
    GPIO.output(IN3_RIGHT, GPIO.LOW)
    GPIO.output(IN4_RIGHT, GPIO.LOW)
    pwm_left.ChangeDutyCycle(0)
    pwm_right.ChangeDutyCycle(0)


# Setup Tkinter (headless)
root = tk.Tk()
root.withdraw()  # Hide the window since no display is needed

# Dictionary to track pressed keys
keys_pressed = {}


def on_key_press(event):
    keys_pressed[event.keysym.lower()] = True


def on_key_release(event):
    keys_pressed[event.keysym.lower()] = False


# Bind key events
root.bind("<KeyPress>", on_key_press)
root.bind("<KeyRelease>", on_key_release)


def update_motors():
    if keys_pressed.get("space"):
        stop_motors()
        print("Stopping motors")
    elif keys_pressed.get("w") and keys_pressed.get("a"):
        move_forward_left()
        print("Moving forward with left bias")
    elif keys_pressed.get("w") and keys_pressed.get("d"):
        move_forward_right()
        print("Moving forward with right bias")
    elif keys_pressed.get("w"):
        move_forward(100)
        print("Moving forward")
    elif keys_pressed.get("s"):
        move_backward(100)
        print("Moving backward")
    elif keys_pressed.get("a"):
        turn_left(100)
        print("Turning left")
    elif keys_pressed.get("d"):
        turn_right(100)
        print("Turning right")
    else:
        stop_motors()
    root.after(100, update_motors)


def on_esc(event):
    print("Exiting program")
    root.quit()


# Bind ESC to exit
root.bind("<Escape>", on_esc)

print("Control the robot using:")
print("   w: forward")
print("   s: backward")
print("   a: turn left")
print("   d: turn right")
print("   wa: forward with left bias")
print("   wd: forward with right bias")
print("   space: stop motors")
print("Press ESC to exit.")

# Start motor update loop
update_motors()

try:
    root.mainloop()
except KeyboardInterrupt:
    print("Exiting program (KeyboardInterrupt)")
finally:
    pwm_left.stop()
    pwm_right.stop()
    GPIO.cleanup()
